import React, { useState, useCallback, memo } from 'react';
import './ProductCard.css';

// Use memo to prevent unnecessary re-renders
const ProductCard = memo(({ product }) => {
  // State to track the current image index
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  
  // Get all available images or use a placeholder if none
  const getImages = () => {
    // Check for new API response format where images is an object containing arrays
    if (product.images && typeof product.images === 'object') {
      // Handle new API format with arrays of images
      if (Array.isArray(product.images.large)) {
        // Prioritize hi_res images if available
        return product.images.large.map((_, idx) => {
          // Prefer hi_res images if available, fallback to large, then thumb
          if (product.images.hi_res && product.images.hi_res[idx]) {
            return product.images.hi_res[idx];
          } else if (product.images.large[idx]) {
            return product.images.large[idx];
          } else if (product.images.thumb && product.images.thumb[idx]) {
            return product.images.thumb[idx];
          }
          return 'https://via.placeholder.com/300x300?text=No+Image';
        });
      }
    }
    
    // Handle old API format (array of objects)
    if (Array.isArray(product.images)) {
      return product.images.map(img => img.large || img.thumb || img.hi_res);
    }
    
    // Fallback when no images are available
    return ['https://via.placeholder.com/300x300?text=No+Image'];
  };
  
  const images = getImages();
  
  // Use useCallback to memoize these functions
  const prevImage = useCallback(() => {
    setCurrentImageIndex((prevIndex) => 
      prevIndex === 0 ? images.length - 1 : prevIndex - 1
    );
  }, [images.length]);
  
  const nextImage = useCallback(() => {
    setCurrentImageIndex((prevIndex) => 
      prevIndex === images.length - 1 ? 0 : prevIndex + 1
    );
  }, [images.length]);

  // Format price if available
  const formattedPrice = product.price 
    ? `$${product.price.toFixed(2)}` 
    : 'Price not available';
    
  // Check if product is discontinued
  const isDiscontinued = (product.details && 
    (product.details["Is Discontinued By Manufacturer"] === "Yes" || 
     product.details["DISCONTINUED_BY_MANUFACTURER"] === "Yes")) ||
    product.discontinued_item === "Yes";

  return (
    <div className="product-card">
      <div className="product-image-container">
        <div className="product-image">
          <img src={images[currentImageIndex]} alt={product.title} />
        </div>
        
        {images.length > 1 && (
          <div className="image-navigation">
            <button className="nav-button prev" onClick={prevImage}>
              &#10094;
            </button>
            <div className="image-indicator">
              {images.map((_, index) => (
                <span 
                  key={index} 
                  className={`dot ${index === currentImageIndex ? 'active' : ''}`}
                  onClick={() => setCurrentImageIndex(index)}
                ></span>
              ))}
            </div>
            <button className="nav-button next" onClick={nextImage}>
              &#10095;
            </button>
          </div>
        )}
      </div>
      
      <div className="product-info">
        <h3 className="product-title">{product.title}</h3>
        
        {isDiscontinued && (
          <div className="discontinued-notice">
            Discontinued by Manufacturer
          </div>
        )}
        
        <div className="product-rating">
          {product.average_rating && (
            <>
              <span className="stars">
                {Array(5).fill().map((_, i) => (
                  <span key={i} className={i < Math.round(product.average_rating) ? 'star filled' : 'star'}>★</span>
                ))}
              </span>
              <span className="rating-count">({product.rating_number || 0})</span>
            </>
          )}
        </div>
        
        <div className="product-price">{formattedPrice}</div>
        
        {product.store && <div className="product-store">Sold by: {product.store}</div>}
        
        {product.parent_asin && (
          <div className="product-asin">
            <span className="asin-label">ASIN:</span> {product.parent_asin}
          </div>
        )}
        
        {product.features && product.features.length > 0 && (
          <div className="product-features">
            <h4>Features:</h4>
            <ul>
              {product.features.slice(0, 3).map((feature, index) => (
                <li key={index}>{feature}</li>
              ))}
              {product.features.length > 3 && <li>...</li>}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
});

export default ProductCard; 