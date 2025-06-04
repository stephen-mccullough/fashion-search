-- =================================================================
-- ENABLE PGVECTOR EXTENSION
-- =================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- =================================================================
-- TABLE DEFINITIONS
-- =================================================================

-- Main table for storing fashion product information
CREATE TABLE fashion_products (
  parent_asin TEXT PRIMARY KEY,           
  main_category TEXT,                     
  title TEXT,                            
  average_rating DECIMAL(2,1),            
  rating_number INT,                      
  features TEXT[],                        
  description TEXT[],                       
  PRICE DECIMAL,                          
  images JSONB,                           
  videos JSONB,                           
  store TEXT,                             
  categories TEXT[],                      
  details JSONB,                          
  bought_together TEXT[]                
);

-- Separate table for product embeddings (for better performance)
CREATE TABLE fashion_product_embeddings (
    parent_asin TEXT PRIMARY KEY REFERENCES fashion_products(parent_asin),
    embedding vector(1536)                
);

-- Create a HNSW (Hierarchical Navigable Small World) index on embeddings
-- This dramatically speeds up vector similarity searches
CREATE INDEX embedding_hnsw_index ON fashion_product_embeddings USING hnsw (embedding vector_ip_ops);

-- =================================================================
-- UPSERT FUNCTION
-- =================================================================

-- Function to insert or update a fashion product and its embedding
-- This provides a single interface for maintaining both tables atomically
CREATE FUNCTION upsert_fashion_product(
    p_parent_asin TEXT,                     
    p_main_category TEXT,                   
    p_title TEXT,                        
    p_average_rating NUMERIC,            
    p_rating_number INT,                  
    p_features TEXT[],                    
    p_description TEXT[],                 
    p_price NUMERIC,                      
    p_images JSONB,                       
    p_videos JSONB,                       
    p_store TEXT,                         
    p_categories TEXT[],                  
    p_details JSONB,                      
    p_bought_together TEXT[],             
    p_embedding VECTOR(1536)              
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO fashion_products (
        parent_asin,
        main_category,
        title,
        average_rating,
        rating_number,
        features,
        description,
        price,
        images,
        videos,
        store,
        categories,
        details,
        bought_together
    ) VALUES (
        p_parent_asin,
        p_main_category,
        p_title,
        p_average_rating,
        p_rating_number,
        p_features,
        p_description,
        p_price,
        p_images,
        p_videos,
        p_store,
        p_categories,
        p_details,
        p_bought_together
    )
    ON CONFLICT (parent_asin) DO UPDATE SET
        main_category = p_main_category,
        title = p_title,
        average_rating = p_average_rating,
        rating_number = p_rating_number,
        features = p_features,
        description = p_description,
        price = p_price,
        images = p_images,
        videos = p_videos,
        store = p_store,
        categories = p_categories,
        details = p_details,
        bought_together = p_bought_together;
        
    INSERT INTO fashion_product_embeddings (
        parent_asin,
        embedding
    ) VALUES (
        p_parent_asin,
        p_embedding
    )
    ON CONFLICT (parent_asin) DO UPDATE SET
        embedding = p_embedding;
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- REINDEXING FUNCTION
-- =================================================================

-- Function to rebuild the HNSW index
-- Call this after bulk inserts or updates to ensure index optimization
CREATE FUNCTION update_hnsw_index()
RETURNS VOID AS $$
BEGIN
    REINDEX INDEX embedding_hnsw_index;
END;
$$ LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public;

-- =================================================================
-- SEARCH FUNCTION
-- =================================================================

-- Core search function that performs semantic and filter-based search
-- Returns a table of matching fashion products ordered by semantic similarity
CREATE FUNCTION get_fashion_items(
    prompt_embedding vector(1536),        
    match_threshold float,                
    match_count int,                      
    min_price float,                      
    max_price float,                      
    min_avg_rating float,                 
    max_avg_rating float,                 
    min_rating_count int,                 
    max_rating_count int,                 
    store_name text,                      
    discontinued text                     
)
RETURNS TABLE(
    parent_asin text,                     
    title text,                          
    images jsonb,                        
    average_rating numeric,              
    rating_number int,                   
    price numeric,                       
    store text,                          
    cosine_distance double precision,    
    discontinued_item text               
) AS $$
BEGIN
  RETURN QUERY
    SELECT 
      -- Select relevant product fields from both tables
      fashion_products.parent_asin, 
      fashion_products.title, 
      fashion_products.images, 
      fashion_products.average_rating, 
      fashion_products.rating_number, 
      fashion_products.price, 
      fashion_products.store,
      -- Calculate cosine distance between query and product embeddings
      -- Lower values mean higher similarity
      fashion_product_embeddings.embedding <=> prompt_embedding AS cosine_distance,
      -- Handle null values for discontinued status
      COALESCE(fashion_products.details->>'Is Discontinued By Manufacturer', 'No') AS discontinued_item
    FROM fashion_products
    INNER JOIN fashion_product_embeddings ON fashion_products.parent_asin = fashion_product_embeddings.parent_asin
    WHERE 
      -- Convert threshold to distance (<=> operator measures distance, not similarity)
      fashion_product_embeddings.embedding <=> prompt_embedding < 1 - match_threshold
      -- Apply all optional filters (these are ignored if NULL)
      AND (min_price IS NULL OR fashion_products.price >= min_price)
      AND (max_price IS NULL OR fashion_products.price <= max_price)
      AND (min_avg_rating IS NULL OR fashion_products.average_rating >= min_avg_rating)
      AND (max_avg_rating IS NULL OR fashion_products.average_rating <= max_avg_rating)
      AND (min_rating_count IS NULL OR fashion_products.rating_number >= min_rating_count)
      AND (max_rating_count IS NULL OR fashion_products.rating_number <= max_rating_count)
      AND (store_name IS NULL OR fashion_products.store = store_name)
      AND (discontinued IS NULL OR COALESCE(fashion_products.details->>'Is Discontinued By Manufacturer', 'No') = discontinued)
    -- Order by semantic similarity (lowest distance first)
    ORDER BY fashion_product_embeddings.embedding <=> prompt_embedding ASC
    -- Limit results (with a hard cap of 100)
    LIMIT LEAST(match_count, 100);
END;
$$ LANGUAGE plpgsql;
