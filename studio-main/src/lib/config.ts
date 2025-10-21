// API Configuration
let apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// In browser environments, if we're running on a different port, 
// we might want to adjust the API URL accordingly
if (typeof window !== 'undefined') {
  // If frontend and backend are expected to be on the same host but different ports
  const currentHost = window.location.hostname;
  const currentPort = window.location.port;
  
  // If running on the default frontend port (3000) and backend is on 8000
  if (currentPort === '3000' && apiBaseUrl.includes('localhost:8000')) {
    apiBaseUrl = `http://${currentHost}:8000`;
  }
}

export const API_BASE_URL = apiBaseUrl;

// Database configuration
export const DATABASE_TYPE = 'backend'; // Force 'backend' implementation to use our mock backend

// Timeouts
export const REQUEST_TIMEOUT = 10000; // 10 seconds

// Feature flags
export const ENABLE_MOCK_DATA = process.env.NEXT_PUBLIC_ENABLE_MOCK_DATA === 'true';