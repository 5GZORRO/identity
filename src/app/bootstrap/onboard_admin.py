from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
import json, os, time, threading, uuid, random, string, copy
from loguru import logger

from app.db import mongo_setup_provider
from app.issuer.classes import State
from app.holder import utils

def onboard_administrator():
    # Check if cred alreafy exists in DB
    try:
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"stakeholderClaim.stakeholderRoles.0.role": "Administrator"})
        if subscriber is None:
            # Onboard Admin
            admin_cred = {
                "stakeholderClaim": {
                    "governanceBoardDID": "governance:DID",
                    "stakeholderRoles": [
                        {
                            "role": "Administrator",
                            "assets": ["Edge", "Cloud", "Spectrum", "RadioAccessNetwork", "VirtualNetworkFunction", "NetworkSlice", "NetworkService"]
                        }
                    ],
                    "stakeholderProfile": {
                        "name": "Operator-a",
                        "ledgerIdentity": "CN=OperatorA,OU=DLT,O=DLT,L=London,C=GB",
                        "address": "Operator-a address",
                        "notificationMethod": {
                            "notificationType": "EMAIL",
                            "distributionList": "Operator-a@mail.com"
                        }
                    },
                    "stakeholderDID": ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=22))
                },
                "timestamp": str(int(time.time())),
                "state": State.stakeholder_issue,
                "handler_url": os.environ["ADMIN_CATALOGUE_URL"],
                "id_token": str(uuid.uuid4())
            }
            object_to_catalogue = copy.deepcopy(admin_cred)
            
            mongo_setup_provider.stakeholder_col.insert_one(admin_cred)

            # SEND TO ADMIN CATALOGUE
            worker = threading.Thread(target = utils.send_to_holder, args=(object_to_catalogue["handler_url"], object_to_catalogue,), daemon=True)
            worker.start()

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to verify Admin Credential")