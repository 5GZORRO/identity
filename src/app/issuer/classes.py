from typing import Optional
from pydantic import BaseModel

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


##### Stakeholder Registry Classes #####
class ReqStakeCred(BaseModel):
    stakeholderClaim: dict
    timestamp: str
    service_endpoint: str
    agent_service_endpoint: str

class IssueStakeCred(BaseModel):
    holder_request_id: str
    stakeholderClaim: dict
    timestamp: str
    service_endpoint: str