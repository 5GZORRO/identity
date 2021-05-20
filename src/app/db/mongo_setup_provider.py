from pymongo import MongoClient
import os, sys

try: 
	conn = MongoClient(os.environ["DATABASE_ADDRESS"], int(os.environ["DATABASE_PORT"])) #host.docker.internal, 27017 
	print("Connected successfully to MongoDB") 
except: 
	print("Could not connect to MongoDB")
	sys.exit() 

# database name: provider
db = conn.provider 

# Created or Switched to collection names: offers
collection = db.offers

# Collection for: stakeholder
stakeholder_col = db.stakeholder