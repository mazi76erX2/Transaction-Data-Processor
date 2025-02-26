import uvicorn
from app import app

if __name__ == "__main__":
    # Run the FastAPI app using Uvicorn on host 0.0
    uvicorn.run(app, host="0.0.0.0", port=8000)
