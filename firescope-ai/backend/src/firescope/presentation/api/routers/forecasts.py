from fastapi import APIRouter, HTTPException
router = APIRouter(tags=["forecasts"])
@router.get("/forecasts")
def planned() -> None:
    raise HTTPException(status_code=501, detail="forecasts endpoint planned; stage 1 only")
