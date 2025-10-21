// Backend API types
export interface BackendSlotStatus {
  slot_id: string;
  occupied: boolean;
  confidence: number;
  vehicle_type?: string;
  last_seen?: string;
  reserved_until?: string;
  predicted_free_minutes?: number;
  prediction_confidence?: number;
}

export interface BackendHoldRequest {
  slot_id: string;
  hold_minutes: number;
  user_id?: string;
}

export interface BackendHoldResponse {
  booking_id: string;
  hold_until: string; // ISO date string
}

// Frontend types
export interface ParkingSlot {
  id: string;
  status: 'Free' | 'Occupied';
  confidence?: number;
  vehicleType?: string;
  lastSeen?: string;
  reservedUntil?: string;
  predictedFreeMinutes?: number;
  predictionConfidence?: number;
  occupiedSince?: string;
}

// Auth types
export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
}
