from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
import requests, json, sys, os, time, threading, copy

from loguru import logger

header = {
    'Content-Type': 'application/json'
}

def send_to_holder(url: str, client_response: dict):
    try:    
        logger.info('--- Sending to holder:' + url)
        logger.info(client_response)


        holder_handler_resp = requests.post(url, headers=header, json=client_response, timeout=30)
        sent_body = json.dumps(client_response, indent = 4)
        logger.info("Sent info to Handler: " + url) 
        logger.info(sent_body)

    except Exception as error:
        logger.error(error)
