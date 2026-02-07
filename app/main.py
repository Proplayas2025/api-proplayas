from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import os
from core.config import settings
from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.nodes import router as nodes_router
from routes.content import router as content_router
from routes.invitations import router as invitations_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear directorios de storage al iniciar
    storage_dirs = ["profiles", "covers", "docs"]
    for d in storage_dirs:
        Path(settings.UPLOAD_DIR, d).mkdir(parents=True, exist_ok=True)
    yield

docs_url = f"{settings.API_V1_STR}/docs" if settings.API_V1_STR else "/docs"
redoc_url = f"{settings.API_V1_STR}/redoc" if settings.API_V1_STR else "/redoc"
openapi_url = f"{settings.API_V1_STR}/openapi.json" if settings.API_V1_STR else "/openapi.json"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    redirect_slashes=False,
    lifespan=lifespan
)

cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://proplayas.org,https://proplayas.org")
if cors_origins.strip() == "*":
    allow_origins = ["http://localhost:3000"]
else:
    allow_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": 422,
            "message": "Validation error",
            "data": None,
            "errors": exc.errors()
        }
    )

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(nodes_router, prefix=settings.API_V1_STR)
app.include_router(content_router, prefix=settings.API_V1_STR)
app.include_router(invitations_router, prefix=settings.API_V1_STR)

# Servir archivos estáticos (uploads: fotos de perfil, covers, docs)
# Accesible en: http://localhost:8080/storage/uploads/profiles/filename.jpg
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

@app.get("/")
async def root():
    return {"message": "Proplayas API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
