from flask import Flask, jsonify
from project import app
from .models import Parkingspot, HistoricOccupancy, HistoricWeather, ForecastWeather, Prediction, VacationRLP, VacationHE, HolidayRLP, HolidayHE, db
import pandas as pd
import numpy as np
from datetime import datetime
import datetime as datetime2
from dateutil.relativedelta import relativedelta
from pathlib import Path
import glob
import io
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from category_encoders.target_encoder import TargetEncoder
from sklearn.preprocessing import MinMaxScaler
from project.utils import zipfileToDataframe, concatenateHistoricRecentData, historicOccupanciesToDataframe
from project.dwdForecast import getForecastsAsDataframe


@app.route("/")
def hello():
    """ Demo Endpoint.
    """    
    return jsonify(hello="world")


@app.route('/parkingspots')
def show_parkingspots():
    """ Endpoint for frontend application.

        Returns:
            predictions, historic occupations and information for every parkingspot as json
    """
    parking_dict = dict()

    # Query Objects from DB
    parkingspots = Parkingspot.query.all()

    # format to expected Output
    for parkingspot in parkingspots:
        name = parkingspot.name
        max_occupancy = parkingspot.max_occupancy
        lat = parkingspot.lat
        lon = parkingspot.lon
        open = parkingspot.open
        parkingspot_type = parkingspot.parkingspot_type
        height_limit = parkingspot.height_limit
        handicapped_spots = parkingspot.handicapped_spots
        women_spots = parkingspot.women_spots
        parent_child_spots = parkingspot.parent_child_spots
        address = parkingspot.address
        url = parkingspot.url
        predictions = parkingspot.predictions
        prediction_dict = dict()

        for prediction in predictions:
            timestamp = prediction.datetime.strftime("%Y-%m-%dT%H:%M:%S")
            occupation = prediction.occupation
            rmse = prediction.rmse
            predictionData = {
                timestamp: {
                    "occupation": occupation,
                    "rmse": rmse
                }
            }
            prediction_dict.update(predictionData)

        parkingspotData = {
            name:
                {
                    "lat": lat,
                    "lon": lon,
                    "openingHours": open,
                    "spots": max_occupancy,
                    "type": parkingspot_type,
                    "heightLimit": height_limit,
                    "handicappedSpots": handicapped_spots,
                    "womenSpots": women_spots,
                    "parentChildSpots": parent_child_spots,
                    "address": address,
                    "url": url,
                    "predictions": prediction_dict
                }
        }
        parking_dict.update(parkingspotData)
    return jsonify(parking_dict)


