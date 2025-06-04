"""
Search Service Module

This module provides semantic search functionality for fashion items.
It combines embeddings, database queries, and LLM recommendations to deliver
relevant fashion items based on natural language queries.
"""

from openai import OpenAI
import json
import traceback
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
from pathlib import Path

# Constants
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"

class SearchService:
    """
    Service for semantic search of fashion items.
    
    This service combines vector embeddings, database queries, and LLM-powered
    filtering to provide relevant fashion item recommendations based on
    natural language queries.
    """
    
    def __init__(
        self, 
        openai_client: OpenAI, 
        embedding_service: Any, 
        query_service: Any
    ) -> None:
        """
        Initialize the search service.
        
        Args:
            openai_client (OpenAI): Initialized OpenAI client instance
            embedding_service: Service for generating text embeddings
            query_service: Service for querying the database
        """
        self.openai_client = openai_client
        self.embedding_service = embedding_service
        self.query_service = query_service
    
    def search(self, prompt: str) -> Dict[str, Any]:
        """
        Perform a semantic search for fashion items based on a natural language prompt.
        
        This method:
        1. Generates an embedding for the search prompt
        2. Extracts filter criteria from the prompt using LLM
        3. Queries the database for matching items
        4. Ranks the results based on multiple factors
        5. Generates a natural language recommendation
        
        Args:
            prompt (str): The user's search query in natural language
            
        Returns:
            Dict[str, Any]: A dictionary containing:
                - response: Ranked list of matching items
                - recommendation: LLM-generated recommendation text
                - warnings: List of any warnings or suggestions
                - filters: The extracted filter criteria
        """
        
        # Extract filters and check if query is fashion-related
        filter_expression, is_fashion_related = self._extract_filter_from_prompt(prompt)
        print("filter_expression", filter_expression)
        
        # Handle non-fashion-related queries
        if not is_fashion_related:
            return {
                "recommendation": None,
                "warnings": ["Looks like you're searching for something outside of fashion! Try asking about clothing, accessories, or fashion items instead."],
                "response": None,
                "filters": filter_expression
            }
            
        # Generate embedding for the search prompt
        query_embedding = self.embedding_service.generate_prompt_embedding(prompt)
        
        # Query database for matching items    
        unranked_results = self.query_service.query_postgres(query_embedding, filter_expression)
        
        # Rank the results based on multiple factors
        ranked_response = self._rank_items(unranked_results['response'])            
        
        # Generate a natural language recommendation
        llm_recommendation = self._generate_llm_recommendation(prompt, ranked_response)
        
        # Check if enough results were found
        warnings = []
        if len(ranked_response) < 5:
            warnings.append("Not many items were found. Try broadening your search!")
            
        # Return the complete response
        return {
            "response": ranked_response,
            "recommendation": llm_recommendation,
            "warnings": warnings,
            "filters": filter_expression
        }
    
    def _extract_filter_from_prompt(self, prompt: str) -> Tuple[Dict[str, Any], bool]:
        """
        Extract filter criteria from the user's prompt using LLM.
        
        This method uses OpenAI's API to analyze the prompt and extract structured
        filter parameters as well as determine if the query is fashion-related.
        
        Args:
            prompt (str): The user's search query
            
        Returns:
            Tuple[Dict[str, Any], bool]: A tuple containing:
                - A dictionary of filter parameters to apply to the database query
                - A boolean indicating whether the query is fashion-related
        """
        # Load the filter schema
        filter_schema = json.load(open(SCHEMAS_DIR / "filter_schema.json"))
        
        # Query the LLM to extract filters
        response = self.openai_client.responses.create(
            model = "gpt-4.5-preview-2025-02-27",
            input = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts search filters from a user's prompt. \
                        These filters are used when querying a SQL database which contains data about fashion \
                        items in an e-commerce store. The ratings are rated from 0-5."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            text = {
                "format": filter_schema
            }
        )
        
        # Parse the response and extract fashion-relevance flag
        filter_expression = json.loads(response.output_text)
        is_fashion_related = filter_expression['is_related_to_fashion']
        filter_expression.pop('is_related_to_fashion')
        
        return filter_expression, is_fashion_related
    
    def _rank_items(
        self,
        items: List[Dict[str, Any]],
        similarity_weight: float = 0.7,
        rating_weight: float = 0.2,
        popularity_weight: float = 0.1,
        min_ratings: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Rank items based on provided cosine similarity, average rating, and number of ratings.
        
        This method implements a multi-factor ranking algorithm that considers:
        - Vector similarity (how well the item matches the search semantically)
        - Average rating (how well-reviewed the item is)
        - Popularity (how many reviews the item has)
        
        Args:
            items: List of dictionaries containing item data.
                Each dict should have: 
                - 'cosine_distance': pre-calculated distance (lower is better)
                - 'average_rating': average rating (0-5)
                - 'rating_number': number of ratings
            similarity_weight: Weight for cosine similarity in final score
            rating_weight: Weight for average rating in final score
            popularity_weight: Weight for number of ratings in final score
            min_ratings: Minimum number of ratings for full confidence
        
        Returns:
            List of dictionaries sorted by score in descending order with
            a 'score' field added to each item
        """
        # Find the maximum number of ratings for normalization
        max_ratings = max(item['rating_number'] for item in items) if items else 1
        ranked_items = []
        
        for item in items:
            # Convert cosine distance to cosine similarity (1 is perfect match)
            similarity = 1 - item['cosine_distance']
            
            # Normalize average rating to 0-1 scale (assuming ratings are 0-5)
            average_rating_normalized = item['average_rating'] / 5.0
            
            # Calculate a confidence factor based on number of ratings
            # (caps at 1.0 when reaching min_ratings threshold)
            confidence = min(item['rating_number'] / min_ratings, 1)
            
            # Adjust rating score based on confidence
            # (items with few ratings are penalized)
            rating_score = average_rating_normalized * confidence
            
            # Normalize number of ratings on log scale to handle large variations
            popularity_score = np.log1p(item['rating_number']) / np.log1p(max_ratings)
            
            # Calculate final score as weighted sum of the three factors
            final_score = (
                similarity_weight * similarity +
                rating_weight * rating_score +
                popularity_weight * popularity_score
            )
            
            # Add the score to the item dictionary
            item_with_score = item.copy()  # Create a copy to avoid modifying original
            item_with_score['score'] = final_score
            ranked_items.append(item_with_score)
        
        # Sort by score in descending order (highest scores first)
        return sorted(ranked_items, key=lambda x: x['score'], reverse=True)
    
    def _generate_llm_recommendation(
        self, 
        prompt: str, 
        item_results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a natural language recommendation based on the query and results.
        
        This method uses an LLM to analyze the user's query and the top search results,
        then generates a personalized recommendation summarizing the findings.
        
        Args:
            prompt (str): The original user query
            item_results (List[Dict[str, Any]]): The ranked search results
            
        Returns:
            str: A natural language recommendation (max 2 sentences)
        """
        # Extract item titles for the system prompt
        item_titles = [item['title'] for item in item_results]
        
        # Create system prompt with guidance for the LLM
        system_prompt = f"You are a helpful assistant that provides recommendations to a user \
        based on their query. Use the provided original user query, and the titles and descriptions of the \
        recommended items to provide a recommendation. This recommendation should be no more \
        than 2 sentences. If the query is not related to fashion, tell the user that the site is for \
        searching for fashion items. The titles of the recommended items are: {item_titles}"      

        # Format the user input
        input_content = [
            {
                "type": "input_text",
                "text": prompt
            }
        ]
        
        # Load the recommendation schema
        recommendation_schema = json.load(open(SCHEMAS_DIR / "recommendation_schema.json"))
        
        # Query the LLM for a recommendation
        response = self.openai_client.responses.create(
            model="gpt-4o-mini",
            instructions = system_prompt,
            input=[
                {
                    "role": "user",
                    "content": input_content,
                }
            ],
            text = {
                "format": recommendation_schema
            }
        )
        
        # Parse the response and extract the recommendation text
        response_data = json.loads(response.output_text)
        result = response_data['response']
        
        return result
