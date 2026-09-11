import AsyncStorage from '@react-native-async-storage/async-storage';
import { LocalSOSItem, LocalReportItem, UserSettings, SyncStatus } from '../types';

const SOS_QUEUE_KEY = '@ps20_sos_queue';
const REPORTS_QUEUE_KEY = '@ps20_reports_queue';
const SETTINGS_KEY = '@ps20_settings';

export const storageService = {
  // --- Settings ---
  async getSettings(): Promise<UserSettings> {
    try {
      const data = await AsyncStorage.getItem(SETTINGS_KEY);
      if (data) {
        return JSON.parse(data);
      }
    } catch (e) {
      console.warn('Error reading settings from storage:', e);
    }
    return {
      reporter_name: '',
      emergency_contact: '',
      custom_api_url: '',
    };
  },

  async saveSettings(settings: UserSettings): Promise<void> {
    try {
      await AsyncStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch (e) {
      console.error('Error saving settings to storage:', e);
    }
  },

  // --- SOS Queue ---
  async getSOSQueue(): Promise<LocalSOSItem[]> {
    try {
      const data = await AsyncStorage.getItem(SOS_QUEUE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.warn('Error reading SOS queue:', e);
      return [];
    }
  },

  async saveSOSQueue(queue: LocalSOSItem[]): Promise<void> {
    try {
      await AsyncStorage.setItem(SOS_QUEUE_KEY, JSON.stringify(queue));
    } catch (e) {
      console.error('Error saving SOS queue:', e);
    }
  },

  async addSOSItem(item: LocalSOSItem): Promise<void> {
    const queue = await this.getSOSQueue();
    // Prepend newest item
    const updated = [item, ...queue.filter((q) => q.local_id !== item.local_id)];
    await this.saveSOSQueue(updated);
  },

  async updateSOSStatus(
    local_id: string,
    sync_status: SyncStatus,
    patch?: { incident_id?: string; server_id?: string; error_message?: string }
  ): Promise<void> {
    const queue = await this.getSOSQueue();
    const updated = queue.map((item) => {
      if (item.local_id === local_id) {
        return {
          ...item,
          sync_status,
          ...(patch?.incident_id ? { incident_id: patch.incident_id } : {}),
          ...(patch?.server_id ? { server_id: patch.server_id } : {}),
          ...(patch?.error_message !== undefined ? { error_message: patch.error_message } : {}),
        };
      }
      return item;
    });
    await this.saveSOSQueue(updated);
  },

  // --- Reports Queue ---
  async getReportsQueue(): Promise<LocalReportItem[]> {
    try {
      const data = await AsyncStorage.getItem(REPORTS_QUEUE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.warn('Error reading Reports queue:', e);
      return [];
    }
  },

  async saveReportsQueue(queue: LocalReportItem[]): Promise<void> {
    try {
      await AsyncStorage.setItem(REPORTS_QUEUE_KEY, JSON.stringify(queue));
    } catch (e) {
      console.error('Error saving Reports queue:', e);
    }
  },

  async addReportItem(item: LocalReportItem): Promise<void> {
    const queue = await this.getReportsQueue();
    const updated = [item, ...queue.filter((q) => q.local_id !== item.local_id)];
    await this.saveReportsQueue(updated);
  },

  async updateReportStatus(
    local_id: string,
    sync_status: SyncStatus,
    patch?: { server_id?: string; server_status?: string; error_message?: string }
  ): Promise<void> {
    const queue = await this.getReportsQueue();
    const updated = queue.map((item) => {
      if (item.local_id === local_id) {
        return {
          ...item,
          sync_status,
          ...(patch?.server_id ? { server_id: patch.server_id } : {}),
          ...(patch?.server_status ? { server_status: patch.server_status } : {}),
          ...(patch?.error_message !== undefined ? { error_message: patch.error_message } : {}),
        };
      }
      return item;
    });
    await this.saveReportsQueue(updated);
  },
};