@app.route('/predict')
def predict():
    """ Prediction endpoint.

        Returns:
            saves predictions in the database
    """
    num_rows_added = 0
   # remove all records
    try:
        num_rows_deleted = db.session.query(Prediction).delete()
        db.session.commit()
    except:
        db.session.rollback()

    models_dir = Path("data/models/Joblib_ohneWetterUndHistData")
    rmse_dir = Path("data/models/Joblib_mitWetterUndHistData")
    # Query Objects from DB
    parkingspots = Parkingspot.query.all()
    vacationRlp = pd.read_sql(db.session.query(
        VacationRLP).statement, db.session.bind, parse_dates=[0, 1])
    vacationRlp = vacationRlp.drop('id', axis=1)
    vacationHe = pd.read_sql(db.session.query(
        VacationHE).statement, db.session.bind)
    vacationHe = vacationHe.drop('id', axis=1)
    holidayRlp = pd.read_sql(db.session.query(
        HolidayRLP).statement, db.session.bind)
    holidayHe = pd.read_sql(db.session.query(
        HolidayHE).statement, db.session.bind)
    historic_Weather = pd.read_sql(db.session.query(
        HistoricWeather).statement, db.session.bind)
    forecast_Weather = pd.read_sql(db.session.query(
        ForecastWeather).statement, db.session.bind)

    for parkingspot in parkingspots:
        name = parkingspot.name
        try:
        
            targetencoder = joblib.load(Path.joinpath(
                models_dir, ("targetenc" + name + ".sav")))
            scalerload = joblib.load(Path.joinpath(
                models_dir, ("scaler" + name + ".sav")))
            modelload = joblib.load(Path.joinpath(
                models_dir, (name + ".sav")))
            rmseload = joblib.load(Path.joinpath(
                rmse_dir, ("rmseAll" + name + ".sav")))
            leaderload = joblib.load(Path.joinpath(
                rmse_dir, ("leaderAll" + name + ".sav")))

            feature_df = create_feature_df(
                vacationRlp, vacationHe, holidayRlp, holidayHe)

            # target encode
            feature_df = pd.DataFrame(index=feature_df.index, data=targetencoder.transform(
                feature_df), columns=feature_df.columns)
            # min max scale
            feature_df = pd.DataFrame(index=feature_df.index, data=scalerload.transform(
                feature_df), columns=feature_df.columns)

            # predict with loaded model
            predictedBelegung = modelload.predict(feature_df)
            predictedBelegung = pd.DataFrame(
                index=feature_df.index, data=(predictedBelegung).astype('int'))
            # add predictions to database
            for index, row in predictedBelegung.iterrows():
                # monday = 0, sunday =6
                dayOfWeek = index.dayofweek
                hourOfDay = index.hour
                date = index.strftime("%Y-%m-%d %H:%M:%S")
                # rmse only for full hours
                try:
                    rmse = rmseload[dayOfWeek][hourOfDay]
                    rmse = np.square(rmse)
                    rmse = np.mean(rmse)
                    rmse = np.sqrt(rmse)
                except:
                    rmse = -999
                occupation = row[0]
                prediction = Prediction(datetime=date,
                                        occupation=occupation, rmse=rmse, parkingspot_id=parkingspot.id)
                db.session.add(prediction)
                num_rows_added += 1
            db.session.commit()

        except Exception as e:
            print(e)

    return jsonify({"messege": "added {} records to database".format(num_rows_added)})

@app.route('/historicOccupancy')
def get_historic_occupancies():
    """ Endpoint for historic occupancies.

        Returns:
            historic occupancies as json
    """
    occupancies_dir = Path("data/parkingspot_occupancy")
    df = historicOccupanciesToDataframe(occupancies_dir)
    return df.to_json(orient='index')


@app.route('/historicMaxOccupancy')
def get_historic_max_occupancies():
    """ Endpoint for historic maximum occupancies.

        Returns:
            historic maximum occupancies as json
    """
    maxoccupancies_dir = Path("data/parkingspot_maxoccupancy")
    df = historicOccupanciesToDataframe(maxoccupancies_dir)
    return df.to_json(orient='index')


