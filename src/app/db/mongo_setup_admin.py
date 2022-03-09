from pymongo import MongoClient
import os, sys
from loguru import logger

try: 
	conn = MongoClient(os.environ["DATABASE_ADDRESS"], int(os.environ["DATABASE_PORT"]), serverSelectionTimeoutMS=20000) #host.docker.internal
	conn.server_info()
	logger.info("Successfully connected to Admin MongoDB") 

except Exception as error:
	logger.error(error)
	sys.exit()

# database name: administrator
db = conn.administrator 

# Created or Switched to collection names: offers
collection = db.offers

# Collection for: stakeholder
stakeholder_col = db.stakeholder

# Collection for: verification
verification_col = db.verification