from fastapi import APIRouter

router = APIRouter(
    prefix="/proof_requests",
    tags=["proof_request"]
)

####################### Proof Requests Management #######################
@router.post("/create")
async def create_proof_request():
    return "Awaiting Implementation"

@router.get("/read")
async def read_proof_request():
    return "Awaiting Implementation"

@router.get("/read/credential")
async def read_proof_request_credential():
    return "Awaiting Implementation"

@router.post("/present_proof/send", summary="Present a proof to send to the Administrator")
async def present_proof_to_admin():
    return "Awaiting Implementation"

@router.post("/present_proof/verify")
async def verify_presented_proof_from_provider():
    return "Awaiting Implementation"