from typing import Optional
from pydantic import BaseModel
from enum import Enum

### State -> Enums ###
class StateQuery(str, Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'

class State(str, Enum):
    license_request = 'Stakeholder License Registration Requested'
    license_issue = 'Stakeholder License Registered'
    license_decline = 'Stakeholder License Declined'

##### License Registry Classes #####
class ReqLicenseCred(BaseModel):
    stakeholderServices: list = []
    id_token: str
    stakeholderDID: str
    licenseDID: str
    timestamp: str
    service_endpoint: str
    agent_service_endpoint: str


class ResolveLicense(BaseModel):
    id_token: str
    license_did: str
    approval: bool