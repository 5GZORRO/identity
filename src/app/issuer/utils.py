from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
import requests, json, sys, os, time, threading, copy

from loguru import logger

def update_catalog(url: str):
    try:
        requests.delete(url, timeout=60)
    
    except Exception as error:
        logger.error(error)
