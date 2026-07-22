from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db.database import Base, engine
from app.models import user, opportunity, recommendation, notification
from app.models import profile as profile_model
from app.api import auth
from app.api import opportunities
from app.api import recommendations
from app.api import notifications
from app.api import profile as profile_router
from app.services.scheduler import start_scheduler
from app.models import bookmark as bookmark_model
from app.api import bookmarks
from app.api import proposals
from app.api import admin
from app.api import predictor
from app.models import analytics as analytics_model
from app.api import analytics
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://funding-frontend-orcin.vercel.app",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Funding Platform API", lifespan=lifespan)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    )

# Handle preflight OPTIONS requests manually
@app.middleware("http")
async def cors_handler(request: Request, call_next):
    origin = request.headers.get("origin", "")

    if request.method == "OPTIONS":
        response = JSONResponse(content={}, status_code=200)
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
        response.headers["Access-Control-Max-Age"] = "600"
        return response

    response = await call_next(request)

    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response

app.add_middleware(
    SlowAPIMiddleware,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["opportunities"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])
app.include_router(profile_router.router, prefix="/api/profile", tags=["profile"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(proposals.router, prefix="/api/proposals", tags=["proposals"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(predictor.router, prefix="/api/predict", tags=["predictor"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.get("/")
def root():
    return {"message": "Funding Platform API is running"}