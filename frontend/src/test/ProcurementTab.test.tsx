import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import React from 'react';
import { ProcurementTab } from '../components/ProcurementTab';
import { useTraderStore } from '../store/useTraderStore';
import { ProcurementAdvisorResponse } from '../types';

vi.mock('recharts', async () => {
  const actual = await vi.importActual<any>('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }: any) => <div data-testid="recharts-container">{children}</div>,
  };
});

describe('ProcurementTab component', () => {
  it('renders loading state when procurement data is missing', () => {
    useTraderStore.setState({ procurementData: null });
    render(<ProcurementTab />);
    expect(screen.getByText('Loading procurement advisor data...')).toBeInTheDocument();
  });

  it('renders interactive sliders and updates peak demand and risk tolerance', async () => {
    const mockProcurement: ProcurementAdvisorResponse = {
      delivery_date: '2026-01-15',
      decision_cutoff_used: '2026-01-14T11:00:00Z',
      buffer_history_start: '2026-01-01',
      buffer_history_end: '2026-01-13',
      peak_consumer_demand_mw: 38000.0,
      risk_tolerance_coefficient: 1.0,
      risk_tolerance_label: 'P90 Standard Risk',
      total_consumer_demand_mwh: 760000.0,
      total_expected_wind_mwh: 280000.0,
      total_recommended_thermal_procurement_mwh: 500000.0,
      total_thermal_safety_reserve_mwh: 20000.0,
      average_thermal_buffer_mw: 833.0,
      schedule: [
        {
          settlement_period: 35,
          time_label: '17:00',
          consumer_demand_mw: 37620.0,
          wind_forecast_mw: 8966.0,
          actual_wind_mw: 8266.0,
          net_demand_mw: 28654.0,
          thermal_safety_buffer_mw: 700.0,
          recommended_thermal_target_mw: 29354.0,
          curtailment_spill_risk_mw: 0.0,
        },
      ],
    };

    useTraderStore.setState({
      procurementData: mockProcurement,
      peakDemandMw: 38000.0,
      riskTolerance: 1.0,
    });

    render(<ProcurementTab />);

    expect(screen.getByText('Procurement Hedging Parameters')).toBeInTheDocument();
    expect(screen.getByText('38,000 MW')).toBeInTheDocument();
    expect(screen.getByText('1.00x')).toBeInTheDocument();

    const sliders = screen.getAllByRole('slider');
    await act(async () => {
      fireEvent.change(sliders[0], { target: { value: '42000' } });
    });
    expect(useTraderStore.getState().peakDemandMw).toBe(42000);

    const updatedSliders = screen.getAllByRole('slider');
    await act(async () => {
      fireEvent.change(updatedSliders[1], { target: { value: '1.5' } });
    });
    expect(useTraderStore.getState().riskTolerance).toBe(1.5);
  });
});
