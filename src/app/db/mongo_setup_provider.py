from pymongo import MongoClient
import os, sys
from loguru import logger

try: 
	conn = MongoClient(os.environ["DATABASE_ADDRESS"], int(os.environ["DATABASE_PORT"]), serverSelectionTimeoutMS=20000) #host.docker.internal, 27017 
	conn.server_info()
	logger.info("Successfully connected to Holder MongoDB") 

except Exception as error:
	logger.error(error)
	sys.exit()

# database name: provider
db = conn.provider 

# Created or Switched to collection names: offers
collection = db.offers

# Collection for: stakeholder
stakeholder_col = db.stakeholder

# Collection for: license
license_collection = db.licenses

# Collection for: key pair
key_pair_col = db.key_pair