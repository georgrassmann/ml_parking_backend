from flask.cli import FlaskGroup

from project import app, db
from project.models import Parkingspot, HistoricOccupancy, HistoricWeather, ForecastWeather, Prediction, VacationRLP, VacationHE, HolidayRLP, HolidayHE, db

import pandas as pd
import math
import os
import glob
from datetime import datetime
from pathlib import Path
from project.utils import zipfileToDataframe, concatenateHistoricRecentData, historicOccupanciesToDataframe
import numpy
from psycopg2.extensions import register_adapter, AsIs

# register adapters to avoid error messages
# see: https://www.psycopg.org/docs/advanced.html#adapting-new-python-types-to-sql-syntax
def addapt_numpy_float64(numpy_float64):
    return AsIs(numpy_float64)
def addapt_numpy_int64(numpy_int64):
    return AsIs(numpy_int64)
register_adapter(numpy.float64, addapt_numpy_float64)
register_adapter(numpy.int64, addapt_numpy_int64)

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("seed_db")
def seed_db():
    seed_holidays()
    seed_vacations()
    seed_parkingspots()
    seed_predictions()
    seed_occupancies_historic()
    seed_weather_historic()
    seed_weather_forecast()

# ## Seed functions


def seed_parkingspots():
    print("seeding table parkingspots")

    df = pd.read_csv(r'data/parkingspot_info/parkhaus_infos.csv')
    for index, row in df.iterrows():
        parkingspot = Parkingspot(name=row['Name'], max_occupancy=row['MaxAnzahl'],
                                  lat=row['Lat'], lon=row['Lon'], open=row['OpeningHours'],
                                  parkingspot_type=row['Type'], height_limit=row['HeightLimit'],
                                  handicapped_spots=row['Handicapped'], women_spots=row['Women'],
                                  parent_child_spots=row['ParentsChild'], address=row['Address'],
                                  url=row['URL'])
        db.session.add(parkingspot)
    try:
        db.session.commit()
    except:
        db.session.rollback()


def seed_occupancies_historic():
    print("seeding table occupancies_historic")

    occupancies_dir = Path("data/parkingspot_occupancy")
    max_occupancies_dir = Path("data/parkingspot_maxoccupancy")

    df_occupancies = historicOccupanciesToDataframe(occupancies_dir)
    df_maxoccupancies = historicOccupanciesToDataframe(max_occupancies_dir)
    parkingspotNames = list(df_occupancies)
    print("Parkingspots: " , parkingspotNames)
    for parkingspotName in parkingspotNames:
        print("seeding " + parkingspotName + " ...")
        try:
            parkingspot_db = Parkingspot.query.filter_by(
                name=parkingspotName).first()
            parkingspot_id = parkingspot_db.id
            for index, row in df_occupancies.iterrows():
                timestamp = index
                occupation = row[parkingspotName]
                try:
                    maxOccupation = df_maxoccupancies.loc[timestamp,parkingspotName]
                except:
                    maxOccupation = parkingspot_db.max_occupancy
                # check for missing values
                if math.isnan(occupation):
                    occupation = -999
                if math.isnan(maxOccupation):
                    maxOccupation = parkingspot_db.max_occupancy
                historic_occupancy = HistoricOccupancy(
                    datetime=timestamp, occupation=occupation, max_occupation= maxOccupation, parkingspot_id=parkingspot_id)
                db.session.add(historic_occupancy)
            #try:
            db.session.commit()
            #except:
                #db.session.rollback()
        except:
            print("Error: Parkingspot {} not found in DB".format(parkingspotName))


def seed_predictions():
    print("seeding table predictions")
    prediction = Prediction(datetime="2020-01-14T07:15:00",
                            occupation=98,rmse=10, parkingspot_id=1)
    db.session.add(prediction)
    prediction = Prediction(datetime="2020-01-15T07:45:00",
                            occupation=98,rmse=10, parkingspot_id=1)
    db.session.add(prediction)
    prediction = Prediction(datetime="2020-01-14T07:15:00",
                            occupation=97,rmse=10, parkingspot_id=2)
    db.session.add(prediction)
    prediction = Prediction(datetime="2020-01-15T07:45:00",
                            occupation=11,rmse=10, parkingspot_id=2)
    db.session.add(prediction)
    db.session.commit()


