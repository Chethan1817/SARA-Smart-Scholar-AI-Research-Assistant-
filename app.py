from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import aiofiles
from scholarly import scholarly
import requests
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
import pinecone
from dotenv import load_dotenv
import openai
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="SmartScholar AI Research Assistant")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Pinecone
pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment=os.getenv("PINECONE_ENVIRONMENT")
)
index = pinecone.Index(os.getenv("PINECONE_INDEX_NAME"))

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Pydantic models
class ResearchRequest(BaseModel):
    keyword: str
    num_results: Optional[int] = 10

class Question(BaseModel):
    question: str

class ResearchResponse(BaseModel):
    status: str
    job_id: str

# In-memory storage for job status and results
research_jobs = {}

async def process_and_store_pdf(file_path: str, job_id: str):
    """Process PDF and store chunks in Pinecone"""
    try:
        # Load PDF
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(pages)
        
        # Store in Pinecone
        for i, chunk in enumerate(chunks):
            index.upsert(
                vectors=[{
                    'id': f"{job_id}-chunk-{i}",
                    'values': chunk.page_content,  # You'll need to convert this to embeddings
                    'metadata': {
                        'page': chunk.metadata.get('page', 0),
                        'source': file_path
                    }
                }]
            )
    except Exception as e:
        print(f"Error processing PDF {file_path}: {str(e)}")

async def download_pdfs(keyword: str, job_id: str):
    """Download PDFs from Google Scholar"""
    try:
        # Search Google Scholar
        search_query = scholarly.search_pubs(keyword)
        results = []
        
        for i, result in enumerate(search_query):
            if i >= 5:  # Limit to 5 papers for demonstration
                break
            
            if 'url_pdf' in result:
                pdf_url = result['url_pdf']
                filename = f"downloads/{job_id}/{i}.pdf"
                
                # Create directory if it doesn't exist
                os.makedirs(f"downloads/{job_id}", exist_ok=True)
                
                # Download PDF
                response = requests.get(pdf_url)
                if response.status_code == 200:
                    async with aiofiles.open(filename, 'wb') as f:
                        await f.write(response.content)
                    
                    # Process and store in Pinecone
                    await process_and_store_pdf(filename, job_id)
                    results.append({
                        'title': result.get('title', ''),
                        'url': pdf_url,
                        'authors': result.get('author', [])
                    })
        
        research_jobs[job_id] = {
            'status': 'completed',
            'results': results
        }
    except Exception as e:
        research_jobs[job_id] = {
            'status': 'failed',
            'error': str(e)
        }

@app.post("/research/", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start research process with keyword"""
    job_id = f"job-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    research_jobs[job_id] = {'status': 'processing'}
    
    background_tasks.add_task(download_pdfs, request.keyword, job_id)
    
    return ResearchResponse(
        status="processing",
        job_id=job_id
    )

@app.get("/research/{job_id}/status")
async def get_research_status(job_id: str):
    """Get status of research job"""
    if job_id not in research_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return research_jobs[job_id]

@app.post("/ask/{job_id}")
async def ask_question(job_id: str, question: Question):
    """Ask question about the research"""
    if job_id not in research_jobs or research_jobs[job_id]['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Research not completed")
    
    try:
        # Query Pinecone for relevant chunks
        query_results = index.query(
            vector=question.question,  # You'll need to convert this to embeddings
            top_k=5,
            include_metadata=True
        )
        
        # Prepare context for ChatGPT
        context = "\n\n".join([match['metadata']['text'] for match in query_results['matches']])
        
        # Query ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a research assistant. Answer the question based on the provided context."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question.question}"}
            ]
        )
        
        return {
            "answer": response.choices[0].message['content'],
            "sources": [match['metadata']['source'] for match in query_results['matches']]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)