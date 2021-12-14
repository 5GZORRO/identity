from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

### State -> Enums ###
class State(str, Enum):
    stakeholder_request = 'Stakeholder Registration Requested'
    stakeholder_issue = 'Stakeholder Registered'
    stakeholder_decline = 'Stakeholder Declined'
    did_offer_request = 'Credential Requested'
    did_offer_issue = 'Credential Issued'
    did_offer_decline = 'Credential Declined'
    

### Role -> Enums ###
class Type(str, Enum):
    product_offer = 'ProductOffer'
    regulated_product_offer = 'RegulatedProductOffer'
    governance_proposal = 'GovernanceProposal'
    governance_vote = 'GovernanceVote'
    legal_prose_template = 'LegalProseTemplate'
    sla = 'SLA'
    agreement = 'Agreement'

class Offer(BaseModel):
    token: str
    type: Type
    #claims: dict
    claims: list = []
    handler_url: str


### Role -> Enums ###
class Role(str, Enum):
    Regulator = 'Regulator'
    Resource_Provider = 'ResourceProvider'
    Resource_Consumer = 'ResourceConsumer'
    Service_Provider = 'ServiceProvider'
    Service_Consumer = 'ServiceConsumer'
    Administrator = 'Administrator'

### Assets -> Enums ###
class Assets(str, Enum):
    InformationResource = 'InformationResource'
    SpectrumResource = 'SpectrumResource'
    PhysicalResource = 'PhysicalResource'
    NetworkFunction = 'NetworkFunction'

### notificationType -> Enum ###
class NType(str, Enum):
    EMAIL = 'EMAIL'

class SHNotify(BaseModel):
    notificationType: NType
    distributionList: str

class SHRoles(BaseModel):
    #role: str
    role: Role
    assets: List[Assets]
    #assets: str

#class SHServices(BaseModel):
#    type: str
#    endpoint: str

class SHProfile(BaseModel):
    name: str
    ledgerIdentity: str
    address: str
    notificationMethod: SHNotify

class Stakeholder(BaseModel):
    key: str
    governanceBoardDID: str
    stakeholderServices: List = []
    #stakeholderServices: List[SHServices]
    stakeholderRoles: List[SHRoles]
    #stakeholderRoles: SHRoles
    stakeholderProfile: SHProfile
    handler_url: str


#class ReadStakeDID(BaseModel):
#    stakeholderDID: str

class ReadOfferDID(BaseModel):
    token: str
    did_identifier: str