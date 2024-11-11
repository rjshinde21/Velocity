import React, { useState, useEffect } from 'react';
import { Coins } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TokenDetails = () => {
  const [tokenInfo, setTokenInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuthAndFetchTokens = async () => {
      const authToken = localStorage.getItem('token');
      console.log("auth token:"+authToken);
      if (!authToken) {
        setError('Authentication required');
        navigate('/login');
        return;
      }
      await fetchTokenDetails(authToken);
    };

    checkAuthAndFetchTokens();
  }, [navigate]);

  const fetchTokenDetails = async (authToken) => {
    try {
      setIsLoading(true);
      setError(null);

      // Get user ID from localStorage
      const userId = localStorage.getItem('userId');
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await fetch('http://127.0.0.1:3000/api/token-types/23', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include'
      });

      if (response.status === 401) {
        // Clear invalid credentials
        localStorage.removeItem('token');
        localStorage.removeItem('userId');
        navigate('/login');
        throw new Error('Session expired. Please login again.');
      }

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setTokenInfo(data.data);

    } catch (err) {
      console.error('Token fetch error:', err);
      setError(err.message);
      
      // Handle specific error cases
      if (err.message.includes('Session expired') || err.message.includes('User ID not found')) {
        navigate('/login');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    const authToken = localStorage.getItem('token');
    if (authToken) {
      await fetchTokenDetails(authToken);
    } else {
      navigate('/login');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
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
            onClick={handleRefresh}
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
            <button>Top UP Credits</button>
          </div>

          {/* <div className="bg-black/60 p-3 rounded">
            <p className="text-gray-400 text-sm">Remaining Tokens</p>
            <p className="text-white font-semibold">
              {tokenInfo.token_received - tokenInfo.tokens_used}
            </p>
            <div className="w-full bg-gray-700 rounded-full h-2.5 mt-2">
              <div 
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                style={{
                  width: `${((tokenInfo.token_received - tokenInfo.tokens_used) / tokenInfo.token_received) * 100}%`
                }}
              ></div>
            </div>
          </div> */}

          {/* <div className="grid grid-cols-2 gap-4">
            <div className="bg-black/60 p-3 rounded">
              <p className="text-gray-400 text-sm">Purchase Date</p>
              <p className="text-white font-semibold">{formatDate(tokenInfo.boughtDateTime)}</p>
            </div>
            <div className="bg-black/60 p-3 rounded">
              <p className="text-gray-400 text-sm">Expiry Date</p>
              <p className="text-white font-semibold">{formatDate(tokenInfo.expiryDateTime)}</p>
            </div>
          </div> */}
        </div>
      )}
    </div>
  );
};

export default TokenDetails;