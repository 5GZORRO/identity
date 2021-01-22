from fastapi import APIRouter

#from app.bootstrap import setup_issuer, setup_verifier

router = APIRouter(
    prefix="/did_documents",
    tags=["did_document"]
)

####################### DID Docs Management #######################
@router.post("/create")
async def create_did_document():
    return "Awaiting Implementation"
    #return "ISSUER conn_id: " + setup_issuer.connection_id + "; VERIFIER conn_id: " + setup_verifier.connection_id

@router.get("/read")
async def read_did_document():
    return "Awaiting Implementation"

@router.put("/update")
async def update_did_document():
    return "Awaiting Implementation"