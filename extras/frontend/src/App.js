import React, { useState } from 'react';
import './App.css';
import SearchBar from './components/SearchBar';
import ProductList from './components/ProductList';
import ActiveFilters from './components/ActiveFilters';

const API_URL = 'http://localhost:8000';

function App() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recommendation, setRecommendation] = useState('');
  const [warnings, setWarnings] = useState([]);
  const [filters, setFilters] = useState(null);

  const handleSearch = async (prompt) => {
    setLoading(true);
    setError(null);
    setRecommendation('');
    setWarnings([]);
    setFilters(null);
    
    try {
      // Add a minimum delay of 1 second to show the loading animation
      const fetchPromise = fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });
      
      // Create a delay promise to ensure loading shows for at least 1 second
      const delayPromise = new Promise(resolve => setTimeout(resolve, 1000));
      
      // Wait for both promises to resolve
      const [response] = await Promise.all([fetchPromise, delayPromise]);
      
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }
      
      const data = await response.json();
      
      // Check for recommendation field (accounting for the typo in the API response)
      if (data.recommentation || data.recommendation) {
        setRecommendation(data.recommentation || data.recommendation);
      }
      
      // Check for warnings field
      if (data.warnings && Array.isArray(data.warnings)) {
        setWarnings(data.warnings);
      }
      
      // Get filters if they exist
      if (data.filters) {
        setFilters(data.filters);
      }
      
      setProducts(prevProducts => {
        // Check if the data has a 'response' property (new API format)
        const newProducts = data.response || data.results || data;
        if (JSON.stringify(prevProducts) !== JSON.stringify(newProducts)) {
          return newProducts;
        }
        return prevProducts;
      });
    } catch (err) {
      console.error('Error fetching search results:', err);
      setError('An error occurred while searching. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Fashion Search</h1>
        <p>Find the perfect fashion items with natural language search</p>
      </header>
      <main>
        <SearchBar onSearch={handleSearch} isLoading={loading} />
        
        {filters && <ActiveFilters filters={filters} />}
        
        {loading && (
          <div className="loading">
            <div>Searching for fashion items</div>
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        {error && <div className="error">{error}</div>}
        
        {!loading && !error && (warnings.length > 0 || products.length > 0 || recommendation) ? (
          <ProductList 
            products={products} 
            recommendation={recommendation} 
            warnings={warnings} 
          />
        ) : !loading && !error ? (
          <div className="no-results">
            <p>Enter a natural language query to find fashion items.</p>
            <p>Example: "I need a dress for a summer wedding" or "Show me men's athletic wear"</p>
          </div>
        ) : null}
      </main>
    </div>
  );
}

export default App;
