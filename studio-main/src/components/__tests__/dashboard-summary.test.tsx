import { render, screen } from '@testing-library/react';
import { DashboardSummary } from '@/components/dashboard-summary';
import { describe, it, expect } from 'vitest';

describe('DashboardSummary', () => {
  it('renders dashboard summary charts', () => {
    render(<DashboardSummary />);
    
    // Check if the main chart titles are present
    expect(screen.getByText('Weekly Occupancy Trend')).toBeInTheDocument();
    expect(screen.getByText('Monthly Revenue')).toBeInTheDocument();
  });

  it('renders without crashing', () => {
    const { container } = render(<DashboardSummary />);
    expect(container).toBeTruthy();
  });
});