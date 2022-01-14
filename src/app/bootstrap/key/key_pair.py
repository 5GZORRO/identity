import requests, json, time, sys, os, binascii
from timeloop import Timeloop
from datetime import timedelta
from loguru import logger
from nacl.public import PrivateKey

tl = Timeloop()

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