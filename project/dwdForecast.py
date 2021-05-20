# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 20:23:52 2020

most code from https://github.com/jlewis91/dwdbulk/blob/master/dwdbulk/
"""

from zipfile import ZipFile
from urllib.parse import urlparse
import shutil
import requests
import os
from pathlib import Path
from typing import List
import pandas as pd
import tempfile
from lxml import etree
import numpy as np


def parse_htmllist(baseurl, content, extension=None, full_url=True):
    class ListParser(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.data = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                for attr in attrs:
                    if attr[0] == "href" and attr[1] != "../":
                        self.data.append(attr[1])

    parser = ListParser()
    parser.feed(content)
    paths = parser.data
    parser.close()

    if extension:
        paths = [path for path in paths if extension in path]

    if full_url:
        return [urljoin(baseurl + "/", path) for path in paths]
    else:
        return [path.rstrip("/") for path in paths]


def get_resource_index(url, extension="", full_url=True):
    """
    Extract link list from HTML, given a url
    :params str url: url of a webpage with simple HTML link list
    :params str extension: String that should be matched in the link list; if "", all are returned
    """

    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Fetching resource {url} failed")
    resource_list = parse_htmllist(url, response.text, extension, full_url)
    return resource_list


def fetch_raw_forecast_xml(url, directory_path):
    """
    Fetch weather forecast file (zipped xml) and extract xml into folder specified by xml_directory_path.
    """
    directory_path = Path(directory_path)

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    r = requests.get(url, stream=True)
    file_name = urlparse(url).path.replace("/", "__")

    if r.status_code == 200:
        with open(directory_path / file_name, "wb") as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

        with ZipFile(directory_path / file_name, "r") as zipObj:
            # Extract all the contents of zip file in current directory
            zipObj.extractall(path=directory_path)
            return directory_path / zipObj.namelist()[0]


def convert_xml_to_pandas(
        filepath,
        station_ids: List = None,
        parameters: List = None,
        return_station_data=False):
    """
    Convert DWD XML Weather Forecast File of Type MOSMIX_S to parquet files.
    """

    tree = etree.parse(str(filepath))
    root = tree.getroot()

    prod_items = {
        "product_id": "ProductID",
        "generating_process": "GeneratingProcess",
        "date_issued": "IssueTime",
    }

    # Get Basic Metadata
    prod_definition = root.findall(
        "kml:Document/kml:ExtendedData/dwd:ProductDefinition", root.nsmap
    )[0]

    metadata = {
        k: prod_definition.find(f"{{{root.nsmap['dwd']}}}{v}").text
        for k, v in prod_items.items()
    }
    metadata["date_issued"] = pd.Timestamp(metadata["date_issued"])

    # Get Time Steps
    timesteps = root.findall(
        "kml:Document/kml:ExtendedData/dwd:ProductDefinition/dwd:ForecastTimeSteps",
        root.nsmap,
    )[0]
    timesteps = [pd.Timestamp(i.text) for i in timesteps.getchildren()]

    # Get Per Station Forecasts
    forecast_items = root.findall("kml:Document/kml:Placemark", root.nsmap)

    df_list = []

    for station_forecast in forecast_items:
        station_id = station_forecast.find("kml:name", root.nsmap).text

        if (station_ids is None) or station_id in station_ids:
            measurement_list = station_forecast.findall(
                "kml:ExtendedData/dwd:Forecast", root.nsmap
            )
            df = pd.DataFrame({"date_start": timesteps})

            for measurement_item in measurement_list:

                measurement_parameter = measurement_item.get(
                    f"{{{root.nsmap['dwd']}}}elementName"
                )

                if parameters is None or measurement_parameter in parameters:

                    measurement_string = measurement_item.getchildren()[0].text

                    measurement_values = " ".join(
                        measurement_string.split()).split(" ")
                    measurement_values = [
                        np.nan if i == "-" else float(i) for i in measurement_values
                    ]

                    assert len(measurement_values) == len(
                        timesteps
                    ), "Number of timesteps does not match number of measurement values."
                    df[measurement_parameter] = measurement_values

            df["station_id"] = station_id
            for k, v in metadata.items():
                df[k] = v

            df_list.append(df)

    df = pd.concat(df_list, axis=0)

    if return_station_data:
        station_df = [
            {
                "coordinates": station_forecast.find(
                    "kml:Point/kml:coordinates", root.nsmap
                ).text.split(","),
                "station_id": station_forecast.find("kml:name", root.nsmap).text,
                "station_name": station_forecast.find(
                    "kml:description", root.nsmap
                ).text,
            }
            for station_forecast in forecast_items
        ]
        station_df = pd.DataFrame(station_df)
        station_df["geo_lon"] = station_df["coordinates"].apply(
            lambda x: float(x[0]))
        station_df["geo_lat"] = station_df["coordinates"].apply(
            lambda x: float(x[1]))
        station_df["height"] = station_df["coordinates"].apply(
            lambda x: float(x[2]))
        del station_df["coordinates"]

        return df, station_df
    else:
        return df


def getForecastsAsDataframe():
    # list with station names
    # https://www.dwd.de/EN/ourservices/met_application_mosmix/mosmix_stations.html
    station = "K584"
    url = "http://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/" + \
        str(station) + "/kml/MOSMIX_L_LATEST_" + str(station) + ".kmz"

    df = pd.DataFrame()
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        kml_path = fetch_raw_forecast_xml(url, tmp_dir_name)
        df = convert_xml_to_pandas(kml_path)

    df.set_index('date_start', inplace=True)
    #convert Kelvin to °C
    df['TTT'] = df['TTT'] - 273.15
    df = df[['TTT', 'RR1c']]
    return df
