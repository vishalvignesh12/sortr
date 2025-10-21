import { DATABASE_TYPE } from '@/lib/config';
import { ParkingSlot, User, LoginCredentials, RegisterData } from '@/lib/types';

// Import both API implementations
import { 
  getAllSlotsFirebase, 
  getSlotByIdFirebase, 
  updateSlotStatusFirebase, 
  initializeParkingSlotsFirebase,
  loginUserFirebase,
  registerUserFirebase
} from '@/lib/api-firebase';

// Backend API implementation
import { apiClient } from '@/lib/http';
import { BackendSlotStatus, BackendHoldRequest, BackendHoldResponse } from '@/lib/types';
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';

/**
 * Get all parking slots - Firebase or Backend implementation
 */
export async function getAllSlots(): Promise<ParkingSlot[]> {
  if (DATABASE_TYPE === 'firebase') {
    return getAllSlotsFirebase();
  } else {
    // Use backend implementation
    try {
      const backendSlots: BackendSlotStatus[] = await apiClient.get('/v1/edge/slots');
      
      // Transform backend data to frontend format
      return backendSlots.map(slot => ({
        id: slot.slot_id,
        status: slot.occupied ? 'Occupied' : 'Free',
        confidence: slot.confidence,
        vehicleType: slot.vehicle_type,
        lastSeen: slot.last_seen,
        reservedUntil: slot.reserved_until,
        predictedFreeMinutes: slot.predicted_free_minutes,
        predictionConfidence: slot.prediction_confidence,
        occupiedSince: slot.last_seen // Use last_seen as occupiedSince for now
      }));
    } catch (error) {
      console.error('Error getting all slots from backend:', error);
      // Return empty array instead of throwing error
      return [];
    }
  }
}

/**
 * Get a specific parking slot by ID - Firebase or Backend implementation
 */
export async function getSlotById(id: string): Promise<ParkingSlot | null> {
  if (DATABASE_TYPE === 'firebase') {
    return getSlotByIdFirebase(id);
  } else {
    // Use backend implementation
    try {
      const backendSlots: BackendSlotStatus[] = await apiClient.get('/v1/edge/slots');
      const backendSlot = backendSlots.find(slot => slot.slot_id === id);
      
      if (backendSlot) {
        return {
          id: backendSlot.slot_id,
          status: backendSlot.occupied ? 'Occupied' : 'Free',
          confidence: backendSlot.confidence,
          vehicleType: backendSlot.vehicle_type,
          lastSeen: backendSlot.last_seen,
          reservedUntil: backendSlot.reserved_until,
          predictedFreeMinutes: backendSlot.predicted_free_minutes,
          predictionConfidence: backendSlot.prediction_confidence,
          occupiedSince: backendSlot.last_seen
        };
      }
      
      return null;
    } catch (error) {
      console.error(`Error getting slot ${id} from backend:`, error);
      // Return null instead of throwing error
      return null;
    }
  }
}

/**
 * Update a parking slot status - Firebase or Backend implementation
 */
export async function updateSlotStatus(id: string, status: 'Free' | 'Occupied'): Promise<void> {
  if (DATABASE_TYPE === 'firebase') {
    return updateSlotStatusFirebase(id, status);
  } else {
    // For backend, this endpoint requires an API key used by edge devices
    // For user actions, we'd typically use the booking system
    console.warn('Direct slot status update requires edge API key. Using booking system instead for user actions.');
    console.log(`Slot ${id} status update requested: ${status}`);
  }
}

/**
 * Initialize parking slots - Firebase or Backend implementation
 */
export async function initializeParkingSlots(): Promise<void> {
  if (DATABASE_TYPE === 'firebase') {
    return initializeParkingSlotsFirebase();
  } else {
    // Backend initialization is handled separately via backend scripts
    console.log('Note: Backend parking slots initialization handled by backend scripts');
    console.log('Run: docker-compose exec backend python -m app.scripts.seed_slots');
  }
}

/**
 * Hold a parking slot - only available in backend implementation
 */
export async function holdSlot(request: BackendHoldRequest): Promise<BackendHoldResponse> {
  if (DATABASE_TYPE !== 'firebase') {
    try {
      const response: BackendHoldResponse = await apiClient.post('/v1/bookings/hold', request);
      return response;
    } catch (error) {
      console.error(`Error holding slot ${request.slot_id}:`, error);
      throw new Error(`Failed to hold parking slot ${request.slot_id}`);
    }
  } else {
    throw new Error('Slot holding is only available with backend database');
  }
}

/**
 * Get prediction for a parking slot - only available in backend implementation
 */
export async function getSlotPrediction(slotId: string): Promise<any> {
  if (DATABASE_TYPE !== 'firebase') {
    try {
      const response = await apiClient.get(`/v1/predictions/${slotId}`);
      return response;
    } catch (error) {
      console.error(`Error getting prediction for slot ${slotId}:`, error);
      throw new Error(`Failed to get prediction for parking slot ${slotId}`);
    }
  } else {
    throw new Error('Slot predictions are only available with backend database');
  }
}

/**
 * User login - using Firebase Auth for both implementations
 */
export async function loginUser(credentials: LoginCredentials): Promise<{ user: User, token: string }> {
  // Both implementations use Firebase Auth for user authentication
  return loginUserFirebase(credentials.email, credentials.password);
}

/**
 * User registration - using Firebase Auth for both implementations
 */
export async function registerUser(userData: RegisterData): Promise<{ user: User, token: string }> {
  // Both implementations use Firebase Auth for user authentication
  return registerUserFirebase(userData.name, userData.email, userData.password);
}