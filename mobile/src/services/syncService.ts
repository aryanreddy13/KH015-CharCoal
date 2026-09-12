import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { storageService } from './storage';
import { apiService } from './api';
import { SyncStatus } from '../types';

type SyncListener = (isSyncing: boolean, stats: { sosPending: number; reportsPending: number }) => void;

class SyncService {
  private isSyncing = false;
  private listeners: Set<SyncListener> = new Set();
  private isOnline = true;
  private unsubscribeNetInfo: (() => void) | null = null;
  private syncTimer: any = null;

  init() {
    if (this.unsubscribeNetInfo) {
      return;
    }

    // Subscribe to network changes
    this.unsubscribeNetInfo = NetInfo.addEventListener((state: NetInfoState) => {
      const connected = Boolean(state.isConnected);
      this.isOnline = connected;

      if (connected) {
        console.log('[Sanjivini SyncService] Network connected. Syncing pending items...');
        this.syncAllPending();
      }
    });

    // Run immediate sync check
    this.syncAllPending();

    // Background recurring sync pulse every 12 seconds
    if (!this.syncTimer) {
      this.syncTimer = setInterval(() => {
        this.syncAllPending();
      }, 12000);
    }
  }

  cleanup() {
    if (this.unsubscribeNetInfo) {
      this.unsubscribeNetInfo();
      this.unsubscribeNetInfo = null;
    }
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
  }

  subscribe(listener: SyncListener): () => void {
    this.listeners.add(listener);
    this.notifyListeners();
    return () => {
      this.listeners.delete(listener);
    };
  }

  private async notifyListeners() {
    try {
      const sosQueue = await storageService.getSOSQueue();
      const reportsQueue = await storageService.getReportsQueue();

      const sosPending = sosQueue.filter((s) => s.sync_status === 'PENDING_SYNC' || s.sync_status === 'SYNCING').length;
      const reportsPending = reportsQueue.filter((r) => r.sync_status === 'PENDING_SYNC' || r.sync_status === 'SYNCING').length;

      this.listeners.forEach((listener) => {
        try {
          listener(this.isSyncing, { sosPending, reportsPending });
        } catch (e) {
          console.warn('Error in sync listener:', e);
        }
      });
    } catch {
      // ignore
    }
  }

  async getPendingCount(): Promise<{ sosCount: number; reportsCount: number; total: number }> {
    const sosQueue = await storageService.getSOSQueue();
    const reportsQueue = await storageService.getReportsQueue();
    const sosCount = sosQueue.filter((s) => s.sync_status === 'PENDING_SYNC' || s.sync_status === 'FAILED').length;
    const reportsCount = reportsQueue.filter((r) => r.sync_status === 'PENDING_SYNC' || r.sync_status === 'FAILED').length;
    return { sosCount, reportsCount, total: sosCount + reportsCount };
  }

  /**
   * Synchronize all pending SOS beacons and incident reports.
   * Uses client-generated local_id to prevent duplicates.
   */
  async syncAllPending(): Promise<{ sosSynced: number; reportsSynced: number; errors: number }> {
    if (this.isSyncing) {
      return { sosSynced: 0, reportsSynced: 0, errors: 0 };
    }

    this.isSyncing = true;
    this.notifyListeners();

    let sosSynced = 0;
    let reportsSynced = 0;
    let errors = 0;

    try {
      // 1. Process SOS Queue (Highest Priority)
      const sosQueue = await storageService.getSOSQueue();
      const pendingSOS = sosQueue.filter(
        (item) => item.sync_status === 'PENDING_SYNC' || item.sync_status === 'FAILED'
      );

      for (const item of pendingSOS) {
        try {
          await storageService.updateSOSStatus(item.local_id, 'SYNCING');
          this.notifyListeners();

          const response = await apiService.sendSOS(item.payload);
          await storageService.updateSOSStatus(item.local_id, 'SENT', {
            incident_id: response.incident_id,
            server_id: response.id,
          });
          sosSynced++;
        } catch (err: any) {
          console.warn(`[Sanjivini SyncService] SOS item ${item.local_id} sync failed:`, err.message);
          await storageService.updateSOSStatus(item.local_id, 'FAILED', {
            error_message: err.message || 'Sync failed',
          });
          errors++;
        }
      }

      // 2. Process Reports Queue
      const reportsQueue = await storageService.getReportsQueue();
      const pendingReports = reportsQueue.filter(
        (item) => item.sync_status === 'PENDING_SYNC' || item.sync_status === 'FAILED'
      );

      for (const item of pendingReports) {
        try {
          await storageService.updateReportStatus(item.local_id, 'SYNCING');
          this.notifyListeners();

          const response = await apiService.sendReport(item.payload);
          await storageService.updateReportStatus(item.local_id, 'SENT', {
            server_id: response.id,
            server_status: response.status || 'PENDING REVIEW',
          });
          reportsSynced++;
        } catch (err: any) {
          console.warn(`[Sanjivini SyncService] Report item ${item.local_id} sync failed:`, err.message);
          await storageService.updateReportStatus(item.local_id, 'FAILED', {
            error_message: err.message || 'Sync failed',
          });
          errors++;
        }
      }
    } finally {
      this.isSyncing = false;
      this.notifyListeners();
    }

    return { sosSynced, reportsSynced, errors };
  }
}

export const syncService = new SyncService();
