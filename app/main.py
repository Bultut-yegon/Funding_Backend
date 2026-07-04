# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from app.db.database import Base, engine

# # Import all models so SQLAlchemy registers them before create_all
# from app.models import user, opportunity, recommendation, notification
# from app.models import profile as profile_model

# # Import routers
# from app.api import auth
# from app.api import opportunities
# from app.api import recommendations
# from app.api import notifications
# from app.api import profile as profile_router
# from app.services.scheduler import start_scheduler

# Base.metadata.create_all(bind=engine)

# app = FastAPI(title="Funding Platform API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(opportunities.router, prefix="/api/opportunities", tags=["opportunities"])
# app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
# app.include_router(profile_router.router, prefix="/api/profile", tags=["profile"])
# app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])

# @app.get("/")
# def root():
#     return {"message": "Funding Platform API is running"}

# @app.on_event("startup")
# def on_startup():
#     start_scheduler()


from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.models import user, opportunity, recommendation, notification
from app.models import profile as profile_model
from app.api import auth
from app.api import opportunities
from app.api import recommendations
from app.api import notifications
from app.api import profile as profile_router
from app.services.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown (add cleanup here if needed later)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Funding Platform API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", 
                   "https://funding-frontend-orcin.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["opportunities"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(profile_router.router, prefix="/api/profile", tags=["profile"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])

@app.get("/")
def root():
    return {"message": "Funding Platform API is running well"}