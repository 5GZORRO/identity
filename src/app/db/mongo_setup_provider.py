from pymongo import MongoClient
import os, sys

try: 
	conn = MongoClient(os.environ["DATABASE_ADDRESS"], 27017) #host.docker.internal
	print("Connected successfully to MongoDB") 
except: 
	print("Could not connect to MongoDB")
	sys.exit() 

# database name: provider
db = conn.provider 

# Created or Switched to collection names: offers
collection = db.offers