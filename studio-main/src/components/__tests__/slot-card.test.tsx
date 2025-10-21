import { render, screen } from '@testing-library/react';
import { SlotCard } from '@/components/slot-card';
import { ParkingSlot } from '@/lib/types';

describe('SlotCard', () => {
  const mockSlot: ParkingSlot = {
    id: 'A-001',
    status: 'Free',
    occupiedSince: undefined,
  };

  it('renders slot ID correctly', () => {
    render(<SlotCard slot={mockSlot} now={new Date()} />);
    expect(screen.getByText('A-001')).toBeInTheDocument();
  });

  it('shows Free status', () => {
    render(<SlotCard slot={mockSlot} now={new Date()} />);
    expect(screen.getByText('Free')).toBeInTheDocument();
    const statusElement = screen.getByText('Free');
    expect(statusElement).toHaveClass('font-semibold');
  });

  it('shows Occupied status', () => {
    const occupiedSlot: ParkingSlot = {
      ...mockSlot,
      status: 'Occupied',
      occupiedSince: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    };

    render(<SlotCard slot={occupiedSlot} now={new Date()} />);
    expect(screen.getByText('Occupied')).toBeInTheDocument();
    const statusElement = screen.getByText('Occupied');
    expect(statusElement).toHaveClass('font-semibold');
  });

  it('displays occupied duration when slot is occupied', () => {
    const occupiedSlot: ParkingSlot = {
      ...mockSlot,
      status: 'Occupied',
      occupiedSince: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
    };

    render(<SlotCard slot={occupiedSlot} now={new Date()} />);
    // The component now shows "2 hours" instead of "2h 0m" due to date-fns formatting
    expect(screen.getByText('2 hours')).toBeInTheDocument();
  });
});