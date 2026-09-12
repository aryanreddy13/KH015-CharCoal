import { SOSPayload, ReportPayload, EmergencyService } from '../types';
import { storageService } from './storage';

const DEFAULT_API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function normalizeUrl(rawUrl: string): string {
  let trimmed = rawUrl.trim().replace(/\/+$/, '');
  if (!trimmed) return 'http://localhost:8000';
  if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
    trimmed = `http://${trimmed}`;
  }
  // If no port specified and not https standard or standard domain with port
  const hasPort = /:\d+$/.test(trimmed);
  if (!hasPort && !trimmed.includes('.com') && !trimmed.includes('.org') && !trimmed.includes('.net') && !trimmed.includes('.gov')) {
    trimmed = `${trimmed}:8000`;
  }
  return trimmed;
}

export const apiService = {
  async getBaseUrl(): Promise<string> {
    try {
      const settings = await storageService.getSettings();
      if (settings.custom_api_url && settings.custom_api_url.trim().length > 0) {
        return normalizeUrl(settings.custom_api_url);
      }
    } catch (e) {
      // fallback
    }
    return normalizeUrl(DEFAULT_API_URL);
  },

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const baseUrl = await this.getBaseUrl();
    const url = `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    console.log(`[Sanjivani API] -> ${options.method || 'GET'} ${url}`);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);

    try {
      const res = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...(options.headers || {}),
        },
      });

      clearTimeout(timeoutId);

      if (!res.ok) {
        let errMessage = `HTTP ${res.status}: ${res.statusText}`;
        try {
          const errData = await res.json();
          if (errData.detail) {
            errMessage = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          // Ignore JSON parse error on non-json error responses
        }
        throw new ApiError(errMessage, res.status);
      }

      return await res.json();
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new ApiError('Network request timed out. Please check your connection.', 408);
      }
      if (err instanceof ApiError) {
        throw err;
      }
      throw new ApiError(err.message || 'Unable to reach Sanjivani emergency server.', 0);
    }
  },

  /**
   * Submit emergency SOS signal.
   */
  async sendSOS(payload: SOSPayload): Promise<{ id: string; incident_id: string; status: string; message: string }> {
    return this.request('/api/sos', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Submit a detailed citizen incident report.
   */
  async sendReport(payload: ReportPayload): Promise<any> {
    return this.request('/api/reports', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Fetch nearby emergency services (Hospitals, Police, Fire & Rescue, NGO) via TomTom & Supabase.
   */
  async getNearbyServices(
    latitude?: number,
    longitude?: number,
    radius?: number,
    type?: string
  ): Promise<EmergencyService[]> {
    const params = new URLSearchParams();
    if (latitude !== undefined) params.append('latitude', String(latitude));
    if (longitude !== undefined) params.append('longitude', String(longitude));
    if (radius !== undefined) params.append('radius', String(radius));
    if (type) params.append('type', type);

    const qs = params.toString();
    const endpoint = `/api/emergency-services/nearby${qs ? `?${qs}` : ''}`;
    const res = await this.request<{ count: number; services: EmergencyService[] }>(endpoint);
    return res.services || [];
  },

  /**
   * Fetch live list of reports from server.
   */
  async getReports(): Promise<any[]> {
    return this.request<any[]>('/api/reports');
  },

  /**
   * Ping backend to check connectivity.
   */
  async checkHealth(): Promise<boolean> {
    try {
      const res = await this.request<{ status: string }>('/api/health');
      return res.status === 'HEALTHY' || res.status === 'ONLINE';
    } catch {
      return false;
    }
  },
};
