import io
import requests
import zipfile
import pandas as pd
from pathlib import Path
import csv
from datetime import datetime


def zipfileToDataframe(url, seperator):
    """ extracts a file from a .zip archive and transforms it to dataframe
    Returns: pandas dataframe object
    """
    r = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(r.content)) as zip:
        files = zip.namelist()
        matchingFile = [file for file in files if "produkt" in file]
        with zip.open(matchingFile[0]) as file:
            df = pd.read_csv(file, sep=seperator,
                             index_col="MESS_DATUM", parse_dates=False)
            df.index = pd.to_datetime(df.index, format="%Y%m%d%H")
            return df


def concatenateHistoricRecentData(df_hist, df_recent):
    """ concatenates two dataframes based on their datetime index \n
        fills missing values with -999
    Returns: concatenates dataframes without missing timestamps
    """
    # append historic and recent weather dataframes
    df_concat = df_hist.append(df_recent)
    # remove duplicates from overlapping timestamps and keep rows from historic data
    df_concat = df_concat.loc[~df_concat.index.duplicated(keep='first')]
    # fill missing timestamps in range of the data and assign value '-999.0'
    begin = df_concat.iloc[0].name
    end = df_concat.iloc[-1].name
    idx = pd.date_range(start=begin, end=end, freq='H')
    idx_df = pd.DataFrame(index=idx)
    df_concat = idx_df.join(df_concat)
    df_concat = df_concat.fillna(value=-999)
    return df_concat

def historicOccupanciesToDataframe(path):
    """ read historic occupancies and save them as a pandas dataframe
    Returns: dataframe with historic occupancies from parkingspots
    """
    occupancies_dir = Path(path)
    files = occupancies_dir.glob("*.csv")
    occupancy_dict = dict()
    for file in files:
        with open(file, "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            date = ""
            timestamp = ""
            for row in csv_reader:
                # handle header
                if line_count == 0:
                    # get parkingspot names
                    names = list(filter(lambda x: (x != "Gesamtergebnis" and x != "") , row))
                    line_count += 1
                # handle remaining rows
                else:
                    # ignore this rows
                    if ("KW" in row[0]):
                        pass
                    else:
                        # get date in format DD.MM.YYYY
                        try:
                            datetime.strptime(row[0],"%d.%m.%Y")
                            date = row[0]
                            continue
                        except:
                            pass
                        try:
                            # get single timestamp in format YYYY-MM-DD HH:MM:SS
                            timestamp = datetime.strptime((date + row[0]),"%d.%m.%Y%H:%M")
                            parking_dict = dict()
                            for name in names:
                                index = names.index(name)
                                occupancy = row[index + 1]
                                if ("." in occupancy):
                                    occupancy = occupancy.replace(".","")
                                if (occupancy == ""):
                                    occupancy = -999
                                try:
                                    occupancy = int(occupancy)
                                except:
                                    pass
                                parking_dict.update({name:occupancy})
                            occupancy_dict.update({timestamp: parking_dict})
                        except:
                            pass

    df = pd.DataFrame.from_dict(occupancy_dict, orient='index')
    df = df.fillna(-999)
    return df
