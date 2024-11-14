from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional
import httpx
import uvicorn
from pathlib import Path
import os
import json
import logging
import certifi
# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    API_BASE_URL: str = "https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1"
    API_TOKEN: str = "19TPS2Z-6004AGY-K968P7Q-2BW0QCD"
    TIMEOUT_SECONDS: int = 30  # Added timeout setting
    
    class Config:
        env_file = ".env"



class APIClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.API_BASE_URL
        self.timeout = settings.TIMEOUT_SECONDS
        self.headers = {
            "Authorization": f"Bearer {settings.API_TOKEN}",
            "accept": "application/json"
        }
        
    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Any:
        timeout = httpx.Timeout(timeout=self.timeout)
        
        try:
            async with httpx.AsyncClient(timeout=timeout,verify=False) as client:
                url = f"{self.base_url}{endpoint}"
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    **kwargs
                )
                
                if response.status_code not in (200, 201):
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=response.text
                    )
                    
                return response.json() if response.text else None
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Request timed out. Please try again later."
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Network error occurred: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred: {str(e)}"
            )


app = FastAPI(title="Workspace Management API")
settings = Settings()
api_client = APIClient(settings)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=["*"],
    max_age=36000
)


class WorkspaceResponse(BaseModel):
    message: str
class CreateWorkspace(BaseModel):
    space_name: str
    
# Workspace operations
@app.post('/create_workspace', response_model=WorkspaceResponse)
async def create_workspace(request: CreateWorkspace):
    data = {"name": request.space_name}
    await api_client.make_request(
        "POST", 
        "/workspace/new",
        json=data
    )
    return WorkspaceResponse(message="Workspace created successfully")

@app.get('/workspaces')
async def get_workspaces():
    return await api_client.make_request("GET", "/workspaces")

@app.get('/workspace/{slug}')
async def get_workspace(slug: str):
    return await api_client.make_request("GET", f"/workspace/{slug}")

@app.delete('/workspace/{slug}')
async def delete_workspace(slug: str):
    await api_client.make_request("DELETE", f"/workspace/{slug}")
    return {"message": "Workspace deleted successfully"}

@app.get('/workspace/{slug}/chats')
async def get_workspace_chats(slug: str):
    return await api_client.make_request("GET", f"/workspace/{slug}/chats")

# Q&A operations
class QueryRequest(BaseModel):
    query: str
    slug: str

class QueryResponse(BaseModel):
    textResponse: str
    citations: List[str]

@app.post('/qa', response_model=QueryResponse)
async def query_and_response(request: QueryRequest):
    try:
        data = {
            "message": request.query,
            "mode": "query",
            "sessionId": "identifier-to-partition-chats-by-external-id"
        }
        
        response = await api_client.make_request(
            "POST",
            f"/workspace/{request.slug}/chat",
            json=data
        )
        
        texts = [source["text"] for source in response["sources"]]
        return QueryResponse(
            textResponse=response["textResponse"],
            citations=texts
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )

class QueryRequestThread(BaseModel):
    query: str
    slug: str
    threadSlug: str
class QueryResponse(BaseModel):
    textResponse: str
    citations: List[str]
@app.post('/qa_thread', response_model=QueryResponse)
async def query_and_response_thread(request: QueryRequestThread):
    try:
        logger.info("hello")
        data = {
            "message": request.query,
            "mode": "query",
            #"sessionId": "identifier-to-partition-chats-by-external-id"
            "userId": 1
        }
        
        response = await api_client.make_request(
            "POST",
            f"/workspace/{request.slug}/thread/{request.threadSlug}/chat",
            json=data
        )
        logger.info(f"Making request to URL: /workspace/{request.slug}/thread/{request.threadSlug}/chat")
        texts = [source["text"] for source in response["sources"]]
        return QueryResponse(
            textResponse=response["textResponse"],
            citations=texts
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )

# Document operations
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        temp_path = Path(file.filename)
        temp_path.write_bytes(content)

        files = {'file': (file.filename, content, file.content_type)}
        response = await api_client.make_request(
            "POST",
            "/document/upload",
            files=files
        )

        # Cleanup temporary file
        os.remove(temp_path)
        return {"message": "File uploaded successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"File upload failed: {str(e)}"
        )


class QueryUpdateEmbed(BaseModel):
    slug:str
    filename:str
@app.post("/workspace/{slug}/update-embeddings")
async def update_workspace_embeddings(request: QueryUpdateEmbed):
    try:

        logger.info(f"Starting embedding update for workspace: {request.slug}, file: {request.filename}")

        # Get document list
        docs = await api_client.make_request("GET", "/documents")
        
        if not docs or 'localFiles' not in docs:
            raise HTTPException(status_code=404, detail="No documents found")
            
        # Find the matching file
        file_name = None
        items = docs.get('localFiles', {}).get('items', [])
        logger.debug(f"Retrieved items from documents: {items}")


        if items and len(items) > 0:
            for item in items[0].get('items', []):
                if request.filename in item.get('name', ''):
                    file_name = item['name']
                    break
        logger.info(f"Found matching file: {file_name}")

        if not file_name:
            raise HTTPException(
                status_code=404, 
                detail=f"File {request.filename} not found in documents"
            )
            
        data = {
            "adds": [f"custom-documents/{file_name}"],
            "deletes": []
        }
        
        await api_client.make_request(
            "POST",
            f"/workspace/{request.slug}/update-embeddings",
            json=data
        )
        
        return {"message": "Embeddings updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update embeddings: {str(e)}"
        )

@app.get("/documents", response_model=List[str])
async def list_documents():
    response = await api_client.make_request("GET", "/documents")
    doc_list = response['localFiles']['items'][0]
    return [item['name'] for item in doc_list['items']]

class NewThreadResponse(BaseModel):
    slug_thread: str

class NewThreadRequest(BaseModel):
    slug: str

@app.post('/create-thread', response_model=NewThreadResponse)
async def new_thread_workspace(request: NewThreadRequest):
    try:
        response = await api_client.make_request(
            method="POST",
            endpoint=f"/workspace/{request.slug}/thread/new"
        )
        
        if not response or 'thread' not in response or 'slug' not in response['thread']:
            raise HTTPException(
                status_code=500,
                detail="Invalid response from server: missing slug"
            )
            
        return NewThreadResponse(
            slug_thread=response['thread']['slug']
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create new thread: {str(e)}"
        )

# if __name__ == '__main__':
#     uvicorn.run("main:app", host='127.0.0.1', port=8000, reload=True)
