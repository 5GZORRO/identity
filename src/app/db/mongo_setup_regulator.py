from pymongo import MongoClient
import os, sys
from loguru import logger

try: 
	conn = MongoClient(os.environ["DATABASE_ADDRESS"], int(os.environ["DATABASE_PORT"]), serverSelectionTimeoutMS=20000) #host.docker.internal
	conn.server_info()
	logger.info("Successfully connected to Regulator MongoDB") 

except Exception as error:
	logger.error(error)
	sys.exit()

# database name: regulator
db = conn.regulator 

# Created or Switched to collection names: licenses
license_collection = db.licenses