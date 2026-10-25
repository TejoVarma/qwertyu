import axios from 'axios';
import {
  HealthStatus,
  DayAheadDecisionResponse,
  MonthlyAccuracyMetrics,
  DailySummaryItem,
  ProcurementAdvisorResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  async getHealth(): Promise<HealthStatus> {
    const { data } = await client.get<HealthStatus>('/health');
    return data;
  },

  async getDayAheadDecision(deliveryDate: string, cutoffHour: number = 11): Promise<DayAheadDecisionResponse> {
    const { data } = await client.get<DayAheadDecisionResponse>('/decision/day-ahead', {
      params: {
        delivery_date: deliveryDate,
        cutoff_hour: cutoffHour,
      },
    });
    return data;
  },

  async getMonthlyEvaluation(
    startDate: string = '2026-01-01',
    endDate: string = '2026-01-31',
    cutoffHour: number = 11
  ): Promise<MonthlyAccuracyMetrics> {
    const { data } = await client.get<MonthlyAccuracyMetrics>('/evaluation/monthly', {
      params: {
        start_date: startDate,
        end_date: endDate,
        cutoff_hour: cutoffHour,
      },
    });
    return data;
  },

  async getDailyLog(
    startDate: string = '2026-01-01',
    endDate: string = '2026-01-31',
    cutoffHour: number = 11
  ): Promise<DailySummaryItem[]> {
    const { data } = await client.get<DailySummaryItem[]>('/evaluation/daily-log', {
      params: {
        start_date: startDate,
        end_date: endDate,
        cutoff_hour: cutoffHour,
      },
    });
    return data;
  },

  async calculateProcurementAdvice(payload: {
    delivery_date: string;
    cutoff_hour: number;
    risk_tolerance: number;
    peak_demand_mw: number;
  }): Promise<ProcurementAdvisorResponse> {
    const { data } = await client.post<ProcurementAdvisorResponse>('/procurement/advisor', payload);
    return data;
  },
};
