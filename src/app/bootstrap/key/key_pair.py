import requests, json, time, sys, os, random, string, binascii
from timeloop import Timeloop
from datetime import timedelta
from loguru import logger
from nacl.public import PrivateKey

tl = Timeloop()

try:
    global did_key
    did_key = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=22))
    logger.info("Operator DID: " + did_key)

except Exception as error:
    logger.error(error)        
    sys.exit()

# Create operator key pair
@tl.job(interval=timedelta(seconds=1800))
def operator_key_pair_create():
    try:
        privKey = PrivateKey.generate()
        pubKey = privKey.public_key
        global priv_key, pub_key
        priv_key = binascii.b2a_base64(bytes(privKey)).decode("utf-8").strip()
        pub_key = binascii.b2a_base64(bytes(pubKey)).decode("utf-8").strip()

    except Exception as error:
        logger.error(error)        
        sys.exit()

tl.start(block=False)