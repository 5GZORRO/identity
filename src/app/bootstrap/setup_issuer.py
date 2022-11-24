#from fastapi import FastAPI
import requests, json, time, sys, os
from loguru import logger

header = {
    'Content-Type': 'application/json'        
}

def issuer_connection(holder_agent_url):
    #connection_id = "teste"
    global connection_id
    try:
        URL = os.environ["ISSUER_AGENT_URL"]
        logger.info('--- Sending /connections/create-invitation:')

        resp = requests.post(URL+"/connections/create-invitation", headers=header, timeout=30)
        body = resp.json()
        connection_id = body["connection_id"]
        conn_invite = json.dumps(body["invitation"], indent = 4)
        logger.info("Created Connection with id: " + connection_id)
        logger.info("Invitation object:")
        logger.info(conn_invite)

    except Exception as error:
        logger.error(error)
        sys.exit()

    try:
        #URL_holder = os.environ["HOLDER_AGENT_URL"]
        #resp_accept = requests.post(URL_holder+"/connections/receive-invitation", data=conn_invite, headers=header, timeout=30)
        logger.info('--- Sending /connections/receive-invitation:')
        logger.info(conn_invite)

        resp_accept = requests.post(holder_agent_url+"/connections/receive-invitation", data=conn_invite, headers=header, timeout=30)
        body_accept = json.dumps(resp_accept.json(), indent = 4)
        logger.info("Accepted connection invitation:")
        logger.info(body_accept)

    except Exception as error:
        logger.error(error)
        sys.exit()

    time.sleep(10)

    try:
        resp_confirm_active = requests.get(URL+"/connections/"+connection_id, timeout=30)
        body_active = resp_confirm_active.json()
        if body_active["state"] == 'active':
            logger.info("Issuer Connection established successfully")
            
    except Exception as error:
        logger.error(error)
        sys.exit()