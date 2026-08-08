from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import SessionLocal

app = FastAPI(
    title="Global Moringa Distributor Intelligence Platform",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Global Lead Intelligence Platform"
    }


@app.get("/health")
def health():
    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

    finally:
        db.close()
