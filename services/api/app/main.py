from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.distributors import router as distributor_router
from app.db.session import SessionLocal
from app.api.v1.leads import router as lead_router


app = FastAPI(
    title="Global Moringa Distributor Intelligence Platform",
    version="0.1.0",
)


app.include_router(
    distributor_router,
    prefix="/api/v1",
)

app.include_router(
    lead_router,
    prefix="/api/v1",
)

app.include_router(
    dashboard_router,
    prefix="/api/v1",
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Global Moringa Distributor Intelligence Platform"
    }


@app.get("/health")
def health():
    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }

    finally:
        db.close()
