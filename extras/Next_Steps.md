# Next Steps for Fashion Search

The current state of Fashion Search represents a solid foundation for semantic fashion product discovery, but several key areas offer opportunities for enhancement and optimization.

## Performance and Cost Optimization
- **Batch Processing Improvements**: Implement batching strategies for embedding generation to optimize OpenAI API usage and reduce processing time. Currently, the ingestion system has yet to make use of batching functionality in OpenAI's APIs. Incorporating batch processing would he
- **Parallel Processing**: Experiment with optimal multi-processing configurations
- **Database Query Optimization**: Fine-tune HNSW index parameters to balance search speed and accuracy
- **Ranking Algorithm Optimization**: Explore further options and algorithms for the hybrid ranking system.

## Feature Expansion
- **More Generated Filter Options**: Implement functionality to generate filters for  gender, age, and style of fashion products
- **Visual Search**: Extend the API to support image uploads for "find similar" functionality
