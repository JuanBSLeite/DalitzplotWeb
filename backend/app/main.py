from fastapi import FastAPI

from app.api.routes import router as api_router

app = FastAPI(title="Dalitz Web Backend")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Dalitz Web Backend"}
