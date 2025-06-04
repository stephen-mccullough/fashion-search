import React, { memo } from 'react';
import './ProductList.css';
import ProductCard from './ProductCard';

const ProductList = memo(({ products, recommendation, warnings }) => {
  // Function to convert newlines to <br> tags
  const formatText = (text) => {
    if (!text) return '';
    // Replace \n with <br> tags
    return text.replace(/\n/g, '<br>');
  };

  return (
    <div className="product-list">
      {warnings && warnings.length > 0 && (
        <div className="warnings">
          {warnings.map((warning, index) => (
            <div key={`warning-${index}`} className="warning">
              <p dangerouslySetInnerHTML={{ __html: formatText(warning) }}></p>
            </div>
          ))}
        </div>
      )}
      
      {recommendation && (
        <div className="recommendation">
          <p dangerouslySetInnerHTML={{ __html: formatText(recommendation) }}></p>
        </div>
      )}
      
      {products.length > 0 && (
        <>
          <h2>Search Results</h2>
          <div className="products-grid">
            {products.map((product, index) => (
              <ProductCard key={`product-${index}`} product={product} />
            ))}
          </div>
        </>
      )}
    </div>
  );
});

export default ProductList; 