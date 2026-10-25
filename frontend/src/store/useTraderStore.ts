import { create } from 'zustand';
import { apiService } from '../services/api';
import {
  DayAheadDecisionResponse,
  MonthlyAccuracyMetrics,
  ProcurementAdvisorResponse,
  HealthStatus,
} from '../types';

export type TabType = 'decision' | 'procurement' | 'monthly' | 'dailylog';

interface TraderStore {
  // Global Trader Parameters
  selectedDate: string;
  cutoffHour: number;
  riskTolerance: number;
  peakDemandMw: number;
  activeTab: TabType;

  // Data Payloads
  decisionData: DayAheadDecisionResponse | null;
  monthlyData: MonthlyAccuracyMetrics | null;
  procurementData: ProcurementAdvisorResponse | null;
  health: HealthStatus | null;

  // UI State
  isLoading: boolean;
  error: string | null;

  // Actions
  setSelectedDate: (date: string) => void;
  setCutoffHour: (hour: number) => void;
  setRiskTolerance: (val: number) => void;
  setPeakDemandMw: (mw: number) => void;
  setActiveTab: (tab: TabType) => void;

  // Async Fetchers
  fetchHealth: () => Promise<void>;
  fetchDecision: () => Promise<void>;
  fetchMonthly: () => Promise<void>;
  fetchProcurement: () => Promise<void>;
  loadAll: () => Promise<void>;
}

export const useTraderStore = create<TraderStore>((set, get) => ({
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

  setSelectedDate: (date) => {
    set({ selectedDate: date });
    get().fetchDecision();
    get().fetchProcurement();
  },

  setCutoffHour: (hour) => {
    set({ cutoffHour: hour });
    get().fetchDecision();
    get().fetchProcurement();
    get().fetchMonthly();
  },

  setRiskTolerance: (val) => {
    set({ riskTolerance: val });
    get().fetchProcurement();
  },

  setPeakDemandMw: (mw) => {
    set({ peakDemandMw: mw });
    get().fetchProcurement();
  },

  setActiveTab: (tab) => set({ activeTab: tab }),

  fetchHealth: async () => {
    try {
      const health = await apiService.getHealth();
      set({ health });
    } catch (err: any) {
      console.warn('Health check warning:', err.message);
    }
  },

  fetchDecision: async () => {
    const { selectedDate, cutoffHour } = get();
    set({ isLoading: true, error: null });
    try {
      const decisionData = await apiService.getDayAheadDecision(selectedDate, cutoffHour);
      set({ decisionData, isLoading: false });
    } catch (err: any) {
      set({ error: err.response?.data?.detail || err.message, isLoading: false });
    }
  },

  fetchMonthly: async () => {
    const { cutoffHour } = get();
    try {
      const monthlyData = await apiService.getMonthlyEvaluation('2026-01-01', '2026-01-31', cutoffHour);
      set({ monthlyData });
    } catch (err: any) {
      console.error('Failed to fetch monthly data:', err);
    }
  },

  fetchProcurement: async () => {
    const { selectedDate, cutoffHour, riskTolerance, peakDemandMw } = get();
    try {
      const procurementData = await apiService.calculateProcurementAdvice({
        delivery_date: selectedDate,
        cutoff_hour: cutoffHour,
        risk_tolerance: riskTolerance,
        peak_demand_mw: peakDemandMw,
      });
      set({ procurementData });
    } catch (err: any) {
      console.error('Failed to fetch procurement advice:', err);
    }
  },

  loadAll: async () => {
    set({ isLoading: true, error: null });
    await Promise.all([
      get().fetchHealth(),
      get().fetchDecision(),
      get().fetchMonthly(),
      get().fetchProcurement(),
    ]);
    set({ isLoading: false });
  },
}));
