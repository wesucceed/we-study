import datetime
import hashlib
import os

import bcrypt
from flask_sqlalchemy import SQLAlchemy

from pandas import read_excel
db = SQLAlchemy()


def load_excel():

    polling_agents_df = read_excel('agents.xlsx')
    polling_station_results_df = read_excel('results.xlsx')
    polling_stations_df = read_excel('stations.xlsx')


    # Specify the table name and the SQLAlchemy engine
    engine = db.get_engine()

    # Insert the data into the database table
    polling_agents_df.to_sql("polling_agents", con = engine, if_exists = 'append', index = False, chunksize = 1000)
    polling_station_results_df.to_sql("polling_stations", con = engine, if_exists = 'append', index = False, chunksize = 1000)
    polling_stations_df.to_sql("polling_station_results", con = engine, if_exists = 'append', index = False, chunksize = 1000)


class Polling_Agent(db.Model):
    """
    Polling Agent Model
    """
    __tablename__ = "polling_agents"
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)

    # Polling Agent information
    name = db.Column(db.String, nullable = False)
    phone_number = db.Column(db.String, nullable = False, unique = True)


    password_digest = db.Column(db.String, nullable=False)

    # Session information
    session_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False, unique=True)


    # Polling station result

    polling_station_result = db.relationship("Polling_Station_Result", cascade = "delete")

    def __init__(self, **kwargs):
        """
        Initializes a polling agent object
        """
        self.name = kwargs.get("firstname") + " " + kwargs.get("lastname")
        password = kwargs.get("phone_number") + kwargs.get("firstname") + kwargs.get("lastname")
        self.password_digest = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt(rounds=13))
        self.phone_number = kwargs.get("phone_number")
        self.renew_session()

    def serialize(self):
        """
        Returns a serialized polling agent
        """
        res = {
            "name" : self.name,
            "phone number" : self.phone_number, 
            "polling station results" : [result.serialize() for result in self.polling_station_result]
        }
        return res

    def _urlsafe_base_64(self):
        """
        Randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()

    def renew_session(self):
        """
        Renews the sessions, i.e.
        1. Creates a new session token
        2. Sets the expiration time of the session to be a day from now
        3. Creates a new update token
        """
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        """
        Verifies the password of a user
        """
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

    def verify_session_token(self, session_token):
        """
        Verifies the session token of a user
        """
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        """
        Verifies the update token of a user
        """
        return update_token == self.update_token
        

class Polling_Station(db.Model):
    """
    Polling Station Model
    """
    __tablename__ = "polling_stations"
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)

    # Polling station results
    polling_station_result = db.relationship("Polling_Station_Result", cascade = "delete")

    # Polling Station information
    name = db.Column(db.String, nullable = False)
    number = db.Column(db.String, nullable = False, unique = True)
    region = db.Column(db.String, nullable = False)


    constituency_id = db.Column(db.Integer, db.ForeignKey("constituencies.id"), nullable = False, unique = True)



    def __init__(self, **kwargs):
        """
        Initializes a polling station object
        """
        self.name = kwargs.get("name") 
        self.number = kwargs.get("number") 
        self.constituency_id = kwargs.get("constituency_id")
        self.region = kwargs.get("region")

         
    def serialize(self):
        """
        Returns a serialized polling station
        """
        res = {
            "name" : self.name,
            "number" : self.number,
            "constituency" : self.constituency_id,
            "region" : self.region,
            "polling station result" : [result.serialize() for result in self.polling_station_result]
        }
        return res
    

class Polling_Station_Result(db.Model):
    """
    Polling Station Result Model
    """
    __tablename__ = "polling_station_results"
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)

    # Candidates with votes

    cand1 = db.Column(db.Integer, nullable = False)
    cand2 = db.Column(db.Integer, nullable = False)
    cand3 = db.Column(db.Integer, nullable = False)

    # measure of centendies
    total_valid_ballots = db.Column(db.Integer, default = 0, nullable = False)
    total_rejected_ballots = db.Column(db.Integer, default = 0, nullable = False)
    total_votes_cast = db.Column(db.Integer, default = 0, nullable = False)

    # pink sheet
    pink_sheet = db.Column(db.String, nullable = False, unique = True)

    # Polling agent posted
    polling_agent_id = db.Column(db.Integer, db.ForeignKey("polling_agents.id"), nullable = False, unique = True)

    # polling station
    polling_station_id = db.Column(db.Integer, db.ForeignKey("polling_stations.id"), nullable = False, unique = True)


    def __init__(self, **kwargs):
        """
        Initializes a polling station result
        """
        self.cand1 = kwargs.get("votes").get("cand1")
        self.cand2 = kwargs.get("votes").get("cand2") 
        self.cand3 = kwargs.get("votes").get("cand3")

        self.total_rejected_ballots = kwargs.get("total_rejected_ballots")
        self.total_valid_ballots = kwargs.get("total_valid_ballots")
        self.total_votes_cast = kwargs.get("total_votes_cast")

        self.pink_sheet = kwargs.get("pink_sheet")

        self.polling_agent_id = kwargs.get("polling_agent_id")
        self.polling_station_id = kwargs.get("polling_station_id")


    def serialize(self):
        """
        Returns a serialized polling station result
        """
        res = {
            "data" : {
                "cand1" : self.cand1,
                "cand2" : self.cand2,
                "cand3" : self.cand3}
                ,
            "total rejected ballots" : self.total_rejected_ballots,
            "total valid ballots" : self.total_valid_ballots,
            "total votes cast" : self.total_votes_cast,
            "pink sheet" : self.pink_sheet,
            "polling agent id" : self.polling_agent_id,
            "polling station id" : self.polling_station_id
        }
        return res
    

class Constituency(db.Model):
    """
    Constituency Model
    """
    __tablename__ = "constituencies"
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)

    # Polling station 
    polling_station = db.relationship("Polling_Station", cascade = "delete")

    # Constituency information
    name = db.Column(db.String, nullable = False)
    region = db.Column(db.String, nullable = False)


    def __init__(self, **kwargs):
        """
        Initializes a polling station object
        """
        self.name = kwargs.get("name") 
        self.region = kwargs.get("region")

         
    def serialize(self):
        """
        Returns a serialized polling station
        """
        res = {
            "name" : self.name,
            "region" : self.region,
            "polling station" : [station.serialize() for station in self.polling_station]
        }
        return res