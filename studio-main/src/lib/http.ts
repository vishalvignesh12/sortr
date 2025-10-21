import { API_BASE_URL } from './config';

interface ApiConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: unknown;
  headers?: Record<string, string>;
  token?: string;
}

class HttpClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async request<T>(endpoint: string, config: ApiConfig = {}): Promise<T> {
    const { method = 'GET', body, headers = {}, token } = config;

    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    // Use provided token or fallback to token from localStorage
    let authToken = token;
    if (!authToken) {
      authToken = typeof window !== 'undefined' ? (localStorage.getItem('token') || undefined) : undefined;
    }

    if (authToken) {
      requestHeaders['Authorization'] = `Bearer ${authToken}`;
    }

    const url = `${this.baseUrl}${endpoint}`;
    const requestConfig: RequestInit = {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
    };

    try {
      const response = await fetch(url, requestConfig);

      if (!response.ok) {
        // If authentication fails, redirect to login or clear the token
        if (response.status === 401 || response.status === 403) {
          if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
          }
        }
        
        const errorData = await response.text();
        throw new Error(`HTTP Error: ${response.status} - ${errorData}`);
      }

      // For DELETE requests or responses without body, return success
      if (method === 'DELETE' || response.status === 204) {
        return undefined as T;
      }

      return response.json();
    } catch (error) {
      console.error(`API request error: ${method} ${url}`, error);
      throw error;
    }
  }

  get<T>(endpoint: string, token?: string) {
    return this.request<T>(endpoint, { method: 'GET', token });
  }

  post<T>(endpoint: string, body?: unknown, token?: string) {
    return this.request<T>(endpoint, { method: 'POST', body, token });
  }

  put<T>(endpoint: string, body?: unknown, token?: string) {
    return this.request<T>(endpoint, { method: 'PUT', body, token });
  }

  delete<T>(endpoint: string, token?: string) {
    return this.request<T>(endpoint, { method: 'DELETE', token });
  }

  patch<T>(endpoint: string, body?: unknown, token?: string) {
    return this.request<T>(endpoint, { method: 'PATCH', body, token });
  }
}

export const apiClient = new HttpClient(API_BASE_URL);