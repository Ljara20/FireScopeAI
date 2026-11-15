from fastapi import APIRouter, HTTPException
router = APIRouter(tags=["regions"])
@router.get("/regions")
def planned() -> None:
    raise HTTPException(status_code=501, detail="regions endpoint planned; stage 1 only")