@app.route('/weather/updateDb')
def update_weather_database():
    """ Endpoint for updating weather data in the historic weather table.

        Returns:
            saves historic weather data in the database
    """
    # current date
    today = datetime.now()

    # Data from dwd opendata
    station_id = "03137"  # Mainz-Lerchenberg
    zip_file_url_temperature_recent = "http://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/recent/stundenwerte_TU_" 
    + station_id + "_akt.zip"
    zip_file_url_precipitation_recent = "http://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/precipitation/recent/stundenwerte_RR_" 
    + station_id + "_akt.zip"

    df_temp = zipfileToDataframe(
        url=zip_file_url_temperature_recent, seperator=";")
    df_precip = zipfileToDataframe(
        url=zip_file_url_precipitation_recent, seperator=";")

    # get last timestamp in database
    resultset = db.session.query(HistoricWeather).order_by(
        HistoricWeather.datetime.desc()).first()
    try:
        last_timestamp = (resultset.datetime).strftime("%Y-%m-%dT%H:%M:%S")
    except:
        last_timestamp = (datetime.today() - relativedelta(years=1)
                          ).strftime("%Y-%m-%dT%H:%M:%S")

    # resize dataframes with new weather data
    df_temp = df_temp.loc[last_timestamp:today]
    df_precip = df_precip.loc[last_timestamp:today]

    # fill missing timestamps in range of the data and assign value '-999.0'
    begin = df_temp.iloc[0].name
    end = df_temp.iloc[-1].name
    idx = pd.date_range(start=begin, end=end, freq='H')
    idx_df = pd.DataFrame(index=idx)
    df_temp = idx_df.join(df_temp)
    df_temp = df_temp.fillna(value=-999)
    df_precip = idx_df.join(df_precip)
    df_precip = df_precip.fillna(value=-999)

    num_rows_added = 0

    # add new records to database
    for record, ((index_temp, row_temp), (index_precip, row_precip)) in enumerate(zip(df_temp.iterrows(), df_precip.iterrows())):
        timestamp = index_temp
        temperature = row_temp[2]
        humidity = row_temp[3]
        precipation_last_hour = row_precip[2]
        historic_weather = HistoricWeather(
            datetime=timestamp, temperature=temperature, humidity=humidity, precipation_last_hour=precipation_last_hour)
        try:
            db.session.add(historic_weather)
            db.session.commit()
            num_rows_added += 1
        except:
            db.session.rollback()

    return jsonify({"message": "successfully updated {} records".format(num_rows_added)})


@app.route('/weather/getForecasts')
def update_weather_forecast_database():
    """ Endpoint for updating weather data in the forecast weather table.

        Returns:
            saves weather forecasts in the database
    """
    # remove all recorda from prediction table
    try:
        num_rows_deleted = db.session.query(ForecastWeather).delete()
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"message": "error when clearing records in table forecast_weather"})

    forecasts = getForecastsAsDataframe()
    num_rows_added = 0
    for index, row in forecasts.iterrows():
        forecast = ForecastWeather(
            datetime=index, temperature=row['TTT'], precipation_last_hour=row['RR1c'])
        db.session.add(forecast)
        try:
            db.session.commit()
            num_rows_added += 1
        except:
            db.session.rollback()
    return jsonify({"message": "successfully updated {} records".format(num_rows_added)})


    ############################
    #### utility functions #####
    ############################

def create_feature_df(ferienRlp, ferienHe, feiertageRlp, feiertageHe):
    now = datetime.today()
    now = datetime.strptime(
        str(now.year) + str(now.month)+str(now.day), '%Y%m%d')
    days = pd.date_range(now, now+relativedelta(days=7), freq='15min')

    interpolated_complete_data = pd.DataFrame(index=days)

    # ### weekdays (Mo=0; So=6)
    interpolated_complete_data['Wochentag'] = interpolated_complete_data.index.dayofweek

    # ### daytime in minutes
    interpolated_complete_data['Uhrzeit'] = interpolated_complete_data.index.hour * \
        60.0 + interpolated_complete_data.index.minute

    kwseries = pd.Series(interpolated_complete_data.index, name='KW',
                         index=interpolated_complete_data.index).apply(calcCalendarWeek)
    interpolated_complete_data['KW'] = kwseries

    # ### month
    interpolated_complete_data['Monat'] = interpolated_complete_data.index.month

    # ### holidays
    #

    feiertageRlp_df = feiertageRlp
    feiertageHe_df = feiertageHe

    feiertagseries_rlp = pd.Series(interpolated_complete_data.index, name='Feiertage',
                                   index=interpolated_complete_data.index).apply(shoppingdaystonextfeiertag, args=(feiertageRlp,))
    feiertagseries_he = pd.Series(interpolated_complete_data.index, name='Feiertage',
                                  index=interpolated_complete_data.index).apply(shoppingdaystonextfeiertag, args=(feiertageHe,))
    interpolated_complete_data['bisFeiertagRlp'] = feiertagseries_rlp
    interpolated_complete_data['bisFeiertagHe'] = feiertagseries_he

    after_feiertagseries_01 = pd.Series(interpolated_complete_data.index, name='Feiertage',
                                        index=interpolated_complete_data.index).apply(shoppingdaysafterfeiertag, args=(feiertageRlp,))
    after_feiertagseries_02 = pd.Series(interpolated_complete_data.index, name='Feiertage',
                                        index=interpolated_complete_data.index).apply(shoppingdaysafterfeiertag, args=(feiertageHe,))
    interpolated_complete_data['nachFeiertagRlp'] = after_feiertagseries_01
    interpolated_complete_data['nachFeiertagHe'] = after_feiertagseries_02

    # ### vacations

    interpolated_complete_data['SchulferienRlp'] = 0
    for sf in ferienRlp.iterrows():
        interpolated_complete_data['SchulferienRlp'].loc[sf[1]
                                                         ['start']:sf[1]['end']] = 1

    interpolated_complete_data['SchulferienHe'] = 0
    for sf in ferienHe.iterrows():
        interpolated_complete_data['SchulferienHe'].loc[sf[1]
                                                        ['start']:sf[1]['end']] = 1

    # ### Christmas
    weihnachtsseries = pd.Series(interpolated_complete_data.index, name='Weihnachten',
                                 index=interpolated_complete_data.index).apply(isweihnachten)
    interpolated_complete_data['Weihnachten'] = weihnachtsseries

    return interpolated_complete_data

