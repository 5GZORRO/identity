from typing import Optional
from pydantic import BaseModel
from enum import Enum

### State -> Enums ###
class StateQuery(str, Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'
    revoked = 'revoked'

class State(str, Enum):
    stakeholder_request = 'Stakeholder Registration Requested'
    stakeholder_issue = 'Stakeholder Registered'
    stakeholder_decline = 'Stakeholder Declined'
    did_offer_request = 'Credential Requested'
    did_offer_issue = 'Credential Issued'
    did_offer_decline = 'Credential Declined'


##### Credential Issuing Classes #####
class ReqCred(BaseModel):
    type: str
    credentialSubject: dict
    timestamp: str
    service_endpoint: str
    agent_service_endpoint: str
    #handler_url: str

class IssueCred(BaseModel):
    holder_request_id: str
    type: str
    credentialSubject: dict
    timestamp: str
    service_endpoint: str
    #handler_url: str

class RevokeCred(BaseModel):
    cred_exchange_id: str

class ResolveOffer(BaseModel):
    id: str
    approval: bool


##### Stakeholder Registry Classes #####
class ReqStakeCred(BaseModel):
    stakeholderClaim: dict
    timestamp: str
    service_endpoint: str
    agent_service_endpoint: str
    handler_url: str

class IssueStakeCred(BaseModel):
    holder_request_id: str
    stakeholderClaim: dict
    timestamp: str
    service_endpoint: str

class ResolveStake(BaseModel):
    stakeholder_did: str
    approval: bool

class RevokeStakeCred(BaseModel):
    id_token: str
    stakeholder_did: str