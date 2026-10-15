import os
import hmac
from fastapi import APIRouter, Header, HTTPException, status, Depends
from ..jobs.daily_sync import run_daily_sync
from ..jobs.weekly_sync import run_weekly_sync

router = APIRouter(prefix="/jobs", tags=["Cron Jobs"])

SECRET = os.getenv("CRON_SECRET")


def verify_cron_secret(authorization: str = Header(None)):
    if not SECRET:
        raise HTTPException(
            status_code=500, detail={"message": "CRON_SECRET is not configured."}
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"message": "Missing or malformed Authorization header."},
        )
    token = authorization.split("Bearer ", 1)[1]
    if not hmac.compare_digest(token, SECRET):
        raise HTTPException(status_code=403, detail={"message": "Invalid token."})


@router.post("/daily-sync", status_code=200)
async def dayly_sync_job(auth: None = Depends(verify_cron_secret)):
    res = await run_daily_sync()
    return {"message": "Daily job successfully executed.", "data": res}


@router.post("/weekly-sync", status_code=200)
async def weekly_sync_job(auth: None = Depends(verify_cron_secret)):
    res = await run_weekly_sync()
    return {"message": "Weeky job successfully executed.", "data": res}