def calcCalendarWeek(df):
    """ calculates actual calender week.
    """
    now = df.date()
    kw = datetime2.date(now.year, now.month, now.day).isocalendar()[1]
    return kw


# ### working days till next holiday
oldDay = ''
olddiffs = ''

def shoppingdaystonextfeiertag(df, feiertage):
    """ calculates workingdays till next holiday.
    """
    global oldDay
    global olddiffs
    diffs = []
    if df.date() == oldDay:
        try:
            return min([d for d in olddiffs if d >= 0])
        except:
            return 100  # if no holiday found
    else:
        for feiertag in feiertage.date:
            diff = np.busday_count(
                df.date(), feiertag.date(), weekmask='Mon Tue Wed Thu Fri Sat')
            diffs.append(diff)
        oldDay = df.date()
        olddiffs = diffs
    try:
        return min([d for d in diffs if d >= 0])
    except:
        return 100  # if no holiday found


# ## weekdays after holiday
oldDay = ''
olddiffs = ''


def shoppingdaysafterfeiertag(df, feiertage):
    """ calculates workingdays after last holiday.
    """
    global oldDay
    global olddiffs
    diffs = []
    if df.date() == oldDay:
        try:
            return min([d for d in olddiffs if d >= 0])
        except:
            return 100  # wenn kein Feiertag gefunden
    else:
        for feiertag in feiertage.date:
            diff = np.busday_count(
                feiertag.date(), df.date(), weekmask='Mon Tue Wed Thu Fri Sat')
            # print('%s bis %s: %i Arbeitstage' % (feiertag, df, diff))
            diffs.append(diff)
        oldDay = df.date()
        olddiffs = diffs
    try:
        return min([d for d in diffs if d >= 0])
    except:
        return 100  # wenn kein Feiertag gefunden

def isweihnachten(series):
    """ flags december as christmas month.
    """
    if series.month == 12:
        return 1
    else:
        return 0


