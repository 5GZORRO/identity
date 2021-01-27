'''
from pymongo import MongoClient

try: 
	conn = MongoClient('host.docker.internal', 27017) #src_mongodb_container_1
	print("Connected successfully to MongoDB") 
except: 
	print("Could not connect to MongoDB") 

# database name: config
db = conn.config 

# Created or Switched to collection names: offers
collection = db.offers

#data={
#    "teste":"ressd1"
#}

#rec_id = collection.insert_one(data)
#print(rec_id.inserted_id)
'''
