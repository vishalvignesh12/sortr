import { ParkingSlot, User } from '@/lib/types';
import { 
  collection, 
  getDocs, 
  getDoc, 
  doc, 
  updateDoc,
  setDoc,
  query,
  where,
  orderBy,
  limit,
  Timestamp,
  serverTimestamp,
  addDoc
} from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth';

const SLOTS_COLLECTION = 'parkingSlots';
const USERS_COLLECTION = 'users';

/**
 * Get all parking slots from Firebase
 */
export async function getAllSlotsFirebase(): Promise<ParkingSlot[]> {
  try {
    const slotsQuery = query(
      collection(db, SLOTS_COLLECTION),
      orderBy('id')
    );
    
    const querySnapshot = await getDocs(slotsQuery);
    const slots: ParkingSlot[] = [];
    
    querySnapshot.forEach((doc) => {
      const data = doc.data();
      slots.push({
        id: doc.id,
        status: data.status as 'Free' | 'Occupied',
        occupiedSince: data.occupiedSince ? (data.occupiedSince as Timestamp).toDate().toISOString() : undefined,
        confidence: data.confidence,
        vehicleType: data.vehicle_type,
        lastSeen: data.last_seen ? (data.last_seen as Timestamp).toDate().toISOString() : undefined,
        reservedUntil: data.reserved_until ? (data.reserved_until as Timestamp).toDate().toISOString() : undefined,
        predictedFreeMinutes: data.predicted_free_minutes,
        predictionConfidence: data.prediction_confidence
      });
    });
    
    return slots;
  } catch (error) {
    console.error('Error getting all slots:', error);
    throw new Error('Failed to fetch parking slots from database');
  }
}

/**
 * Get a specific parking slot by ID
 */
export async function getSlotByIdFirebase(id: string): Promise<ParkingSlot | null> {
  try {
    const slotDoc = await getDoc(doc(db, SLOTS_COLLECTION, id));
    
    if (slotDoc.exists()) {
      const data = slotDoc.data();
      return {
        id: slotDoc.id,
        status: data.status as 'Free' | 'Occupied',
        occupiedSince: data.occupiedSince ? (data.occupiedSince as Timestamp).toDate().toISOString() : undefined,
        confidence: data.confidence,
        vehicleType: data.vehicle_type,
        lastSeen: data.last_seen ? (data.last_seen as Timestamp).toDate().toISOString() : undefined,
        reservedUntil: data.reserved_until ? (data.reserved_until as Timestamp).toDate().toISOString() : undefined,
        predictedFreeMinutes: data.predicted_free_minutes,
        predictionConfidence: data.prediction_confidence
      };
    }
    
    return null;
  } catch (error) {
    console.error(`Error getting slot ${id}:`, error);
    throw new Error(`Failed to fetch parking slot ${id} from database`);
  }
}

/**
 * Update a parking slot status
 */
export async function updateSlotStatusFirebase(id: string, status: 'Free' | 'Occupied'): Promise<void> {
  try {
    const slotRef = doc(db, SLOTS_COLLECTION, id);
    const updateData: { status: string; occupiedSince?: Date } = { status };
    
    if (status === 'Occupied') {
      updateData.occupiedSince = serverTimestamp();
    } else {
      // When becoming free, remove occupiedSince
      updateData.occupiedSince = null;
    }
    
    await updateDoc(slotRef, updateData);
  } catch (error) {
    console.error(`Error updating slot ${id}:`, error);
    throw new Error(`Failed to update parking slot ${id}`);
  }
}

/**
 * Initialize parking slots if they don't exist
 */
export async function initializeParkingSlotsFirebase(): Promise<void> {
  try {
    // Check if slots already exist
    const snapshot = await getDocs(collection(db, SLOTS_COLLECTION));
    
    if (snapshot.empty) {
      // Create parking slots A-001 through C-050
      const levels = ['A', 'B', 'C'];
      const slotsPerLevel = 50;
      
      for (const level of levels) {
        for (let i = 1; i <= slotsPerLevel; i++) {
          const slotId = `${level}-${String(i).padStart(3, '0')}`;
          const isOccupied = Math.random() > 0.6; // Approximately 40% occupancy rate
          
          const slotData = {
            id: slotId,
            status: isOccupied ? 'Occupied' : 'Free',
            occupiedSince: isOccupied ? serverTimestamp() : null,
            createdAt: serverTimestamp(),
            level: level,
            number: i,
            confidence: 0.95,
            vehicle_type: Math.random() > 0.5 ? 'car' : 'truck',
          };
          
          await setDoc(doc(db, SLOTS_COLLECTION, slotId), slotData);
        }
      }
      
      console.log('Parking slots initialized successfully');
    } else {
      console.log('Parking slots already exist, skipping initialization');
    }
  } catch (error) {
    console.error('Error initializing parking slots:', error);
    throw new Error('Failed to initialize parking slots');
  }
}

/**
 * User login using Firebase Auth
 */
export async function loginUserFirebase(email: string, password: string): Promise<{ user: User, token: string }> {
  try {
    const auth = getAuth();
    const userCredential = await signInWithEmailAndPassword(
      auth, 
      email, 
      password
    );
    
    const user = userCredential.user;
    
    // Create a user object compatible with the frontend
    const userData: User = {
      id: user.uid,
      name: user.displayName || email.split('@')[0],
      email: user.email || email,
      role: 'user' // Default role, could be fetched from custom claims
    };
    
    // Get ID token for any backend API calls that might still be needed
    const token = await user.getIdToken();
    
    return { user: userData, token };
  } catch (error) {
    console.error('Login error:', error);
    throw new Error(error.message || 'Failed to login');
  }
}

/**
 * User registration using Firebase Auth
 */
export async function registerUserFirebase(name: string, email: string, password: string): Promise<{ user: User, token: string }> {
  try {
    const auth = getAuth();
    const userCredential = await createUserWithEmailAndPassword(
      auth,
      email,
      password
    );
    
    // Update the display name
    await userCredential.user.updateProfile({
      displayName: name
    });
    
    const user = userCredential.user;
    
    // Create a user object compatible with the frontend
    const returnUser: User = {
      id: user.uid,
      name: name,
      email: user.email || email,
      role: 'user' // Default role
    };
    
    // Get ID token 
    const token = await user.getIdToken();
    
    // Add user data to Firestore
    await setDoc(doc(db, USERS_COLLECTION, user.uid), {
      name: name,
      email: email,
      createdAt: serverTimestamp(),
    });
    
    return { user: returnUser, token };
  } catch (error) {
    console.error('Registration error:', error);
    throw new Error(error.message || 'Failed to register');
  }
}

/**
 * User logout
 */
export async function logoutUserFirebase(): Promise<void> {
  try {
    const auth = getAuth();
    await signOut(auth);
  } catch (error) {
    console.error('Logout error:', error);
    throw new Error(error.message || 'Failed to logout');
  }
}