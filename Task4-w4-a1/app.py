import os
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import httpx

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_KEY not set in environment!")
else:
    print("Server running and connected to Supabase")

# FastAPI App Instance with Custom Title and Description
app = FastAPI(
    title="Auth - Login & Protect API",
    description="Secure RESTful API utilizing Supabase Auth as Identity Provider with JWT Bearer protection and Swagger UI.",
    version="1.0.0"
)

# HTTPBearer Security Scheme for Swagger UI /docs
security = HTTPBearer(auto_error=False)


# ================= Pydantic Schemas =================
class SignupRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password (min 6 chars)")

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


# ================= Custom Exception Handlers =================
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Ensure error response format matches assignment specs (e.g. {"error": "..."})"""
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {"error": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=content)


# ================= Helper Functions for Supabase REST API =================
def get_supabase_headers(token: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# ================= Middleware / Dependency Guard =================
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Reusable FastAPI Dependency for Stage 4 Token Verification Guard.
    Extracts Bearer JWT token from Authorization header and verifies it via Supabase Auth API.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"}
        )
    
    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"}
        )
    
    try:
        # Call Supabase Auth REST Endpoint /auth/v1/user
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers=get_supabase_headers(token)
            )
            
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"error": "Invalid or expired token"}
                )
            
            user_data = resp.json()
            return {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "created_at": user_data.get("created_at"),
                "user_metadata": user_data.get("user_metadata", {}),
                "raw_token": token
            }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"}
        )


# ================= Public Endpoints =================
@app.get("/public/info", tags=["Public"])
async def public_info():
    """Unprotected public endpoint."""
    return {"message": "Welcome stranger! This info is public."}


# ================= Auth Endpoints =================
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def signup(payload: SignupRequest):
    """
    Stage 1: Register a new user account via Supabase Auth.
    Returns 201 Created on success, 400 Bad Request on input/validation error.
    """
    email = payload.email.strip()
    password = payload.password.strip()

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Email and password are required"}
        )
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/auth/v1/signup",
                headers=get_supabase_headers(),
                json={"email": email, "password": password}
            )
            
            if resp.status_code not in (200, 201):
                err_data = resp.json()
                err_msg = err_data.get("msg") or err_data.get("error_description") or err_data.get("message") or "Registration failed"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": err_msg}
                )
            
            data = resp.json()
            user_obj = data.get("user") or data
            return {
                "message": "User registered successfully",
                "user": {
                    "id": user_obj.get("id"),
                    "email": user_obj.get("email"),
                    "created_at": user_obj.get("created_at")
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Registration failed: {str(e)}"}
        )


@app.post("/auth/login", tags=["Auth"])
async def login(payload: LoginRequest):
    """
    Stage 1: Authenticate user & return JWT Access Token and Refresh Token.
    Returns 200 OK on success, 400 on empty fields, 401 on invalid credentials.
    """
    email = payload.email.strip()
    password = payload.password.strip()

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Email and password are required"}
        )
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
                headers=get_supabase_headers(),
                json={"email": email, "password": password}
            )
            
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"error": "Invalid login credentials"}
                )
            
            data = resp.json()
            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "token_type": "bearer",
                "user": {
                    "id": data.get("user", {}).get("id"),
                    "email": data.get("user", {}).get("email")
                }
            }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"}
        )


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["Auth"])
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Stage 4: Terminate the user session using Bearer Token.
    Returns 204 No Content upon successful logout.
    """
    token = current_user.get("raw_token")
    if token:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{SUPABASE_URL}/auth/v1/logout",
                    headers=get_supabase_headers(token)
                )
        except Exception:
            pass
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ================= Protected Endpoints =================
@app.get("/protected/profile", tags=["Protected"])
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Stage 2, 3 & 4: Read private user profile metadata verified via Bearer JWT.
    """
    return {
        "user_id": current_user["id"],
        "email": current_user["email"],
        "created_at": current_user["created_at"],
        "metadata": current_user["user_metadata"]
    }


@app.get("/protected/dashboard", tags=["Protected"])
async def get_dashboard(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Stage 4 Checkpoint: Second protected route proving reusable middleware protection.
    """
    return {
        "message": "Welcome to your protected dashboard!",
        "user_id": current_user["id"],
        "status": "authenticated"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)
