from fastapi import APIRouter
router = APIRouter()

@router.get("")
async def list_resource():
    return {"data": [], "message": "research stub - implemented in later phases"}
