import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { KpiCards } from '../components/KpiCards';
import { useTraderStore } from '../store/useTraderStore';
import { DayAheadDecisionResponse, ProcurementAdvisorResponse } from '../types';

describe('KpiCards component', () => {
  it('renders loading skeleton when data is not ready', () => {
    useTraderStore.setState({
      isLoading: true,
      decisionData: null,
    });

    const { container } = render(<KpiCards />);
    const pulses = container.querySelectorAll('.animate-pulse');
    expect(pulses.length).toBe(4);
  });

  it('renders formatted market metrics when data is available', () => {
    const mockDecision: DayAheadDecisionResponse = {
      delivery_date: '2026-01-15',
      decision_cutoff_used: '2026-01-14T11:00:00Z',
      periods_count: 48,
      day_mae_mw: 1110.2,
      day_rmse_mw: 1228.5,
      day_bias_mw: 555.1,
      normalized_mae_pct: 3.7,
      total_expected_generation_mwh: 280272.0,
      total_actual_generation_mwh: 253626.0,
      volume_imbalance_mwh: 26646.0,
      peak_shortfall_mw: 1226.0,
      p90_shortfall_mw: 1000.0,
      settlement_periods: [],
    };

    const mockProcurement: ProcurementAdvisorResponse = {
      delivery_date: '2026-01-15',
      decision_cutoff_used: '2026-01-14T11:00:00Z',
      peak_consumer_demand_mw: 38000.0,
      risk_tolerance_coefficient: 1.0,
      risk_tolerance_label: 'P90 Standard Risk',
      total_consumer_demand_mwh: 760000.0,
      total_expected_wind_mwh: 280000.0,
      total_recommended_thermal_procurement_mwh: 700000.0,
      total_thermal_safety_reserve_mwh: 15000.0,
      average_thermal_buffer_mw: 625.0,
      schedule: [],
    };

    useTraderStore.setState({
      isLoading: false,
      decisionData: mockDecision,
      procurementData: mockProcurement,
    });

    render(<KpiCards />);

    // Expected Wind Generation
    expect(screen.getByText('Day-Ahead Expected')).toBeInTheDocument();
    expect(screen.getByText(/280,272/)).toBeInTheDocument();

    // Actual Metered Flow & Deficit
    expect(screen.getByText('Actual Metered Flow')).toBeInTheDocument();
    expect(screen.getByText(/253,626/)).toBeInTheDocument();
    expect(screen.getByText(/-26,646 MWh Deficit/)).toBeInTheDocument();

    // MAE Precision
    expect(screen.getByText('Forecast Precision (MAE)')).toBeInTheDocument();
    expect(screen.getByText(/1,110.2/)).toBeInTheDocument();
    expect(screen.getByText(/RMSE: 1228.5 MW/)).toBeInTheDocument();

    // Thermal Safety Hedge
    expect(screen.getByText('Thermal Safety Hedge')).toBeInTheDocument();
    expect(screen.getByText(/\+625/)).toBeInTheDocument();
    expect(screen.getByText(/Over-forecast: Shortfall risk/)).toBeInTheDocument();
  });
});
