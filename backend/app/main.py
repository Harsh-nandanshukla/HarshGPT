
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__),"services"))
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Annotated,Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


try:
    from llm_chain import get_answer       # Local ✅
except ImportError:
    from app.services.llm_chain import get_answer 

# Rate limiter
limiter = Limiter(key_func=get_remote_address) #getting user IP to limit hourly rate

app = FastAPI(
    title="HarshGPT API",
    description="AI assistant for Harsh's documents",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)#When limit is exceeded,Return proper error response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SourceItem(BaseModel):
    source: str
    page: int

# Request model
class QueryRequest(BaseModel):
    question: Annotated[str,Field(description="User's question about Harsh's documents",min_length=1,max_length=120, example="What are Harsh's technical skills?")]
    # source_filter: Annotated[Optional[str],Field(description="Optional PDF filename to filter search",default=None,examples=None)]
# Response model
class QueryResponse(BaseModel):
    answer: Annotated[str,Field(description="HarshGPT's answer to user's query",min_length=1)]
    sources: Annotated[list[SourceItem],Field(description="List of source documents used to generate the answer")]

@app.get("/")
def root():
    return {"message": "HarshGPT API is running.. "}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/chat", response_model=QueryResponse)
@limiter.limit("3/hour")
async def chat(request: Request, query: QueryRequest):
    if not query.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    try:
        result = get_answer(
            query=query.question          
    )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"]
    )
