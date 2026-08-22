import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface RunRequest {
  filename: string;
  language: string;
  code: string;
}

export interface RunResponse {
  success: boolean;
  stdout: string;
  stderr: string;
  exit_code: number;
  execution_time: number;
  timed_out: boolean;
  error_type?: string;
}

export interface ChangeDetail {
  line?: number;
  before: string;
  after: string;
}

export interface DebugResponse {
  success: boolean;
  original_code: string;
  fixed_code: string;
  error_type?: string;
  error_line?: number;
  root_cause: string;
  fix_explanation: string;
  changes: ChangeDetail[];
  stdout: string;
  stderr: string;
  exit_code: number;
  execution_time: number;
  attempts: number;
  logs: string[];
}

export interface HistoryItem {
  id: string;
  filename: string;
  language: string;
  original_code: string;
  fixed_code?: string;
  stdout: string;
  stderr: string;
  error_type?: string;
  error_line?: number;
  root_cause?: string;
  fix_explanation?: string;
  exit_code: number;
  execution_time: number;
  attempts: number;
  status: string;
  created_at: string;
}

export interface StatsResponse {
  total_executions: number;
  bugs_detected: number;
  bugs_fixed: number;
  success_rate: number;
  recent_activity: HistoryItem[];
}

export const runCode = async (data: RunRequest): Promise<RunResponse> => {
  const response = await api.post<RunResponse>('/run', data);
  return response.data;
};

export const debugCode = async (data: RunRequest): Promise<DebugResponse> => {
  const response = await api.post<DebugResponse>('/debug', data);
  return response.data;
};

export const getStats = async (): Promise<StatsResponse> => {
  const response = await api.get<StatsResponse>('/stats');
  return response.data;
};

export const getHistory = async (): Promise<HistoryItem[]> => {
  const response = await api.get<HistoryItem[]>('/history');
  return response.data;
};

export const deleteHistoryItem = async (id: string): Promise<void> => {
  await api.delete(`/history/${id}`);
};

export const clearHistory = async (): Promise<void> => {
  await api.delete('/history');
};

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};
