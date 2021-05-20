from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy


# ### Config
app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)

# import views
from . import views