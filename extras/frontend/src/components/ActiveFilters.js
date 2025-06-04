import React from 'react';
import './ActiveFilters.css';

const ActiveFilters = ({ filters }) => {
  if (!filters) return null;

  // Function to generate friendly filter labels
  const getFilterLabel = (key, value) => {
    switch (key) {
      case 'min_price':
        return `Items over $${value}`;
      case 'max_price':
        return `Items under $${value}`;
      case 'min_avg_rating':
        return `${value}+ stars`;
      case 'max_avg_rating':
        return `Up to ${value} stars`;
      case 'min_rating_count':
        return `${value}+ reviews`;
      case 'max_rating_count':
        return `Up to ${value} reviews`;
      case 'store_name':
        return `Store: ${value}`;
      case 'discontinued':
        return value === 'No' ? 'Not discontinued' : 'Discontinued items';
      default:
        return `${key}: ${value}`;
    }
  };

  return (
    <div className="active-filters">
      {Object.entries(filters).map(([key, value]) => {
        // Only render if the filter has a value (not null or empty string)
        if (value === null || value === '') return null;
        
        return (
          <div key={key} className="filter-tag">
            {getFilterLabel(key, value)}
          </div>
        );
      })}
    </div>
  );
};

export default ActiveFilters; 