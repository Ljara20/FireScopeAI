from fastapi import APIRouter, HTTPException
router = APIRouter(tags=["preparedness"])
@router.get("/preparedness")
def planned() -> None:
    raise HTTPException(status_code=501, detail="preparedness endpoint planned; stage 1 only")
