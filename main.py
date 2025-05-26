import uvicorn
from api_backend import app

def main():
    print("🔑 Starting API service with API_KEY")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()