import os
import logging
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from jose.exceptions import JWTError, ExpiredSignatureError
from dotenv import load_dotenv
from app.database import engine, Base
from app.router import auth, expense, users, category, budget
from app.rate_limiter import rate_limiter
from app.security_logger import log_rate_limit_violation

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expense Tracker API",
    description="A comprehensive expense tracking system with JWT authentication",
    version="1.0.0"
)

# origins = os.getenv("CORS_ORIGINS", "http://localhost:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    
    auth_endpoints = ["/auth/login", "/auth/register", "/users/create"]
    
    if request.url.path in auth_endpoints:
        key = f"rate_limit:auth:{client_ip}"
        max_requests = 5
        window_seconds = 900
    else:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            user_id = f"user_{client_ip}"
        else:
            user_id = f"anon_{client_ip}"
        key = f"rate_limit:api:{user_id}"
        max_requests = 100
        window_seconds = 60
    
    is_limited, remaining = rate_limiter.is_rate_limited(key, max_requests, window_seconds)
    
    if is_limited:
        ttl = rate_limiter.get_ttl(key)
        log_rate_limit_violation(client_ip, request.url.path, max_requests, window_seconds)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests"},
            headers={
                "Retry-After": str(ttl),
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(ttl)
            }
        )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"] if loc != "body"),
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Validation error", "errors": errors}
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logging.error(f"Integrity error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "A conflict occurred. The resource may already exist."}
    )


@app.exception_handler(OperationalError)
async def database_error_handler(request: Request, exc: OperationalError):
    logging.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Service temporarily unavailable. Please try again later."}
    )


@app.exception_handler(JWTError)
async def jwt_error_handler(request: Request, exc: JWTError):
    logging.error(f"JWT error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid authentication credentials"},
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(ExpiredSignatureError)
async def expired_token_handler(request: Request, exc: ExpiredSignatureError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Token has expired"},
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logging.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"}
    )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(category.router)
app.include_router(budget.router)
app.include_router(expense.router)


@app.get("/")
def root():
    return {"message": "AI Expense Tracker API is running"}
