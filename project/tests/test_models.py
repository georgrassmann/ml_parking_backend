import os
import unittest

from project import app
from project.models import Parkingspot, HistoricOccupancy, HistoricWeather, ForecastWeather, Prediction, VacationRLP, VacationHE, HolidayRLP, HolidayHE


class ModelTests(unittest.TestCase):

    ############################
    #### setup and teardown ####
    ############################

    # executed prior to each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user42:hsmainz@143.93.114.137:54322/database'
        self.app = app.test_client()
        self.assertEqual(app.debug, False)

    # executed after each test
    def tearDown(self):
        pass

###############
#### tests ####
###############

    print("### Performing Model Tests ###")

    def test_Parkingspot(self):
         # create new Parkingspot
        new_parkingspot = Parkingspot(name="testPS", max_occupancy=999,
                                      lat=50.0, lon=8.0, open="0-24h",
                                      parkingspot_type="Parkhaus", height_limit="2 m",
                                      handicapped_spots="22", women_spots="3",
                                      parent_child_spots="10", address="Musterstrasse 22",
                                      url="www.test.com")

        self.assertEqual(new_parkingspot.name, "testPS")
        self.assertEqual(new_parkingspot.max_occupancy, 999)
        self.assertEqual(new_parkingspot.lat, 50.0)
        self.assertEqual(new_parkingspot.lon, 8.0)
        self.assertEqual(new_parkingspot.open, "0-24h")
        self.assertEqual(new_parkingspot.parkingspot_type, "Parkhaus")
        self.assertEqual(new_parkingspot.height_limit, "2 m")
        self.assertEqual(new_parkingspot.handicapped_spots, "22")
        self.assertEqual(new_parkingspot. women_spots, "3")
        self.assertEqual(new_parkingspot.parent_child_spots, "10")
        self.assertEqual(new_parkingspot.address, "Musterstrasse 22")
        self.assertEqual(new_parkingspot.url, "www.test.com")

    def test_HistoricOccupancy(self):

        # create new HistoricOccupancy
        new_HistoricOccupancy = HistoricOccupancy(
            datetime="2020-02-10 13:00:00", occupation=99, max_occupation=100, parkingspot_id=1)

        self.assertEqual(new_HistoricOccupancy.datetime, "2020-02-10 13:00:00")
        self.assertEqual(new_HistoricOccupancy.occupation, 99)
        self.assertEqual(new_HistoricOccupancy.max_occupation, 100)
        self.assertEqual(new_HistoricOccupancy.parkingspot_id, 1)

    def test_HistoricWeather(self):

        # create new HistoricWeather
        new_historicWeather = HistoricWeather(
            datetime="2020-02-10 13:00:00", temperature=10.2, humidity=77, precipation_last_hour=1)

        self.assertEqual(new_historicWeather.datetime, "2020-02-10 13:00:00")
        self.assertEqual(new_historicWeather.temperature, 10.2)
        self.assertEqual(new_historicWeather.humidity, 77)
        self.assertEqual(new_historicWeather.precipation_last_hour, 1)

    def test_ForecastWeather(self):

        # create new HistoricWeather
        new_forecastWeather = ForecastWeather(
            datetime="2020-02-10 13:00:00", temperature=10.2, precipation_last_hour=1)

        self.assertEqual(new_forecastWeather.datetime, "2020-02-10 13:00:00")
        self.assertEqual(new_forecastWeather.temperature, 10.2)
        self.assertEqual(new_forecastWeather.precipation_last_hour, 1)

    def test_Prediction(self):

        # create new Prediction
        new_prediction = Prediction(
            datetime="2020-02-10 13:00:00", occupation=99, rmse=10, parkingspot_id=1)

        self.assertEqual(new_prediction.datetime, "2020-02-10 13:00:00")
        self.assertEqual(new_prediction.occupation, 99)
        self.assertEqual(new_prediction.rmse, 10)
        self.assertEqual(new_prediction.parkingspot_id, 1)

    def test_VacationRLP(self):

        # create new VacationRLP
        new_vacationRLP = VacationRLP(
            start="2020-02-17 23:00:00", end="2020-02-25 23:00:00")

        self.assertEqual(new_vacationRLP.start, "2020-02-17 23:00:00")
        self.assertEqual(new_vacationRLP.end, "2020-02-25 23:00:00")

    def test_VacationHE(self):

        # create new VacationHE
        new_vacationHE = VacationHE(
            start="2020-02-17 00:00:00", end="2020-02-27 00:00:00")

        self.assertEqual(new_vacationHE.start, "2020-02-17 00:00:00")
        self.assertEqual(new_vacationHE.end, "2020-02-27 00:00:00")

    def test_HolidayRLP(self):

        # create new HolidayRLP
        new_holidayRLP = HolidayRLP(date="2020-01-01")

        self.assertEqual(new_holidayRLP.date, "2020-01-01")

    def test_HolidayHE(self):

        # create new HolidayHE
        new_holidayHE = HolidayHE(date="2020-01-01")

        self.assertEqual(new_holidayHE.date, "2020-01-01")


if __name__ == "__main__":
    unittest.main()
