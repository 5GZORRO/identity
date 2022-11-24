import requests, json, time, sys, os
from timeloop import Timeloop
from datetime import timedelta
from loguru import logger

# Create private agent key
def holder_key_create():
    try:
        holder_url = os.environ["HOLDER_AGENT_URL"]
        logger.info('--- Sending /wallet/did/create (holder-key):')

        resp = requests.post(holder_url+"/wallet/did/create", timeout=30)
        result = resp.json()
        #did = result["result"]["did"]
        global verkey
        verkey = result["result"]["verkey"]
        logger.info("Private Verification Key: " + str(verkey))

    except Exception as error:
        logger.error(error)  
        sys.exit()
