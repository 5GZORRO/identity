import requests, json, time, sys, os, copy, random, string, binascii, jwt
from timeloop import Timeloop
from datetime import timedelta
from loguru import logger
from nacl.public import PrivateKey

from app.db import mongo_setup_provider

#tl = Timeloop()

# Create operator key pair
#@tl.job(interval=timedelta(seconds=1800))
def operator_key_pair_create():
    try:
        privKey = PrivateKey.generate()
        pubKey = privKey.public_key
        key_pair_res = {
            "DID": ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=22)),
            "public_key": binascii.b2a_base64(bytes(privKey)).decode("utf-8").strip(),
            "private_key": binascii.b2a_base64(bytes(pubKey)).decode("utf-8").strip(),
            "timestamp": str(int(time.time()))
        }
        client_key_res = copy.deepcopy(key_pair_res)
        mongo_setup_provider.key_pair_col.insert_one(key_pair_res)
        return client_key_res

    except Exception as error:
        logger.error(error)        
        sys.exit()

#tl.start(block=False)