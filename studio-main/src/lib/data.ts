import type { ParkingSlot } from '@/lib/types';
import type { BackendHoldResponse, BackendPredictionResponse } from '@/lib/types';
import { getAllSlots as apiGetAllSlots, getSlotById as apiGetSlotById, holdSlot as apiHoldSlot, getSlotPrediction as apiGetSlotPrediction } from '@/lib/api';

export const getSlots = async (): Promise<ParkingSlot[]> => {
  try {
    // Fetch real data from backend API
    const slots = await apiGetAllSlots();
    return slots;
  } catch (error) {
    console.error('Error fetching slots:', error);
    // Return mock data when backend is unavailable
    console.log('Backend unavailable, returning mock data');
    return generateMockSlots();
  }
};

// Generate mock parking slots when backend is unavailable
function generateMockSlots(): ParkingSlot[] {
  const mockSlots: ParkingSlot[] = [];
  const levels = ['A', 'B', 'C'];
  const slotsPerLevel = 10;
  
  for (const level of levels) {
    for (let i = 1; i <= slotsPerLevel; i++) {
      const slotId = `${level}-${String(i).padStart(3, '0')}`;
      const isOccupied = Math.random() > 0.6; // Approximately 40% occupancy rate
      
      mockSlots.push({
        id: slotId,
        status: isOccupied ? 'Occupied' : 'Free',
        confidence: 0.95,
        vehicleType: Math.random() > 0.5 ? 'car' : 'truck',
        lastSeen: new Date().toISOString(),
        occupiedSince: isOccupied ? new Date().toISOString() : undefined,
        predictedFreeMinutes: Math.floor(Math.random() * 60),
        predictionConfidence: 0.8
      });
    }
  }
  
  return mockSlots;
}

export const getSlot = async (id: string): Promise<ParkingSlot | undefined> => {
  try {
    const slot = await apiGetSlotById(id);
    return slot || undefined;
  } catch (error) {
    console.error(`Error fetching slot ${id}:`, error);
    console.log(`Backend unavailable, returning mock data for slot ${id}`);
    
    // Generate a mock slot when backend is unavailable
    const isOccupied = Math.random() > 0.6;
    return {
      id: id,
      status: isOccupied ? 'Occupied' : 'Free',
      confidence: 0.95,
      vehicleType: Math.random() > 0.5 ? 'car' : 'truck',
      lastSeen: new Date().toISOString(),
      occupiedSince: isOccupied ? new Date().toISOString() : undefined,
      predictedFreeMinutes: Math.floor(Math.random() * 60),
      predictionConfidence: 0.8
    };
  }
};

export const holdParkingSlot = async (slotId: string, holdMinutes: number = 2): Promise<BackendHoldResponse> => {
  try {
    const response = await apiHoldSlot({ slot_id: slotId, hold_minutes: holdMinutes });
    return response;
  } catch (error) {
    console.error(`Error holding slot ${slotId}:`, error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to hold parking slot ${slotId}: ${errorMessage}`);
  }
};

export const getSlotPredictions = async (slotId: string): Promise<BackendPredictionResponse> => {
  try {
    const prediction = await apiGetSlotPrediction(slotId);
    return prediction;
  } catch (error) {
    console.error(`Error getting prediction for slot ${slotId}:`, error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to get prediction for slot ${slotId}: ${errorMessage}`);
  }
};