def fillMissingValues(timeseries, column):
    """
    Fills all zero values(=-999) with the mean value of the previous 4 weeks 
    on the same weekday at the same time of day.

    If no values are found, the values of the following 4 weeks are used.
    """
    copydf = timeseries.copy()
    for index, row in timeseries.iterrows():
        if row[column] == -999:
            count_valid_weeks = 0
            sum_belegung = 0
            week_minus1 = index - datetime.timedelta(days=7)
            week_minus2 = index - datetime.timedelta(days=14)
            week_minus3 = index - datetime.timedelta(days=21)
            week_minus4 = index - datetime.timedelta(days=28)
            try:
                belegung_week_minus1 = timeseries.loc[week_minus1][column]
                if belegung_week_minus1 > -1:
                    count_valid_weeks += 1
                    sum_belegung += belegung_week_minus1
            except:
                pass
            try:
                belegung_week_minus2 = timeseries.loc[week_minus2][column]
                if belegung_week_minus2 > -1:
                    count_valid_weeks += 1
                    sum_belegung += belegung_week_minus2
            except:
                pass
            try:
                belegung_week_minus3 = timeseries.loc[week_minus3][column]
                if belegung_week_minus3 > -1:
                    count_valid_weeks += 1
                    sum_belegung += belegung_week_minus3
            except:
                pass
            try:
                belegung_week_minus4 = timeseries.loc[week_minus4][column]
                if belegung_week_minus4 > -1:
                    count_valid_weeks += 1
                    sum_belegung += belegung_week_minus4
            except:
                pass
            week_plus1 = index + datetime.timedelta(days=7)
            week_plus2 = index + datetime.timedelta(days=14)
            week_plus3 = index + datetime.timedelta(days=21)
            week_plus4 = index + datetime.timedelta(days=28)
            try:
                belegung_week_plus1 = timeseries.loc[week_plus1][column]
                if belegung_week_plus1 > -1:
                    count_valid_weeks += 1
                    sum_belegung += belegung_week_plus1
            except:
                pass
            try:
                belegung_week_plus2 = timeseries.loc[week_plus2][column]
                if belegung_week_plus2 > -1:
                    count_valid_weeks += 1
                    sum_belegung += belegung_week_plus2
            except:
                pass
            try:
                belegung_week_plus3 = timeseries.loc[week_plus3][column]
                if belegung_week_plus3 > -1:
                    count_valid_weeks += 1
                    sum_belegung += belegung_week_plus3
            except:
                pass
            try:
                belegung_week_plus4 = timeseries.loc[week_plus4][column]
                if belegung_week_plus4 > -1:
                    count_valid_weeks += 1
                    sum_belegung += belegung_week_plus4
            except:
                pass
            if count_valid_weeks > 0:
                mean_occupancy_4weeks = sum_belegung / count_valid_weeks
                copydf.loc[index][column] = mean_occupancy_4weeks
        else:
            pass

    return copydf


def drop_constant_rows_from_df(df, column_to_look_at, number_of_constant_rows):
    h = 0
    to_delete = []
    list_of_indices_which_get_deleted = []

    for index, row in df.iterrows():
        if (h < len(df.free)-1):
            if row[column_to_look_at] == df[column_to_look_at][h+1]:
                to_delete.append(index)
            else:
                if (len(to_delete) > number_of_constant_rows):
                    list_of_indices_which_get_deleted.extend(to_delete)
                to_delete = []
        h += 1
    df_return = df.copy()

    for each in list_of_indices_which_get_deleted:
        df_return.loc[each][column_to_look_at] = -999
    return list_of_indices_which_get_deleted, df_return


def historicshift(df, column='Belegung', lagsize=2, T=999, shifttime=336, dropna=True, timestap=336):
    newdf = pd.DataFrame(index=df.index, data=0, columns=['histBelegung'])
    for i in range(0, lagsize):
        newdf['histBelegung'] = newdf['histBelegung'] + \
            df[column].shift(shifttime+(timestap*i))
    newdf['histBelegung'] = newdf['histBelegung']/lagsize
    newdf.dropna(inplace=True)
    return newdf


def historicshift2(df, column='Belegung', lagsize=2, T=999, shifttime=336, dropna=True, timestap=336):
    name = 'hist'+column
    newdf = pd.DataFrame(index=df.index, data=0, columns=[name])
    for i in range(0, lagsize):
        newdf[name] = newdf[name] + df[column].shift(shifttime+(timestap*i))
    newdf[name] = newdf[name]/lagsize
    newdf.dropna(inplace=True)
    return newdf
