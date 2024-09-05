from typing import Optional
import requests
# import pyrebase
# import firebase_admin
import json
#from firebase_admin import credentials, auth
from fastapi import  FastAPI, HTTPException, Depends,File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import os
import httpx
#from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}
