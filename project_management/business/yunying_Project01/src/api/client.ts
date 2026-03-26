import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_URL,
});

export interface Report {
  id: string;
  title: string;
  period_start: string;
  period_end: string;
  created_at: string;
  status: string;
  progress?: number;
  total_rows?: number;
  processed_rows?: number;
  file_path?: string;
  html_content?: string;
  price_analysis?: any[];
  supply_demand_analysis?: any[];
  profit_analysis?: any[];
}

export const uploadFile = async (file: File, type: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', type);
  const response = await api.post('/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const generateReport = async (data: {
  title: string;
  period_start: string;
  period_end: string;
  products?: string[];
  custom_prompt?: string;
}) => {
  const response = await api.post<Report>('/reports/generate', {
    ...data,
    products: data.products || [],
    custom_prompt: data.custom_prompt
  });
  return response.data;
};

export const getReport = async (id: string) => {
  const response = await api.get<Report>(`/reports/${id}`);
  return response.data;
};

export const listReports = async () => {
  const response = await api.get<Report[]>('/reports/');
  return response.data;
};
