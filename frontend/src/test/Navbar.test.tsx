import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Navbar } from '../components/Navbar';
import { useTraderStore } from '../store/useTraderStore';

describe('Navbar component', () => {
  it('renders branding and market identity correctly', () => {
    useTraderStore.setState({
      selectedDate: '2026-01-15',
      cutoffHour: 11,
      riskTolerance: 1.0,
      activeTab: 'decision',
      health: {
        status: 'ok',
        version: '1.0.0',
        timestamp: '2026-01-15T11:00:00Z',
        database_connected: true,
        actuals_count: 1537,
        forecasts_count: 37376,
      },
    });

    render(<Navbar />);

    expect(screen.getByText('WindProcure')).toBeInTheDocument();
    expect(screen.getByText('GB Day-Ahead')).toBeInTheDocument();
    expect(screen.getByText('37,376 forecasts')).toBeInTheDocument();
  });

  it('renders Gate Closure timestamp and cutoff selector', () => {
    render(<Navbar />);

    expect(screen.getByText(/Decision Cutoff/)).toBeInTheDocument();
    expect(screen.getByDisplayValue('11:00 UTC (Default)')).toBeInTheDocument();
  });

  it('allows clicking between trader navigation tabs', () => {
    render(<Navbar />);

    const procurementTabBtn = screen.getByText('Thermal Procurement Advisor');
    fireEvent.click(procurementTabBtn);
    expect(useTraderStore.getState().activeTab).toBe('procurement');

    const accuracyTabBtn = screen.getByText('Accuracy Lab & Diurnal Heatmap');
    fireEvent.click(accuracyTabBtn);
    expect(useTraderStore.getState().activeTab).toBe('monthly');
  });
});
