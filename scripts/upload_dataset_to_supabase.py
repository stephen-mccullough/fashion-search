"""
Fashion Product Dataset Generation Script

This script loads fashion product data from Hugging Face datasets,
processes it to generate embeddings and captions, and saves the 
enriched data to disk for later use in search applications.
"""

import os
import argparse
from supabase import create_client, Client
from openai import OpenAI
import threading
from dotenv import load_dotenv
from datasets import load_dataset, load_from_disk
from utils import upsert_fashion_product, process_product

# Load environment variables from .env file
load_dotenv()

# Add a lock for thread-safe printing in multiprocessing
print_lock = threading.Lock()

# Initialize API clients
supabase_client: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
openai_client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def process_dataset_from_huggingface_hub(
    dataset_name: str, 
    data_files: str, 
    split: str,
    limit: int,
    num_proc: int
) -> None:
    """
    Process a dataset from Hugging Face Hub.
    
    Args:
        dataset_name (str): Name of the dataset on Hugging Face Hub
        data_files (str): Specific data files to load
        split (str): Dataset split to use (e.g., "train", "full")
        limit (int): Maximum number of records to process
        num_proc (int): Number of processes to use for parallel processing
    """
    # Load the dataset using the specified parameters
    dataset = load_dataset(dataset_name, data_files, split=split)
    print(f"Loaded dataset with {len(dataset)} records")
    dataset = dataset.select(range(min(limit, len(dataset))))
    dataset.map(
        lambda x: process_product(x, openai_client), 
        num_proc=num_proc,
        remove_columns=[]
    )

def process_dataset_from_disk(dataset_path: str, limit: int, num_proc: int) -> None:
    """
    Process a dataset from a local file path.
    
    Args:
        dataset_path (str): Path to the dataset on disk
        
    Returns:
        Dataset: A Hugging Face dataset object
    """
    
    # Load the dataset from disk
    print("Loading data from disk")
    data = load_from_disk(dataset_path)
    data = data.select(range(min(limit, len(data))))
    print(f"Loaded {len(data)} records from {dataset_path}")
    
    data.map(
        lambda x: upsert_fashion_product(supabase_client, x, x['embedding'] ), 
        num_proc=args.num_proc, 
        remove_columns=[]
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the script.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Upload dataset to Supabase')

    # Create a mutually exclusive group (optional)
    group = parser.add_mutually_exclusive_group()

    # Add the generate-embeddings flag to the group
    group.add_argument(
        '--generate-embeddings', 
        action='store_true',
        help='Generate embeddings for the dataset from HuggingFace Hub'
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
        help='Limit the number of records to upload to Supabase (default: 3000)'
    )
    
    parser.add_argument(
        '--input-path', 
        type=str, 
        default="data/amazon_fashion_sample",
        help='Path to the dataset on disk (required if --generate-embeddings is not used)'
    )

    # Parse the arguments
    args = parser.parse_args()

    # Validate that input-path is provided if not generating embeddings
    if not args.generate_embeddings and not args.input_path:
        parser.error('--input-path is required when --generate-embeddings is not used')

    return args


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()
        
    # Handle loading from Hugging Face or local dataset     
    if args.generate_embeddings:
        process_dataset_from_huggingface_hub(
            "McAuley-Lab/Amazon-Reviews-2023",
            "raw_meta_Amazon_Fashion",
            "full",
            args.limit,
            args.num_proc
        )
    else:
        process_dataset_from_disk(args.input_path, args.limit, args.num_proc)
    
    # Re-index the HNSW index on the embeddings table
    print("Updating HNSW index...")
    supabase_client.rpc('update_hnsw_index').execute()
    print("Index update complete!")
    