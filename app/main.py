"""
Fashion Query API Main Application Module

This module initializes and configures the FastAPI application for the Fashion Query API.
It sets up logging, database connections, middleware, and defines all API endpoints.
"""

from supabase import create_client, Client
from openai import OpenAI
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from services.search_service import SearchService
from services.embedding_service import EmbeddingService
from services.query_service import QueryService
from pathlib import Path
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s() - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger: logging.Logger = logging.getLogger(__name__)

# Load data from .env file
ENV_FILE_PATH: Path = Path(__file__).parent.parent/".env"
load_dotenv(ENV_FILE_PATH)

# Create supabase and openai clients
supabase_client: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
openai_client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create FastAPI app
app: FastAPI = FastAPI(title="Fashion Query API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

class QueryRequest(BaseModel):
    """
    Represents a search query request.
    
    Attributes:
        prompt (str): The search text provided by the user
    """
    prompt: str
        
# Initialize services
embedding_service: EmbeddingService = EmbeddingService(openai_client)
query_service: QueryService = QueryService(supabase_client)
search_service: SearchService = SearchService(openai_client, embedding_service, query_service)
    
@app.get("/")
def default_message() -> Dict[str, str]:
    """
    Root endpoint that provides a welcome message.
    
    Returns:
        Dict[str, str]: A dictionary containing a welcome message
    """
    return {"message": "Welcome to the Fashion Query API"}

@app.post("/search")
def semantic_search(request: QueryRequest) -> Dict[str, Any]:
    """
    Endpoint for semantic search of fashion products.
    
    Performs a semantic search using the provided query prompt and returns
    matching fashion products.
    
    Args:
        request (QueryRequest): Request object containing the search prompt
        
    Returns:
        Dict[str, Any]: Search results containing matched products and metadata
        
    Raises:
        HTTPException: 500 error if search processing fails
    """
    try:
        response: Dict[str, Any] = search_service.search(request.prompt)
        return response
    except Exception as e:
        # Log the error for internal monitoring
        logger.error({
            "event": "search_error",
            "error": str(e)
        })
        # Return a user-friendly error message
        raise HTTPException(status_code=500)

@app.get("/items/{parent_asin}")
def get_item(parent_asin: str) -> Dict[str, Any]:
    """
    Retrieves detailed information for a specific product.
    
    Args:
        parent_asin (str): The parent ASIN (Amazon Standard Identification Number)
            that uniquely identifies the product
            
    Returns:
        Dict[str, Any]: Detailed product information
    """
    try:
        response: Dict[str, Any] = query_service.get_item(parent_asin)
        logger.info(f"Retrieved item with parent_asin: {parent_asin}")
        return response
    except Exception as e:
        # Log the error for internal monitoring
        logger.error({
            "event": "get_item_error",
            "error": str(e)
        })
        raise HTTPException(status_code=500)
    
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def catch_all(request: Request, path_name: str) -> JSONResponse:
    """
    Catch-all route handler for undefined endpoints.
    
    This endpoint catches any requests to undefined routes and returns
    a standardized 404 error message.
    
    Args:
        request (Request): The incoming request
        path_name (str): The path that was requested but not found
        
    Returns:
        JSONResponse: A 404 response with an error message
    """
    logger.info(f"Catch-all route called for path: {path_name}")
    return JSONResponse(
        status_code=404,
        content={"error": f"Path '/{path_name}' not found. Please check the documentation for the correct path."}
    )