from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field
from enum import Enum

### State -> Enums ###
class State(str, Enum):
    stakeholder_request = 'Stakeholder Registration Requested'
    stakeholder_issue = 'Stakeholder Registered'
    stakeholder_decline = 'Stakeholder Declined'
    did_offer_request = 'Credential Requested'
    did_offer_issue = 'Credential Issued'
    did_offer_decline = 'Credential Declined'
    license_request = 'Stakeholder License Registration Requested'
    license_issue = 'Stakeholder License Registered'
    license_decline = 'Stakeholder License Declined'


### Role -> Enums ###
class Role(str, Enum):
    Trader = 'Trader'
    Regulator = 'Regulator'

### Assets -> Enums ###
class Assets(str, Enum):
    Edge = 'Edge'
    Cloud = 'Cloud'
    Spectrum = 'Spectrum'
    RadioAccessNetwork = 'RadioAccessNetwork'
    VirtualNetworkFunction = 'VirtualNetworkFunction'
    NetworkSlice = 'NetworkSlice'
    NetworkService = 'NetworkService'

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
    #assets: List[Assets] = Field(..., min_items=1)
    #claims: dict
    claims: list = []
    handler_url: str


### notificationType -> Enum ###
class NType(str, Enum):
    EMAIL = 'EMAIL'

class SHNotify(BaseModel):
    notificationType: NType
    distributionList: str

class SHRoles(BaseModel):
    #role: str
    role: Role
    assets: List[Assets] = Field(..., min_items=1)
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
    #stakeholderServices: List[SHServices]
    stakeholderRoles: List[SHRoles] = Field(..., min_items=1)
    #stakeholderRoles: SHRoles
    stakeholderProfile: SHProfile
    handler_url: HttpUrl


#class ReadStakeDID(BaseModel):
#    stakeholderDID: str

class ReadOfferDID(BaseModel):
    token: str
    did_identifier: str

class License(BaseModel):
    id_token: str
    stakeholderServices: List = Field(..., min_items=1)