def seed_weather_historic():
    print("seeding table weather_historic")

    # remove all records
    try:
        num_rows_deleted = db.session.query(HistoricWeather).delete()
        db.session.commit()
    except:
        db.session.rollback()

    try:
        # drop table
        db.metadata.drop_all(bind=db.engine, tables=[
                             HistoricWeather.__table__])
        # create table
        db.metadata.create_all(bind=db.engine, tables=[
                               HistoricWeather.__table__])
        db.session.commit()
    except:
        print("table weather_historic didn`t exists")

    # Data from dwd opendata
    station_id = "03137"  # Mainz-Lerchenberg
    zip_file_url_temperature_recent = "http://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/recent/stundenwerte_TU_" + station_id + "_akt.zip"
    zip_file_url_precipitation_recent = "http://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/precipitation/recent/stundenwerte_RR_" + station_id + "_akt.zip"

    zip_file_url_temperature_historical = "http://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/historical/stundenwerte_TU_" + \
        station_id + "_20080501_20181231_hist.zip"
    zip_file_url_precipitation_historical = "http://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/precipitation/historical/stundenwerte_RR_" + \
        station_id + "_20080501_20181231_hist.zip"

    # zip files to dataframes
    df_temp_hist = zipfileToDataframe(
        url=zip_file_url_temperature_historical, seperator=";")
    df_precip_hist = zipfileToDataframe(
        url=zip_file_url_precipitation_historical, seperator=";")
    df_temp_recent = zipfileToDataframe(
        url=zip_file_url_temperature_recent, seperator=";")
    df_precip_recent = zipfileToDataframe(
        url=zip_file_url_precipitation_recent, seperator=";")

    df_temp = concatenateHistoricRecentData(df_temp_hist, df_temp_recent)
    df_precip = concatenateHistoricRecentData(df_precip_hist, df_precip_recent)

    start_date = '2014-12-31'
    end_date = datetime.now()
    df_temp = df_temp.loc[start_date:end_date]
    # only keep records from start_date till yesterday
    df_temp = df_temp.loc[start_date:end_date]
    df_precip = df_precip.loc[start_date:end_date]

    for record, ((index_temp, row_temp), (index_precip, row_precip)) in enumerate(zip(df_temp.iterrows(), df_precip.iterrows())):
        timestamp = index_temp
        temperature = row_temp[2]
        humidity = row_temp[3]
        precipation_last_hour = row_precip[2]
        historic_weather = HistoricWeather(
            datetime=timestamp, temperature=temperature, humidity=humidity, precipation_last_hour=precipation_last_hour)
        db.session.add(historic_weather)
    db.session.commit()


def seed_weather_forecast():
    print("seeding table weather_forecast")

def seed_holidays():
    print("seeding tables holiday_rlp and holiday_he")
    dir = Path("data/holidays")
    files = dir.glob("*.csv")
    for file in files:
        df = pd.read_csv(file, dayfirst=True,parse_dates=True)
        for index,row in df.iterrows():
            date = datetime.strptime(row[0],"%d.%m.%Y")
            if("rlp" in str(file)):
                holiday = HolidayRLP(date=date)
            else:
                holiday = HolidayHE(date=date)
            db.session.add(holiday)
        db.session.commit()
        

def seed_vacations():
    print("seeding tables vacation_rlp and vacation_he")
    dir = Path("data/vacations")
    files = dir.glob("*.csv")
    for file in files:
        df = pd.read_csv(file, parse_dates=[0,1])
        for index,row in df.iterrows():
            if("rlp" in str(file)):
                vacation = VacationRLP(start=row[0], end=row[1])
            else:
                vacation = VacationHE(start=row[0], end=row[1])
            db.session.add(vacation)
        db.session.commit()


if __name__ == "__main__":
    cli()
