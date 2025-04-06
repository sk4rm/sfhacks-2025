#this connects the SF2025 database cluster with the app
import json
import pathlib

import certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_KEY = os.getenv("MONGODB_KEY")

# Create a new client and connect to the server
client = MongoClient(MONGODB_KEY, tlsCAFile=certifi.where(),server_api=ServerApi('1'))

#create database and the collection 
db = client.SF2025
collection = db['test3_data']

# Load JSON data
with open(pathlib.Path(__file__).parent / "database" / "data.json", 'r') as file:
    file_data = json.load(file)

# Update documents in the collection
for document in file_data:
    # Assuming 'id' is the unique identifier for each document
    identifier = document['user_id']
    # This will replace the document with the same id or insert a new one if it doesn't exist
    collection.replace_one({'user_id': identifier}, document, upsert=True)
