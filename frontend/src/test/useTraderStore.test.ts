import { describe, it, expect, beforeEach } from 'vitest';
import { useTraderStore } from '../store/useTraderStore';

describe('useTraderStore', () => {
  beforeEach(() => {
    // Reset store to defaults before each test
    useTraderStore.setState({
      selectedDate: '2026-01-15',
      cutoffHour: 11,
      riskTolerance: 1.0,
      peakDemandMw: 38000.0,
      activeTab: 'decision',
      decisionData: null,
      monthlyData: null,
      procurementData: null,
      health: null,
      isLoading: false,
      error: null,
    });
  });

  it('initializes with default energy market parameters', () => {
    const state = useTraderStore.getState();
    expect(state.selectedDate).toBe('2026-01-15');
    expect(state.cutoffHour).toBe(11);
    expect(state.riskTolerance).toBe(1.0);
    expect(state.peakDemandMw).toBe(38000.0);
    expect(state.activeTab).toBe('decision');
  });

  it('updates selected delivery date', () => {
    useTraderStore.getState().setSelectedDate('2026-01-22');
    expect(useTraderStore.getState().selectedDate).toBe('2026-01-22');
  });

  it('updates gate closure cutoff hour', () => {
    useTraderStore.getState().setCutoffHour(14);
    expect(useTraderStore.getState().cutoffHour).toBe(14);
  });

  it('updates risk tolerance scaling factor', () => {
    useTraderStore.getState().setRiskTolerance(1.5);
    expect(useTraderStore.getState().riskTolerance).toBe(1.5);
  });

  it('updates peak consumer demand', () => {
    useTraderStore.getState().setPeakDemandMw(45000.0);
    expect(useTraderStore.getState().peakDemandMw).toBe(45000.0);
  });

  it('switches active navigation tabs', () => {
    useTraderStore.getState().setActiveTab('procurement');
    expect(useTraderStore.getState().activeTab).toBe('procurement');

    useTraderStore.getState().setActiveTab('monthly');
    expect(useTraderStore.getState().activeTab).toBe('monthly');
  });
});
