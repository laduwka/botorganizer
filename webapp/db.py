from flask_pymongo import PyMongo
from flask import current_app

mongo = PyMongo()


def get_db():
    return mongo.db[current_app.config['MONGO_AUTH_COLLECTION']]
