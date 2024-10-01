from typing import Optional
import json
from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pathlib import Path
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=["*"],
    max_age=36000
)

BASE_URL = "https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1"
API_KEY = "19TPS2Z-6004AGY-K968P7Q-2BW0QCD"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "accept": "application/json"
}

async def make_request(method, url, **kwargs):
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post('/create_workspace')
async def new_workspace(space_name: str):
    data = {"name": space_name}
    return await make_request("POST", f"{BASE_URL}/workspace/new", json=data)

@app.get('/workspaces_present')
async def get_workspaces():
    return await make_request("GET", f"{BASE_URL}/workspaces")

@app.get('/workspace/{slug}')
async def get_workspace(slug: str):
    return await make_request("GET", f"{BASE_URL}/workspace/{slug}")

@app.delete('/delete/workspace/{slug}')
async def delete_workspace(slug: str):
    return await make_request("DELETE", f"{BASE_URL}/workspace/{slug}")

@app.get('/workspace/{slug}/chats')
async def get_workspace_chat(slug: str):
    return await make_request("GET", f"{BASE_URL}/workspace/{slug}/chats")

@app.post('/QnA')
async def query_and_response(request: Request):
    body = await request.json()
    query = body.get('query')
    slug = body.get('slug')
    
    data = {
        "message": query,
        "mode": "query",
        "sessionId": "identifier-to-partition-chats-by-external-id"
    }
    
    response = await make_request("POST", f"{BASE_URL}/workspace/{slug}/chat", json=data)
    
    result = {
        'textResponse': response.get('textResponse', 'No response text found'),
        'Citations': [item['text'] for item in response.get('sources', [])] if 'sources' in response else 'No sources available'
    }
    return result

@app.post("/upload")
async def upload_document(file: UploadFile):
    content = await file.read()
    Path(file.filename).write_bytes(content)
    
    files = {'file': (file.filename, content, file.content_type)}
    response = await make_request("POST", f"{BASE_URL}/document/upload", files=files)
    
    os.remove(file.filename)
    return {"message": file.filename}

@app.post("/update_embeddings")
async def update_workspace_embeddings(request: Request):
    body = await request.json()
    filename = body.get('filename')
    slug = body.get('slug')
    
    docs = await make_request("GET", f"{BASE_URL}/documents")
    fileName = next((item['name'] for item in docs['localFiles']['items'][0]['items'] if filename in item['name']), None)
    
    if not fileName:
        raise HTTPException(status_code=404, detail="File not found")
    
    data = {
        "adds": [f"custom-documents/{fileName}"],
        "deletes": [" "]
    }
    
    return await make_request("POST", f"{BASE_URL}/workspace/{slug}/update-embeddings", json=data)

@app.get("/docs_list")
async def list_of_docs():
    docs = await make_request("GET", f"{BASE_URL}/documents")
    return [item['name'] for item in docs['localFiles']['items'][0]['items']]

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


# from typing import Optional
# import requests
# # import pyrebase
# # import firebase_admin
# import json
# #from firebase_admin import credentials, auth
# from fastapi import  FastAPI, HTTPException, Depends,File, UploadFile
# from fastapi.responses import JSONResponse
# from fastapi.requests import Request
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn
# from pathlib import Path
# import os
# import httpx
# #from fastapi import FastAPI

# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=['*'],
#     allow_credentials=True,
#     allow_methods=['*'],
#     allow_headers=['*'],
#     expose_headers=["*"],
#     max_age=36000
# )

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}

# @app.get('/hello')
# async def hello():
#     return {"message": "Hello World"}
    
# # @app.get("/items/{item_id}")
# # def read_item(item_id: int, q: Optional[str] = None):
# #     return {"item_id": item_id, "q": q}
# @app.post('/create_workspace')
# async def new_workspace(space_name):
#     url=f'https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1/workspace/new'
    
