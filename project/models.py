from project import db

class Parkingspot(db.Model):
    """
    A class used to represent parkingspots in the database


    Attributes
    ----------
    __tablename__ : str
        the name of the table
    id : int
        primary key of the table
    name : str
        the name of the parkingspot
    max_occupancy : int
        the maximum number of parking places
    lat : float
        the latitude of the parking spot
    lon : float
        the longitude of the parking spot
    open : str
        the opening hours of the parking spot
    parkingspot_type : str
        the type of the parking spot ('Parkhaus', 'Parkplatz', 'Tiefgarage')
    height_limit : str
        the maximum height of the vehicle, which authorizes the entry into the parking spot
    handicapped_spots : str
        information on the availability of parking spaces for handicapped people
    women_spots : str
        information on the availability of parking spaces for handicapped people
    parent_child_spots : str
        information on the availability of parent child parking places
    address : str
        the address of the parking spot
    url : str
        the hyperlink to the website of the parking spot
    predictions : 
        relationship to table 'Predictions'
    occupancies : float
        relationship to table 'HistoricOccupancy'

    Methods
    -------
    says(sound=None)
        Prints the animals name and what sound it makes
    """
    __tablename__ = "parkingspot"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    max_occupancy = db.Column(db.Integer, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    open = db.Column(db.String(20), nullable=False)
    parkingspot_type = db.Column(db.String(20), nullable=False)
    height_limit = db.Column(db.String(20), nullable=False)
    handicapped_spots = db.Column(db.String(20), nullable=False)
    women_spots = db.Column(db.String(20), nullable=False)
    parent_child_spots = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(120), nullable=False)
    predictions = db.relationship(
        'Prediction', backref='parkingspot', lazy='select')
    occupancies = db.relationship(
        'HistoricOccupancy', backref='parkingspot', lazy='select')

    def __init__(self, name, max_occupancy, lat, lon, open, parkingspot_type, height_limit,
                 handicapped_spots, women_spots, parent_child_spots, address, url):
        self.name = name
        self.max_occupancy = max_occupancy
        self.lat = lat
        self.lon = lon
        self.open = open
        self.parkingspot_type = parkingspot_type
        self.height_limit = height_limit
        self.handicapped_spots = handicapped_spots
        self.women_spots = women_spots
        self.parent_child_spots = parent_child_spots
        self.address = address
        self.url = url

class HistoricOccupancy(db.Model):
    """
    A class used to represent hictoric occupancy data in the database


    Attributes
    ----------
    __tablename__ : str
        the name of the table
    id : int
        primary key of the table
    datetime : date
        date and time of occupation
    occupation : int
        the occupation at each time point
    max_occupation : int
        the maximum occupation at each time point
    parkingspot_id : int
        foreign key - reference to table 'parkingspot'
    
    """
    __tablename__ = "historic_occupancy"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    occupation = db.Column(db.Integer, nullable=False)
    max_occupation = db.Column(db.Integer, nullable=False)
    parkingspot_id = db.Column(db.Integer, db.ForeignKey('parkingspot.id'))

    def __init__(self, datetime, occupation, max_occupation, parkingspot_id):
        self.datetime = datetime
        self.occupation = occupation
        self.max_occupation = max_occupation
        self.parkingspot_id = parkingspot_id

class HistoricWeather(db.Model):
    """
    A class used to represent hictoric weather data in the database


    Attributes
    ----------
    __tablename__ : str
        the name of the table
    datetime : date
        date and time of occupation - acts as primary key
    temperature : float
        air temperature at 2m height [°C]
    humidity : float
        relative humidity [%]
    precipation_last_hour : float
        precipitation height of the last hour [mm]
    
    """
    __tablename__ = "historic_weather"
    datetime = db.Column(db.DateTime, primary_key=True, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    precipation_last_hour = db.Column(db.Float, nullable=False)

    def __init__(self, datetime, temperature, humidity, precipation_last_hour):
        self.datetime = datetime
        self.temperature = temperature
        self.humidity = humidity
        self.precipation_last_hour = precipation_last_hour

class ForecastWeather(db.Model):
    """
    A class used to represent forecast weather data in the database


    Attributes
    ----------
    __tablename__ : str
        the name of the table
    datetime : date
        date and time of occupation - acts as primary key
    temperature : float
        air temperature at 2m height [°C]
    precipation_last_hour : float
        precipitation height of the last hour [mm]
    
    """
    __tablename__ = "forecast_weather"
    datetime = db.Column(db.DateTime, primary_key=True, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    precipation_last_hour = db.Column(db.Float, nullable=False)

    def __init__(self, datetime, temperature, precipation_last_hour):
        self.datetime = datetime
        self.temperature = temperature
        self.precipation_last_hour = precipation_last_hour

class Prediction(db.Model):
    """
    A class used to represent predicted occupation data in the database


    Attributes
    ----------
    __tablename__ : str
        the name of the table
    id : int
        primary key of the table
    datetime : date
        date and time of occupation
    occupation : int
        the predicted occupation at each time point
    rmse : float
        the rmse for each prediction
    parkingspot_id : int
        foreign key - reference to table 'parkingspot'
    
    """
    __tablename__ = "prediction"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    occupation = db.Column(db.Integer, nullable=False)
    rmse = db.Column(db.Float, nullable=False)
    parkingspot_id = db.Column(db.Integer, db.ForeignKey('parkingspot.id'))

    def __init__(self, datetime, occupation, rmse, parkingspot_id):
        self.datetime = datetime
        self.occupation = occupation
        self.rmse = rmse
        self.parkingspot_id = parkingspot_id

class VacationRLP(db.Model):
    """
    A class used to represent vacations in  Rhineland-Palatinate in the database


    Attributes
    ----------
    __tablename__ : str
        the name of the table
    id : int
        primary key of the table
    start : date
        start date
    end : date
        ent date
    
    """
    __tablename__ = "vacation_rlp"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)

    def __init__(self, start, end):
        self.start = start
        self.end = end

class VacationHE(db.Model):
    """
    A class used to represent vacations in  Hessen in the database


    Attributes
    ----------
    __tablename__ : str
        the name of the table
    id : int
        primary key of the table
    start : date
        start date
    end : date
        ent date
    
    """
    __tablename__ = "vacation_he"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)

    def __init__(self, start, end):
        self.start = start
        self.end = end

class HolidayRLP(db.Model):
    """
    A class used to represent holidays in  Rhineland-Palatinate in the database


    Attributes
    ----------
    __tablename__ : str
        the name of the table
    id : int
        primary key of the table
    date : date
        date of the vacation
    
    """
    __tablename__ = "holiday_rlp"
    date = db.Column(db.DateTime, primary_key=True, nullable=False)

    def __init__(self, date):
        self.date = date

class HolidayHE(db.Model):
    """
    A class used to represent holidays in  Hessen in the database


    Attributes
    ----------
    __tablename__ : str
        the name of the table
    id : int
        primary key of the table
    date : date
        date of the vacation
    
    """
    __tablename__ = "holiday_he"
    date = db.Column(db.DateTime, primary_key=True, nullable=False)

    def __init__(self, date):
        self.date = date

