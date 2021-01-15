from fastapi import APIRouter

router = APIRouter(
    prefix="/credentials",
    tags=["credential"]
)

####################### Verifiable Credentials Management #######################
@router.post("/issue")
async def issue_credential():
    return "Awaiting Implementation"

@router.get("/read")
async def read_credential():
    return "Awaiting Implementation"

@router.get("/read/all")
async def read_all_credentials():
    return "Awaiting Implementation"

@router.put("/revoke")
async def revoke_credential():
    return "Awaiting Implementation"

@router.get("/read/revoke")
async def read_revoked_credential():
    return "Awaiting Implementation"

@router.delete("/remove")
async def remove_credential():
    return "Awaiting Implementation"