#     headers= {
#         "Authorization": "Bearer 19TPS2Z-6004AGY-K968P7Q-2BW0QCD",
#         "accept": "application/json"
#         }
    
#     data={
#         "name":f"{space_name}"
#     }
#     response = requests.post(url,headers=headers,json=data)
    
#     if response.status_code != 200:
#             raise HTTPException(
#                 status_code=response.status_code,
#                 detail=f"{response.text}",
#             )
#     else:
#         return {"message": "**WorkSpace created successfully**"}

# @app.get('/workspaces_present')
# async def get_workspaces():
#     url='https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1/workspaces'
       
#     headers= {
#         "Authorization": "Bearer 19TPS2Z-6004AGY-K968P7Q-2BW0QCD",
#         "accept": "application/json"
#         }
#     response = requests.get(url,headers=headers)
    
#     if response.status_code != 200:
#             raise HTTPException(
#                 status_code=response.status_code,
#                 detail=f"{response.text}",
#             )
#     else:
#         data=json.loads(response.text)
#         return data


# @app.post('/workspace/slug')
# async def get_workspace(slug:str):
#     url=f'https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1/workspace/{slug}'    
    
       
#     headers= {
#         "Authorization": "Bearer 19TPS2Z-6004AGY-K968P7Q-2BW0QCD",
#         "accept": "application/json"
#         }
    
#     response = requests.get(url,headers=headers)
    
#     if response.status_code != 200:
#             raise HTTPException(
#                 status_code=response.status_code,
#                 detail=f"{response.text}",
#             )
#     else:
#         data=json.loads(response.text)
#         return data

# @app.delete('/delete/workspace')
# async def delete_workspace(slug:str):
#     url = f'https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1/workspace/{slug}'

#     headers = {'accept': '*/*'}
       
#     headers= {
#         "Authorization": "Bearer 19TPS2Z-6004AGY-K968P7Q-2BW0QCD",
#         "accept": '*/*'
#         }

#     # Send a DELETE request to the API endpoint
#     response = requests.delete(url, headers=headers)

#     # Check the response status code
#     if response.status_code == 200:
#         return {'Workspace deleted successfully!'}
#     else:
#         return {f'Error deleting workspace: {response.status_code} - {response.text}'}

# @app.post('/workspace/chats')
# async def get_workspace_chat(slug:str):
#     url=f'https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1/workspace/{slug}/chats'    

#     headers= {
#         "Authorization": "Bearer 19TPS2Z-6004AGY-K968P7Q-2BW0QCD",
#         "accept": "application/json"
#         }
    
#     response = requests.get(url,headers=headers)
    
#     if response.status_code == 200:
#             # raise HTTPException(
#             #     status_code=response.status_code,
#             #     detail=f"{response.text}",
#             # )
#             data=json.loads(response.text)
#             return data
#     else:
#         print(f"Error fetching data. Status code: {response.status_code}")

# @app.post('/QnA')
# async def query_and_response(request: Request):
#     body = await request.body()
#     # Decode the byte string to a regular string
#     body_str = body.decode('utf-8')

#     # Parse the string as JSON
#     body_json = json.loads(body_str)

#     # Access the value of the "query" key
#     query = body_json.get('query')
#     slug = body_json.get('slug')
#     url = f'https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1/workspace/{slug}/chat'

#     # Define your headers (optional)
#     headers = {
#         "Authorization": "Bearer 19TPS2Z-6004AGY-K968P7Q-2BW0QCD",
#         "Content-Type": "application/json"
#     }

#     # Ensure the data is correctly structured
#     data = {
#         "message": query,
#         "mode": "query",  # Ensure this is the correct mode -- "chat"
#         "sessionId": "identifier-to-partition-chats-by-external-id"
#     }
#     # print(query)
#     # print(type(query))
#     # print(slug, type(slug))
#     try:
#         # Make the POST request
#         response = requests.post(url, headers=headers, json=data)
#         response.raise_for_status()  # Raise an exception for any HTTP errors

#         # Parse the response
#         ans = response.json()

