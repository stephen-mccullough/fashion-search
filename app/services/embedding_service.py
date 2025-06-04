"""
Embedding Service Module

This module provides functionality for generating embeddings using OpenAI's API.
It includes methods for generating prompt embeddings and handling embedding-related tasks.
"""

from openai import OpenAI
from typing import List, Any

class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI's API.
    
    This service handles the creation of vector embeddings from text inputs,
    which can be used for semantic search and similarity comparisons.
    """
    
    # Default embedding model to use
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    def __init__(self, openai_client: OpenAI):
        """
        Initialize the embedding service.
        
        Args:
            openai_client (OpenAI): Initialized OpenAI client instance
        """
        self.openai_client = openai_client
        
    def generate_prompt_embedding(self, prompt: str) -> List[float]:
        """
        Generate an embedding vector for the provided text prompt.
        
        This method sends the text prompt to OpenAI's embedding API and returns
        the resulting vector representation.
        
        Args:
            prompt (str): The text to generate an embedding for
            
        Returns:
            List[float]: The embedding vector as a list of floating point numbers
            
        Raises:
            Exception: If the OpenAI API request fails
        """
        # Call OpenAI's embeddings API with the provided prompt
        response = self.openai_client.embeddings.create(
            model=self.EMBEDDING_MODEL,
            input=[prompt]
        )
        
        # Extract and return just the embedding vector from the response
        return response.data[0].embedding