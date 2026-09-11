import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import {
  RefreshCw,
  AlertCircle,
  Radio,
  FileText,
  MapPin,
  Clock,
  CheckCircle2,
  Users,
} from 'lucide-react-native';
import { storageService } from '../src/services/storage';
import { syncService } from '../src/services/syncService';
import { StatusBadge } from '../src/components/StatusBadge';
import { LocalSOSItem, LocalReportItem } from '../src/types';

type CombinedItem =
  | { type: 'SOS'; data: LocalSOSItem }
  | { type: 'REPORT'; data: LocalReportItem };

export default function MyReportsScreen() {
  const [items, setItems] = useState<CombinedItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'SENT'>('ALL');

  const loadLocalData = useCallback(async () => {
    try {
      setLoading(true);
      const [sosList, reportsList] = await Promise.all([
        storageService.getSOSQueue(),
        storageService.getReportsQueue(),
      ]);

      const combined: CombinedItem[] = [
        ...sosList.map((s) => ({ type: 'SOS' as const, data: s })),
        ...reportsList.map((r) => ({ type: 'REPORT' as const, data: r })),
      ];

      // Sort by newest first
      combined.sort(
        (a, b) => new Date(b.data.created_at).getTime() - new Date(a.data.created_at).getTime()
      );

      setItems(combined);
    } catch (err: any) {
      console.warn('Failed to load local reports:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLocalData();
    syncService.syncAllPending().then(() => loadLocalData());

    // Subscribe to sync changes
    const unsubscribe = syncService.subscribe((syncing) => {
      setIsSyncing(syncing);
      loadLocalData();
    });

    return unsubscribe;
  }, [loadLocalData]);

  // Retry Sync Action
  const handleRetrySync = async () => {
    setIsSyncing(true);
    try {
      const result = await syncService.syncAllPending();
      await loadLocalData();
      if (result.errors > 0) {
        Alert.alert(
          'Sync Incomplete',
          `${result.sosSynced + result.reportsSynced} items synced, but ${result.errors} item(s) could not reach the server.`
        );
      } else if (result.sosSynced + result.reportsSynced > 0) {
        Alert.alert(
          'Sync Successful',
          `Successfully synchronized ${result.sosSynced + result.reportsSynced} item(s) with the Command Center.`
        );
      } else {
        Alert.alert('Sync Status', 'All items are already synchronized.');
      }
    } catch (e: any) {
      Alert.alert('Sync Error', e.message || 'Failed to complete synchronization.');
    } finally {
      setIsSyncing(false);
    }
  };

  // Filter items
  const filteredItems = items.filter((item) => {
    if (filter === 'PENDING') {
      return item.data.sync_status === 'PENDING_SYNC' || item.data.sync_status === 'FAILED';
    }
    if (filter === 'SENT') {
      return item.data.sync_status === 'SENT';
    }
    return true;
  });

  const pendingCount = items.filter(
    (i) => i.data.sync_status === 'PENDING_SYNC' || i.data.sync_status === 'FAILED'
  ).length;

  const renderItem = ({ item }: { item: CombinedItem }) => {
    const isSOS = item.type === 'SOS';
    const rawData = item.data;
    const createdAt = new Date(rawData.created_at).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: 'short',
    });

    if (isSOS) {
      const sos = rawData as LocalSOSItem;
      const incidentId = sos.incident_id || `SOS-${sos.local_id.slice(-4).toUpperCase()}`;

      return (
        <View style={[styles.card, styles.cardSOS]}>
          <View style={styles.cardHeader}>
            <View style={styles.badgeGroup}>
              <View style={styles.sosTypePill}>
                <Radio size={14} color="#ef4444" />
                <Text style={styles.sosTypeText}>SOS BEACON</Text>
              </View>
              <Text style={styles.incidentIdText}>{incidentId}</Text>
            </View>
            <StatusBadge status={sos.sync_status} />
          </View>

          <View style={styles.cardBody}>
            <View style={styles.metaRow}>
              <MapPin size={14} color="#94a3b8" />
              <Text style={styles.metaText}>
                {sos.payload.latitude.toFixed(4)}°, {sos.payload.longitude.toFixed(4)}° (±
                {Math.round(sos.payload.accuracy || 10)}m)
              </Text>
            </View>

            <View style={styles.metaRow}>
              <Clock size={14} color="#94a3b8" />
              <Text style={styles.metaText}>{createdAt}</Text>
            </View>

            {sos.error_message && (
              <View style={styles.errorBox}>
                <AlertCircle size={14} color="#f87171" />
                <Text style={styles.errorText}>{sos.error_message}</Text>
              </View>
            )}
          </View>
        </View>
      );
    }

    const report = rawData as LocalReportItem;
    const reportIncidentId = report.server_id
      ? `REP-${report.server_id.slice(0, 6).toUpperCase()}`
      : `LOCAL-${report.local_id.slice(-4).toUpperCase()}`;

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.badgeGroup}>
            <View style={styles.reportTypePill}>
              <FileText size={14} color="#38bdf8" />
              <Text style={styles.reportTypeText}>{report.payload.disaster_type}</Text>
            </View>
            <Text style={styles.incidentIdText}>{reportIncidentId}</Text>
          </View>
          <StatusBadge
            status={
              report.sync_status === 'SENT'
                ? report.server_status || 'PENDING REVIEW'
                : report.sync_status
            }
          />
        </View>

        <View style={styles.cardBody}>
          <Text style={styles.reportDesc} numberOfLines={2}>
            {report.payload.description}
          </Text>

          <View style={styles.metaRow}>
            <Users size={14} color="#94a3b8" />
            <Text style={styles.metaText}>
              {report.payload.people_affected} affected · {report.payload.injured_people} injured ·{' '}
              {report.payload.missing_people} missing
            </Text>
          </View>

          <View style={styles.metaRow}>
            <MapPin size={14} color="#94a3b8" />
            <Text style={styles.metaText}>
              {report.payload.latitude.toFixed(4)}°, {report.payload.longitude.toFixed(4)}°
            </Text>
          </View>

          <View style={styles.metaRow}>
            <Clock size={14} color="#94a3b8" />
            <Text style={styles.metaText}>{createdAt}</Text>
          </View>

          {report.error_message && (
            <View style={styles.errorBox}>
              <AlertCircle size={14} color="#f87171" />
              <Text style={styles.errorText}>{report.error_message}</Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Top Controls & Sync Bar */}
      <View style={styles.topBar}>
        <View style={styles.filterRow}>
          <TouchableOpacity
            style={[styles.filterTab, filter === 'ALL' && styles.filterTabActive]}
            onPress={() => setFilter('ALL')}
          >
            <Text style={[styles.filterTabText, filter === 'ALL' && styles.filterTabTextActive]}>
              All ({items.length})
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.filterTab, filter === 'PENDING' && styles.filterTabActive]}
            onPress={() => setFilter('PENDING')}
          >
            <Text
              style={[
                styles.filterTabText,
                filter === 'PENDING' && styles.filterTabTextActive,
                pendingCount > 0 && { color: '#fbbf24' },
              ]}
            >
              Pending ({pendingCount})
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.filterTab, filter === 'SENT' && styles.filterTabActive]}
            onPress={() => setFilter('SENT')}
          >
            <Text style={[styles.filterTabText, filter === 'SENT' && styles.filterTabTextActive]}>
              Sent
            </Text>
          </TouchableOpacity>
        </View>

        {pendingCount > 0 && (
          <TouchableOpacity
            style={[styles.syncBtn, isSyncing && styles.syncBtnDisabled]}
            onPress={handleRetrySync}
            disabled={isSyncing}
            activeOpacity={0.8}
          >
            {isSyncing ? (
              <ActivityIndicator size="small" color="#ffffff" />
            ) : (
              <>
                <RefreshCw size={14} color="#ffffff" />
                <Text style={styles.syncBtnText}>RETRY SYNC ({pendingCount})</Text>
              </>
            )}
          </TouchableOpacity>
        )}
      </View>

      {/* List */}
      {loading ? (
        <View style={styles.centerBox}>
          <ActivityIndicator size="large" color="#ef4444" />
          <Text style={styles.loadingText}>Loading reports queue...</Text>
        </View>
      ) : (
        <FlatList
          data={filteredItems}
          keyExtractor={(item) => item.data.local_id}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={loading}
              onRefresh={async () => {
                await syncService.syncAllPending();
                await loadLocalData();
              }}
              tintColor="#ef4444"
              colors={['#ef4444']}
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyBox}>
              <CheckCircle2 size={40} color="#64748b" />
              <Text style={styles.emptyTitle}>No Emergency Reports Found</Text>
              <Text style={styles.emptySubtitle}>
                {filter === 'PENDING'
                  ? 'All local incident reports are in sync.'
                  : 'You have not triggered any SOS signals or submitted reports yet.'}
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#070a12',
  },
  topBar: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    gap: 10,
  },
  filterRow: {
    flexDirection: 'row',
    gap: 8,
  },
  filterTab: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  filterTabActive: {
    backgroundColor: '#1e293b',
    borderColor: '#38bdf8',
  },
  filterTabText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '700',
  },
  filterTabTextActive: {
    color: '#ffffff',
  },
  syncBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#d97706',
    paddingVertical: 10,
    borderRadius: 8,
  },
  syncBtnDisabled: {
    backgroundColor: '#78350f',
  },
  syncBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  listContent: {
    padding: 16,
    paddingBottom: 40,
    gap: 14,
  },
  card: {
    backgroundColor: '#0f172a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
    padding: 14,
    gap: 10,
  },
  cardSOS: {
    borderColor: 'rgba(239, 68, 68, 0.4)',
    backgroundColor: 'rgba(239, 68, 68, 0.05)',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  badgeGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sosTypePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  sosTypeText: {
    color: '#f87171',
    fontSize: 11,
    fontWeight: '900',
  },
  reportTypePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  reportTypeText: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '800',
  },
  incidentIdText: {
    color: '#cbd5e1',
    fontFamily: 'Courier',
    fontSize: 12,
    fontWeight: '700',
  },
  cardBody: {
    gap: 6,
  },
  reportDesc: {
    color: '#ffffff',
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '500',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '500',
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    padding: 8,
    borderRadius: 6,
    marginTop: 4,
  },
  errorText: {
    color: '#f87171',
    fontSize: 11,
    flex: 1,
  },
  centerBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    color: '#94a3b8',
    fontSize: 13,
  },
  emptyBox: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    gap: 10,
  },
  emptyTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '800',
  },
  emptySubtitle: {
    color: '#64748b',
    fontSize: 13,
    textAlign: 'center',
    maxWidth: 260,
    lineHeight: 18,
  },
});
