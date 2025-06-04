"""
Query Service Module

This module provides database querying functionality for the fashion items database.
It includes methods for vector similarity search and item retrieval.
"""

import json
from typing import Dict, List, Any, Optional
from supabase import Client

class QueryService:
    """
    Service for querying the database for fashion items.
    
    This service provides methods to perform vector similarity searches and
    retrieve specific items from the database.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the query service.
        
        Args:
            supabase_client (Client): Initialized Supabase client instance
        """
        self.supabase_client = supabase_client
        
    def query_postgres(self, prompt_embedding: List[float], filter_expression: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform a vector similarity search on fashion items.
        
        This method sends a request to the Supabase RPC function that performs
        vector similarity search using the provided embedding and optional filters.
        
        Args:
            prompt_embedding (List[float]): The embedding vector to search against
            filter_expression (Dict[str, Any]): Optional filters to apply to the search
                                               (e.g., category, brand, price range)
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary containing the matched items
                                            in the "response" key
        """
        # Call the Supabase RPC function with embedding and filters
        response = (
            self.supabase_client.rpc(
                "get_fashion_items",
                {
                    "prompt_embedding": prompt_embedding,
                    "match_threshold": 0.3,  # Minimum similarity score to include results
                    "match_count": 10,       # Maximum number of results to return
                } | filter_expression  # Merge the filter parameters
            ).execute()
        )
        print(response)
        # Wrap the response data in a standardized format
        response = {
            "response": response.data
        }
        return response
    
    def get_item(self, parent_asin: str) -> Dict[str, Any]:
        """
        Retrieve a specific fashion item by its parent ASIN.
        
        Args:
            parent_asin (str): The parent ASIN (Amazon Standard Identification Number)
                              that uniquely identifies the product
            
        Returns:
            Dict[str, Any]: The complete item data if found, or an empty dict if not found
            
        Raises:
            Exception: If the database query fails for reasons other than item not found
        """
        # Query the database for the specific item by parent_asin
        response = (
            self.supabase_client.table("fashion_items")
            .select("*")
            .eq("parent_asin", parent_asin)
            .single() 
            .execute()
        )
        
        return response.data