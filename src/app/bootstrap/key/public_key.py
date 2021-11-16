import requests, json, time, sys, os
from timeloop import Timeloop
from datetime import timedelta
from loguru import logger

# Create public agent key
def public_key_create():
    try:
        holder_url = os.environ["HOLDER_AGENT_URL"]
        resp = requests.post(holder_url+"/wallet/did/create", timeout=30)
        result = resp.json()
        #did = result["result"]["did"]
        global public_verkey
        public_verkey = result["result"]["verkey"]
        logger.info("Public Verification Key: " + str(public_verkey))

    except Exception as error:
        logger.error(error)        
        sys.exit()
