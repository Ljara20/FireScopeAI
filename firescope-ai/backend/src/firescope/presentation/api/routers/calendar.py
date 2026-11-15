from fastapi import APIRouter, HTTPException
router = APIRouter(tags=["calendar"])
@router.get("/calendar")
def planned() -> None:
    raise HTTPException(status_code=501, detail="calendar endpoint planned; stage 1 only")
