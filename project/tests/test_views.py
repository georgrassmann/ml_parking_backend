import os
import unittest
import numpy
from psycopg2.extensions import register_adapter, AsIs

from project import app


class ViewTests(unittest.TestCase):

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

    # register adapters to avoid error messages
    # see: https://www.psycopg.org/docs/advanced.html#adapting-new-python-types-to-sql-syntax
    def addapt_numpy_float64(numpy_float64):
        return AsIs(numpy_float64)
    def addapt_numpy_int64(numpy_int64):
        return AsIs(numpy_int64)
    register_adapter(numpy.float64, addapt_numpy_float64)
    register_adapter(numpy.int64, addapt_numpy_int64)

###############
#### tests ####
###############

    print("### Performing Endpoint Tests ###")

    def test_parkingspot_endpoint(self):
        response = self.app.get('/parkingspots', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_predict_endpoint(self):
        response = self.app.get('/predict', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_historicOccupancy_endpoint(self):
        response = self.app.get('/historicOccupancy', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_historicMaxOccupancy_endpoint(self):
        response = self.app.get('/historicMaxOccupancy', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_updateWeather_endpoint(self):
        response = self.app.get('/weather/updateDb', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_getWeatherForecasts_endpoint(self):
        response = self.app.get('/weather/getForecasts', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
