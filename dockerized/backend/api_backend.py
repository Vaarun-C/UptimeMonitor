import asyncio
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager
from constants import monitoring_service, db_manager

class EmailRequest(BaseModel):
    email: str

class URLTrackRequest(BaseModel):
    url: HttpUrl
    category: Optional[str] = None

class URLStatusResponse(BaseModel):
    url: str
    uptime_percentage: float
    last_checked: Optional[str]
    category: Optional[str] = None

class LogEntry(BaseModel):
    timestamp: str
    status: str
    response_time_ms: int
    http_code: int

class UserRegistration(BaseModel):
    username: str
    password: str
    email: str

class CategoryUpdate(BaseModel):
    category: str

security = HTTPBasic()

# Lifespan manager to handle startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background monitoring
    monitoring_task = asyncio.create_task(monitoring_service.start_monitoring())
    yield
    # Shutdown: Stop monitoring
    await monitoring_service.stop_monitoring()
    monitoring_task.cancel()

app = FastAPI(
    title="Uptime Monitoring API",
    description="API for tracking website uptime and performance",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    user_id, email = db_manager.verify_user(credentials.username, credentials.password)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return {
        "user_id": user_id,
        "username": credentials.username,
        "email": email
    }

@app.post("/register")
async def register_user(user_data: UserRegistration):
    user_id = db_manager.create_user(user_data.username, user_data.password, user_data.email)
    if not user_id:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    return {
        "message": "User created successfully",
        "user_id": user_id,
        "username": user_data.username,
        "email": user_data.email
    }

@app.post("/track")
async def track_url(
    request: URLTrackRequest, 
    current_user: dict = Depends(get_current_user)
):
    url_str = str(request.url)
    
    if db_manager.add_url(url_str, current_user["user_id"], request.category):
        # Trigger immediate check for the new URL
        try:
            await monitoring_service.check_single_url_immediately(url_str)
        except Exception as e:
            print(f"Warning: Could not perform immediate check: {e}")
        
        return {"message": f"Successfully added {url_str} to monitoring"}
    else:
        raise HTTPException(status_code=400, detail="URL is already being monitored by you")

@app.get("/status/{url:path}")
async def get_url_status(
    url: str, 
    current_user: dict = Depends(get_current_user)
):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    if not db_manager.user_owns_url(url, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="URL not found")
    
    status = db_manager.get_url_status(url, current_user["user_id"])
    if status is None:
        raise HTTPException(status_code=404, detail="URL not found")
    
    result = {
        "url": status["url"],
        "uptime_percentage": status["uptime_percentage"],
        "last_checked": status["last_checked"]
    }
    
    if status.get("category"):
        result["category"] = status["category"]
    
    return result

@app.get("/logs/{url:path}")
async def get_url_logs(
    url: str, 
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    if not db_manager.user_owns_url(url, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="URL not found")
    
    logs = db_manager.get_url_logs(url, current_user["user_id"], limit)
    return logs

@app.get("/my-urls")
async def get_my_urls(current_user: dict = Depends(get_current_user)):
    urls = db_manager.get_user_urls(current_user["user_id"])
    return {
        "user": current_user["username"],
        "url_count": len(urls),
        "urls": urls
    }

@app.delete("/urls/{url:path}")
async def remove_url(
    url: str,
    current_user: dict = Depends(get_current_user)
):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    if not db_manager.user_owns_url(url, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="URL not found")
    
    if db_manager.remove_url(url, current_user["user_id"]):
        return {"message": f"Successfully removed {url} from monitoring"}
    else:
        raise HTTPException(status_code=500, detail="Error removing URL")

@app.put("/urls/{url:path}/category")
async def update_url_category(
    url: str,
    category_data: CategoryUpdate,
    current_user: dict = Depends(get_current_user)
):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    if not db_manager.user_owns_url(url, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="URL not found")
    
    if db_manager.update_url_category(url, current_user["user_id"], category_data.category):
        return {"message": f"Category updated for {url}"}
    else:
        raise HTTPException(status_code=500, detail="Error updating category")

@app.post("/check-all")
async def check_my_urls_now(current_user: dict = Depends(get_current_user)):
    try:
        user_urls = db_manager.get_user_urls(current_user["user_id"])
        for url_data in user_urls:
            await monitoring_service.check_single_url_immediately(url_data["url"])
        
        return {"message": f"All {len(user_urls)} URLs checked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking URLs: {str(e)}")

@app.post("/check/{url:path}")
async def check_url_now(
    url: str,
    current_user: dict = Depends(get_current_user)
):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    if not db_manager.user_owns_url(url, current_user["user_id"]):
        raise HTTPException(status_code=404, detail="URL not found")
    
    try:
        await monitoring_service.check_single_url_immediately(url)
        return {"message": f"URL {url} checked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking URL: {str(e)}")

@app.get("/me")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"]
    }

@app.post("/send-report")
async def send_my_report(
    current_user: dict = Depends(get_current_user)
):
    try:
        success = await monitoring_service.send_user_notification(
            current_user["user_id"], 
            current_user["email"]
        )
        
        if success:
            return {"message": f"Report sent successfully to {current_user['email']}"}
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to send report. Check email configuration."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending report: {str(e)}")