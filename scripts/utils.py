"""
Fashion Product Utilities

This module provides utility functions for processing fashion product data,
including text construction, embedding generation, caption generation,
and database operations.
"""

from openai import OpenAI
import json
from typing import Dict, List, Any, Optional, Union
import traceback
import threading
from time import sleep

# Add a lock for thread-safe printing in multiprocessing
print_lock = threading.Lock()

# Define constants for model names
EMBEDDING_MODEL = "text-embedding-3-small"
CAPTION_MODEL = "gpt-4o-mini"


def construct_product_sentence(product: Dict[str, Any]) -> str:
    """
    Construct a detailed sentence describing a fashion product.
    
    Creates a structured text representation of a product by combining
    its title, features, and description into a coherent sentence.
    
    Args:
        product (Dict[str, Any]): Product data dictionary containing
                                  title, features, and description
    
    Returns:
        str: A formatted sentence describing the product
    """
    clauses = []
    
    # Extract title
    title = product.get('title', 'Unknown title')
    clauses.append(f"The fashion product's title is {title}.")
    
    # Extract and format features
    features = product.get('features', [])
    if features:
        if len(features) == 1:
            clauses.append(f" Its feature is that it is {features[0]}.")
        else:
            # Join all features except the last one
            features_joined = ", it is ".join(features[:-1])
            # Add the last feature with "and"
            clauses.append(f" Its features are that it is {features_joined}, and it is {features[-1]}.")
    
    # Extract and format description
    description = product.get('description', [])
    description_text = " ".join(description) if description else ""
    clauses.append(f" The description of the fashion product is: {description_text}.")
        
    # Create the complete sentence
    sentence = " ".join(clauses)
    
    return sentence


def generate_product_caption(
    openai_client: OpenAI, 
    caption_model: str, 
    product: Dict[str, Any]
) -> str:
    """
    Generate a natural language caption for a fashion product using OpenAI.
    
    Uses the OpenAI API to generate a detailed description of the product
    based on its title and images. The description focuses on the product's
    visual attributes, material, style, and use case.
    
    Args:
        openai_client (OpenAI): Initialized OpenAI client
        caption_model (str): Name of the OpenAI model to use for caption generation
        product (Dict[str, Any]): Product data containing title and images
    
    Returns:
        str: A natural language caption describing the product
    """
    system_prompt = '''
        You are a system generating descriptions for fashion products on an e-commerce website.
        Provided with an image and a title, you will describe the main product that you see in the image, giving details but staying concise.
        You can describe unambiguously what the product is and its material, color, gender, style, and expected use case.
        If there are multiple products depicted, refer to the title to understand which product you should describe.
    '''
    
    print("Generating caption for", product["title"])
    
    # Extract product title
    title = product["title"]
    
    # Select the first 3 large images for the caption generation
    product_images = [{"type": "input_image", "image_url": image} for image in product["images"]['large'][0:3]]
    
    # Construct input content with text and images
    input_content = [
        {
            "type": "input_text",
            "text": title
        }
    ]
    input_content.extend(product_images)
    
    # Call OpenAI API to generate caption
    response = openai_client.responses.create(
        model=caption_model,
        instructions=system_prompt,
        input=[
            {
                "role": "user",
                "content": input_content,
            }
        ]
    )

    return response.output_text


def generate_product_embedding(
    openai_client: OpenAI, 
    embedding_model: str, 
    generated_sentence: str, 
    generated_caption: str
) -> List[float]:
    """
    Generate a vector embedding for a fashion product.
    
    Creates a numerical vector representation (embedding) of the product
    by combining the generated sentence and caption. This embedding can
    be used for semantic search and similarity matching.
    
    Args:
        openai_client (OpenAI): Initialized OpenAI client
        embedding_model (str): Name of the embedding model to use
        generated_sentence (str): Structured sentence describing the product
        generated_caption (str): Natural language caption for the product
    
    Returns:
        List[float]: Vector embedding representing the product
    """
    # Combine sentence and caption, then generate embedding
    response = openai_client.embeddings.create(
        model=embedding_model,
        input=[f"{generated_sentence}. {generated_caption}"]
    )
    return response.data[0].embedding


def upsert_fashion_product(
    supabase_client: Any, 
    product: Dict[str, Any], 
    embedding: List[float]
) -> None:
    """
    Insert or update a fashion product in the database.
    
    Calls the Supabase RPC function 'upsert_fashion_product' to upsert
    a product and its embedding into the database. Handles None values
    appropriately.
    
    Args:
        supabase_client: Initialized Supabase client
        product (Dict[str, Any]): Product data dictionary
        embedding (List[float]): Vector embedding for the product
    
    Returns:
        None
    """
    # Process each field to convert "None" strings to actual None values
    # This ensures proper handling of null values in the database
    response = (
        supabase_client.rpc(
            "upsert_fashion_product",
            {
                "p_parent_asin": product["parent_asin"],
                "p_main_category": product["main_category"] if product["main_category"] != "None" else None,
                "p_title": product["title"] if product["title"] != "None" else None,
                "p_average_rating": product["average_rating"] if product["average_rating"] != "None" else None,
                "p_rating_number": product["rating_number"] if product["rating_number"] != "None" else None,
                "p_features": product["features"] if product["features"] != "None" else None,
                "p_description": product["description"] if product["description"] != "None" else None,
                "p_price": product["price"] if product["price"] != "None" else None,
                "p_images": product["images"] if product["images"] != "None" else None,
                "p_videos": product["videos"] if product["videos"] != "None" else None,
                "p_store": product["store"] if product["store"] != "None" else None,
                "p_categories": product["categories"] if product["categories"] != "None" else None,
                "p_details": product["details"] if product["details"] != "None" else None,
                "p_bought_together": product["bought_together"] if product["bought_together"] != "None" else None,
                "p_embedding": embedding
            }
        ).execute()
    )
    
    
def process_product(product: Dict[str, Any], openai_client: OpenAI) -> Optional[Dict[str, Any]]:
    """
    Process a single product by generating embeddings and captions.
    
    This function:
    1. Constructs a textual representation of the product
    2. Generates a natural language caption using OpenAI
    3. Creates an embedding vector for the product
    
    Args:
        product (Dict[str, Any]): Raw product data dictionary
        
    Returns:
        Optional[Dict[str, Any]]: Processed product with embeddings added,
                                  or None if processing failed
    """
    product = dict(product)  # Create a copy to avoid modifying the original
    
    try:
        # Print progress information (thread-safe)
        with print_lock:
            print(f"Processing {product['parent_asin']}: {product['title']}")
        
        # Generate embedding or use existing if already present
        if 'embedding' in product and product['embedding'] is not None:
            embedding = product['embedding']
        else:
            # Generate a structured sentence representing the product
            generated_sentence = construct_product_sentence(product)
            
            # Generate a natural language caption for the product
            generated_caption = generate_product_caption(
                openai_client, 
                CAPTION_MODEL, 
                product
            )
            
            # Create an embedding vector from the text representations
            embedding = generate_product_embedding(
                openai_client, 
                EMBEDDING_MODEL, 
                generated_sentence, 
                generated_caption
            )
        
        # Create a new dictionary with the embedding added
        result = product.copy()
        result['embedding'] = embedding
        return result
        
    except Exception as e:
        # Log errors but continue processing other products
        print(f"Error processing product: {str(e)[:100]}...")
        traceback.print_exc()   
        sleep(1)  # Brief pause to avoid rate limiting in case of API errors
        return None