from pymongo import MongoClient
import os, sys

try: 
	conn = MongoClient(os.environ["DATABASE_ADDRESS"], 27017) #host.docker.internal
	print("Connected successfully to MongoDB") 
except: 
	print("Could not connect to MongoDB")
	sys.exit() 

# database name: administrator
db = conn.administrator 

# Created or Switched to collection names: offers
collection = db.offers

# Collection for: stakeholder
stakeholder_col = db.stakeholder

# Collection for: verification
verification_col = db.verification