#         # Handle the successful response (status code 200)
#         if 'sources' in ans:
#             texts = [item['text'] for item in ans['sources']]
#             result = {
#                 'textResponse': ans['textResponse'],
#                 'Citations': texts
#             }
#         else:
#             result = {
#                 'textResponse': ans.get('textResponse', 'No response text found'),
#                 'Citations': 'No sources available'
#             }
#         return result

#     except requests.exceptions.HTTPError as http_err:
#         return {"error": f"HTTP error occurred: {http_err}"}
#     except requests.exceptions.RequestException as err:
#         return {"error": f"Request error occurred: {err}"}
#     except Exception as e:
#         return {"error": f"An error occurred: {e}"}



# @app.post("/upload")
# async def upload_document(file: UploadFile):
#     try:
#         content = await file.read()
#         Path(file.filename).write_bytes(content)
#         # storage.child(file.filename).put(file.filename)

#         url = "https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1/document/upload"
#         headers = {
#             "Authorization": "Bearer 19TPS2Z-6004AGY-K968P7Q-2BW0QCD",
#             "accept": "application/json"
#         }
#         files = {'file': (file.filename, content, file.content_type)}
#         print(file.filename)
#         # async with httpx.AsyncClient() as client:
#         response = requests.post(url, headers=headers, files=files)

#         # Validate response status code
#         if response.status_code != 200:
#             raise HTTPException(
#                 status_code=response.status_code,
#                 detail=f"Error uploading file: {response.text}",
#             )

#         os.remove(file.filename)

#         return {"message": file.filename}
#     except Exception as e:
#         print("Error: ", e)
#         raise HTTPException(status_code=400, detail="File upload failed.")


# @app.post("/update_embeddings")
# async def update_workspace_embeddings(request: Request):
#     body = await request.body()
#     # Decode the byte string to a regular string
#     body_str = body.decode('utf-8')
#     # Parse the string as JSON
#     body_json = json.loads(body_str)

#     # Access the value of the "query" key
#     filename = body_json.get('filename')
#     slug = body_json.get('slug')
#     print(filename, slug)
#     url = f'https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1/workspace/{slug}/update-embeddings'
#     headers = {
#         "Authorization": "Bearer 19TPS2Z-6004AGY-K968P7Q-2BW0QCD",
#         "accept": "application/json"
#     }
#     file = filename
#     docs_url = 'https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1/documents'
#     doc_header = {
#         "Authorization": "Bearer 19TPS2Z-6004AGY-K968P7Q-2BW0QCD",
#         "accept": "application/json"
#     }
#     doc_resp = requests.get(docs_url, headers=doc_header)
#     for item in doc_resp.json()['localFiles']['items'][0]['items']:
#         if file in item['name']:
#             fileName = item['name']
#     data = {
#         "adds": [f"custom-documents/{fileName}"
#                  ],
#         "deletes": [" "]

#     }
#     update_resp = requests.post(url, headers=headers, json=data)
#     print(update_resp.json())
#     if update_resp.status_code != 200:
#         raise HTTPException(
#             status_code=update_resp.status_code,
#             detail=f"Error uploading file: {update_resp.text}",
#         )
#     else:
#         return {"message": "Embeddings updated successfully"}


# @app.get("/docs_list")
# async def list_of_docs():
#     url="https://literate-meme-7vrq4j7xv66p2x5w4-3001.app.github.dev/api/v1/documents"
#     headers= {
#         "Authorization": "Bearer 19TPS2Z-6004AGY-K968P7Q-2BW0QCD",
#         "accept": "application/json"
#         }
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(url, headers=headers)
#     except Exception as exc:
#         raise HTTPException(status_code=500, detail="An unexpected error occurred.")

#     list = response.json()
#     doc_list= list['localFiles']['items'][0]
#     doc_names=[]
#     for i,item in enumerate(doc_list['items']):
#         doc_names.append(item['name'])
#     return doc_names
