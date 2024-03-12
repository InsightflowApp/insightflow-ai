"""
For connecting to the MongoDB database with PyMongo.

"""

import os
from dotenv import load_dotenv

from pymongo import MongoClient
import pymongo as pm

load_dotenv()

USER = "Insightflow-ai"
DB = "Insightflow"
MONGO_ID = "_id"
client = None

def connect_db():
  global client

  if client is None:
    password = os.getenv("MONGODB_PASSWORD", "")
    CONNECTION_STRING = f"mongodb+srv://{USER}:{password}@insightflow0.bn2saqf.mongodb.net/?retryWrites=true&w=majority&appName=Insightflow0"
    client = MongoClient(CONNECTION_STRING)


def insert_one(collection, doc, db=DB):
  """
  Insert a single doc into collection.
  """
  try:
    result = client[db][collection].insert_one(doc)
    return result.inserted_id  # Return the ID of the inserted document
  except pm.PyMongoError as e:
    pm.logging.error(f"Error inserting doc into {db}.{collection}: {e}")
    return None


def fetch_one(collection, filt, db=DB):
  """
  Find with a filter and return on the first doc found.
  """
  for doc in client[db][collection].find(filt):
    if MONGO_ID in doc:
      # Convert mongo ID to a string so it works as JSON
      doc[MONGO_ID] = str(doc[MONGO_ID])
    return doc


def del_one(collection, filt, db=DB):
  """
  Find with a filter and return on the first doc found.
  """
  return client[db][collection].delete_one(filt)


def del_all(collection, db=DB):
  """
  Removes all elements in a collection.
  """
  client[db][collection].drop()
  return client[db][collection]


def update_doc(collection, filters, update_dict, db=DB):
  return client[db][collection].update_one(filters, {'$set': update_dict})


def fetch_all(collection, db=DB):
  ret = []
  for doc in client[db][collection].find():
    if '_id' in doc:
      doc['_id'] = str(doc['_id'])
    ret.append(doc)
  return ret


def fetch_all_with_filter(collection, filt={}, db=DB):
  ret = []
  for doc in client[db][collection].find(filter=filt):
    # Convert ObjectId fields to string
    if '_id' in doc:
      doc['_id'] = str(doc['_id'])
    ret.append(doc)
  return ret


def fetch_all_as_dict(key, collection, db=DB):
  ret = {}
  for doc in client[db][collection].find():
    del doc[MONGO_ID]
    temp = doc[key]
    ret[temp] = doc
  return ret



# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":   

  # Get the database
  connect_db()
  doc = fetch_one('User', {"username": "oliveliuu"})

  if doc is not None:
    print(doc['username'])
  else:
    print('something went wrong')
