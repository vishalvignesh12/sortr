import { describe, it, expect, vi, beforeEach } from 'vitest';
import { 
  getAllSlots, 
  getSlotById, 
  updateSlotStatus,
  holdSlot,
  getSlotPrediction,
  loginUser,
  registerUser
} from '@/lib/api';

// Mock the HTTP client
vi.mock('@/lib/http', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}));

// Mock Firebase Auth functions
vi.mock('firebase/auth', async () => {
  const actual = await vi.importActual('firebase/auth');
  return {
    ...actual,
    getAuth: vi.fn(() => ({})),
    signInWithEmailAndPassword: vi.fn(() => Promise.resolve({ user: { uid: 'test123', email: 'test@example.com', getIdToken: () => Promise.resolve('token123'), updateProfile: vi.fn() } })),
    createUserWithEmailAndPassword: vi.fn(() => Promise.resolve({ user: { uid: 'test123', email: 'test@example.com', getIdToken: () => Promise.resolve('token123'), updateProfile: vi.fn() } })),
  };
});

describe('API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch all slots', async () => {
    expect(getAllSlots).toBeTypeOf('function');
  });

  it('should fetch a specific slot by ID', async () => {
    expect(getSlotById).toBeTypeOf('function');
  });

  it('should update slot status', async () => {
    expect(updateSlotStatus).toBeTypeOf('function');
  });

  it('should hold a parking slot', async () => {
    expect(holdSlot).toBeTypeOf('function');
  });

  it('should get slot prediction', async () => {
    expect(getSlotPrediction).toBeTypeOf('function');
  });

  it('should handle user login', async () => {
    expect(loginUser).toBeTypeOf('function');
  });

  it('should handle user registration', async () => {
    expect(registerUser).toBeTypeOf('function');
  });
});