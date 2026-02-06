
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings
from app.api.legal import router
from app.services.logger import logger
from fastapi.responses import JSONResponse
from fastapi import HTTPException, status

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for extracting and comparing legal documents",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.UPLOAD_DIR.mkdir(exist_ok=True)


app.include_router(router)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.PROJECT_NAME} API")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR.absolute()}")
    logger.info(f"Allowed file extensions: {settings.ALLOWED_EXTENSIONS}")

@app.get("/")
async def root():
    return {
        "message": "Legal Tabular Review System API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/documents/upload",
            "list_documents": "/api/documents",
            "extract": "/api/documents/{id}/extract",
            "docs": "/api/docs"
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )