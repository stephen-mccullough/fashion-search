"""
Fashion Product Dataset Generation Script

This script loads fashion product data from Hugging Face datasets,
processes it to generate embeddings and captions, and saves the 
enriched data to disk for later use in search applications.
"""

import os
import argparse
from supabase import create_client, Client
from utils import construct_product_sentence, generate_product_embedding, generate_product_caption
from openai import OpenAI
import threading
from dotenv import load_dotenv
from datasets import load_dataset, Dataset
from time import sleep
import traceback
from typing import Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()

# Add a lock for thread-safe printing in multiprocessing
print_lock = threading.Lock()

# Initialize API clients
supabase_client: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
openai_client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def create_dataset_from_huggingface(
    dataset_name: str, 
    data_files: str, 
    split: str
) -> Dataset:
    """
    Load a dataset from Hugging Face Hub.
    
    Args:
        dataset_name (str): Name of the dataset on Hugging Face Hub
        data_files (str): Specific data files to load
        split (str): Dataset split to use (e.g., "train", "full")
        
    Returns:
        Dataset: A Hugging Face dataset object
    """
    # Load the dataset using the specified parameters
    iterable_dataset = load_dataset(dataset_name, data_files, split=split)
    
    # Print dataset size for verification
    print(f"Loaded dataset with {len(iterable_dataset)} records")
        
    return iterable_dataset


def process_product(product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
                "gpt-4o-mini", 
                product
            )
            
            # Create an embedding vector from the text representations
            embedding = generate_product_embedding(
                openai_client, 
                "text-embedding-3-small", 
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


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the script.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Process fashion products data and generate embeddings'
    )
    
    parser.add_argument(
        '--num-proc', 
        type=int, 
        default=10,
        help='Number of processes to use for parallel processing'
    )
    
    parser.add_argument(
        '--limit', 
        type=int, 
        default=3000,
        help='Limit the number of records to process (default: 3000)'
    )
    
    parser.add_argument(
        '--output-path', 
        type=str, 
        default="data/dataset_on_disk",
        help='Path to save processed data'
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load the dataset from Hugging Face
    print("Loading data from Hugging Face")
    data = create_dataset_from_huggingface(
        dataset_name="McAuley-Lab/Amazon-Reviews-2023",
        data_files="raw_meta_Amazon_Fashion", 
        split="full"
    )
        
    # Apply size limit if specified
    if args.limit:
        data = data.select(range(min(args.limit, len(data))))
        print(f"Limited dataset to {len(data)} records")
    
    # Process each product in parallel to generate embeddings
    # The map function applies process_product to each item in the dataset
    print(f"Processing data with {args.num_proc} parallel processes")
    processed_data = data.map(
        lambda x: process_product(x), 
        num_proc=args.num_proc, 
        remove_columns=[]
    )
    
    # Report completion status
    print("Processing complete!")
    print(f"Number of products in processed_data: {len(processed_data)}")
    
    # Save the processed dataset to disk
    print(f"Saving dataset to {args.output_path}")
    processed_data.save_to_disk(args.output_path)
    print("Dataset saved successfully")
    