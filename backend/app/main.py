from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.demo import router as demo_router
from app.api.cases import router as cases_router
from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.analytics_export import router as analytics_export_router
from app.api.nm import router as nm_router
from app.api.pharmacy import router as pharmacy_router
from app.db.session import SessionLocal, init_db
from app.services.seed import seed_demo_cases


app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_demo_cases(db)
    finally:
        db.close()


app.include_router(health_router)
app.include_router(demo_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(analytics_export_router, prefix="/api")
app.include_router(nm_router, prefix="/api")
app.include_router(pharmacy_router, prefix="/api")
