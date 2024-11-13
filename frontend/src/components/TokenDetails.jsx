import React, { useState, useEffect } from 'react';
import { Coins } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TokenDetails = () => {
  const [tokenInfo, setTokenInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Get user data from localStorage
  const userId = localStorage.getItem('userId');
  const authToken = localStorage.getItem('token');

  useEffect(() => {
    const checkAuthAndFetchTokens = async () => {
      // console.log("Checking auth - User ID:", userId);
      // console.log("Auth Token:", authToken);

      if (!authToken || !userId) {
        setError('Authentication required');
        navigate('/login');
        return;
      }
      await fetchTokenDetails();
    };

    checkAuthAndFetchTokens();
  }, [navigate, isUpdating]);

  const fetchTokenDetails = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // console.log("Fetching tokens for user:", userId);
      const response = await fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },  
        credentials: 'include'
      });

      // console.log("Token API Response status:", response.status);

      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('userId');
        localStorage.removeItem('userEmail');
        navigate('/login');
        throw new Error('Session expired. Please login again.');
      }

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const responseData = await response.json();
      // console.log("Token API Response data:", responseData);

      // Make sure we're accessing the correct data structure
      if (responseData.data) {
        setTokenInfo(responseData.data);
      } else {
        throw new Error('Invalid data format received');
      }

    } catch (err) {
      console.error('Token fetch error:', err);
      setError(err.message);
      
      if (err.message.includes('Session expired') || err.message.includes('Invalid data format')) {
        navigate('/login');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleTopUp = async () => {
    const authToken = localStorage.getItem('token');
    const userId = localStorage.getItem('userId'); // Ensure userId is retrieved correctly
    if (!authToken || !userId) {
      setError('Authentication required.');
      return;
    }
  
    try {
      setIsUpdating(true);
      setError(null);
  
      console.log("Initiating top-up for user:", userId);
        
      const response = await fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          token_received: 72,
          user_id: userId
        })
      });
  
      // console.log("Top-up response status:", response.status);
  
      if (!response.ok) {
        throw new Error(`Failed to update tokens: ${response.status}`);
      }
  
      const updatedData = await response.json();
      console.log("Top-up response data:", updatedData); // Log the full response structure
  
      // Check and set token info based on the actual structure
      if (updatedData && updatedData.data) {
        setTokenInfo(updatedData.data);
        alert('Successfully topped up credits!');
      } 
      // else {
      //   console.log("Unexpected response format:", updatedData);
      //   throw new Error('Invalid response data format. Expected "data" field.');
      // }
  
    } catch (error) {
      console.error('Top-up error:', error);
      setError(error.message);
      alert('Failed to top up tokens. Please try again.');
    } finally {
      setIsUpdating(false);
    }
  };
  

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-black/40 rounded-lg p-4 w-full max-w-md mx-auto">
        <div className="text-red-500 text-center">
          <p>{error}</p>
          <button
            onClick={fetchTokenDetails}
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-black/40 rounded-lg p-4 w-full max-w-md mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Coins className="w-6 h-6 text-yellow-500 mr-2" />
          <h2 className="text-xl font-semibold text-white">Token Details</h2>
        </div>
      </div>

      {tokenInfo && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-black/60 p-3 rounded">
              <p className="text-gray-400 text-sm">Total Tokens</p>
              <p className="text-white font-semibold">{tokenInfo.token_received}</p>
            </div>
            <div className="bg-black/60 p-3 rounded">
              <p className="text-gray-400 text-sm">Used Tokens</p>
              <p className="text-white font-semibold">{tokenInfo.tokens_used}</p>
            </div>
          </div>


          <div className="flex justify-center mt-4">
            <button
              onClick={handleTopUp}
              disabled={isUpdating}
              className={`px-4 py-2 ${
                isUpdating 
                  ? 'bg-gray-500 cursor-not-allowed' 
                  : 'bg-green-500 hover:bg-green-600'
              } text-white font-semibold rounded transition-colors`}
            >
              {isUpdating ? 'Processing...' : 'Top Up Credits'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TokenDetails;