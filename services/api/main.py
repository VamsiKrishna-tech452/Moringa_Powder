from fastapi import FastAPI

app = FastAPI(
    title="Global Lead Intelligence Platform",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Global Lead Intelligence Platform"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }
