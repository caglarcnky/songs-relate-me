#!/usr/bin/env python3
"""
Simple script to run the FastAPI application with uvicorn
"""
import uvicorn
from app import app

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8020,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    ) 