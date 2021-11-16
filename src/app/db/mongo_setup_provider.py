from pymongo import MongoClient
import os, sys
from loguru import logger

try: 
	conn = MongoClient(os.environ["DATABASE_ADDRESS"], int(os.environ["DATABASE_PORT"])) #host.docker.internal, 27017 
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