from fastapi import FastAPI, Depends, HTTPException
from .dependencies import get_client, RedisDependency
from .routers import historical_players, historical_records, players, teams, jobs

app = FastAPI()

app.include_router(historical_players.router, prefix="/api/v1")
app.include_router(historical_records.router, prefix="/api/v1")
app.include_router(players.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")


@app.get(
    "/",
    status_code=200,
    tags=["App"],
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "services": {"api": "healthy", "database": "healthy"},
                    }
                }
            },
        },
        503: {
            "description": "Service Unavailable / Database unreachable",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "unhealthy",
                            "services": {
                                "api": "healthy",
                                "database": "unhealthy",
                                "error": "Connection timed out",
                            },
                        }
                    }
                }
            },
        },
    },
)
async def health_check(redis: RedisDependency, client=Depends(get_client)):
    health_status = {
        "status": "healthy",
        "services": {"api": "healthy", "database": "unknown", "cache": "unknown"},
    }

    try:
        mongo_ping = await client.admin.command("ping")
        redis_ping = await redis.ping()
        if mongo_ping:
            health_status["services"]["database"] = "healthy"
        if redis_ping:
            health_status["services"]["cache"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = "unhealthy"
        health_status["services"]["cache"] = "unhealthy"
        health_status["services"]["error"] = str(e)
        health_status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=health_status)

    return health_status
