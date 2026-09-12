import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import {
  AlertTriangle,
  FileText,
  Clock,
  PhoneCall,
  Settings,
  Radio,
  WifiOff,
  CheckCircle2,
} from 'lucide-react-native';
import { locationService } from '../src/services/location';
import { storageService } from '../src/services/storage';
import { apiService } from '../src/services/api';
import { syncService } from '../src/services/syncService';
import { GPSIndicator } from '../src/components/GPSIndicator';
import { EmergencyRoadmap } from '../src/components/EmergencyRoadmap';
import { LocationData, LocationLockState, LocalSOSItem } from '../src/types';

export default function HomeScreen() {
  const router = useRouter();

  const [location, setLocation] = useState<LocationData | null>(null);
  const [lockState, setLockState] = useState<LocationLockState>('ACQUIRING');
  const [isSendingSOS, setIsSendingSOS] = useState<boolean>(false);
  const [pendingCount, setPendingCount] = useState<number>(0);

  // Fetch initial location
  const refreshLocation = useCallback(async () => {
    setLockState('ACQUIRING');
    const res = await locationService.getCurrentLocation();
    if (res.data) {
      setLocation(res.data);
      setLockState('LOCKED');
    } else {
      setLockState(res.state);
    }
  }, []);

  useEffect(() => {
    refreshLocation();
  }, [refreshLocation]);

  // Subscribe to queue updates
  useEffect(() => {
    const updateStats = async () => {
      const stats = await syncService.getPendingCount();
      setPendingCount(stats.total);
    };

    updateStats();
    const unsubscribe = syncService.subscribe(() => {
      updateStats();
    });

    return unsubscribe;
  }, []);

  // SOS Trigger Flow
  const handleTriggerSOS = async () => {
    if (isSendingSOS) return;

    setIsSendingSOS(true);

    try {
      // 1. Acquire current GPS
      let activeLocation = location;
      if (!activeLocation || lockState !== 'LOCKED') {
        const res = await locationService.getCurrentLocation();
        if (res.data) {
          activeLocation = res.data;
          setLocation(res.data);
          setLockState('LOCKED');
        } else {
          // Manual safe fallback if hardware GPS cannot be obtained
          activeLocation = locationService.createManualFallback();
          setLocation(activeLocation);
          setLockState('MANUAL');
        }
      }

      // 2. Load reporter settings
      const settings = await storageService.getSettings();
      const localId = `sos_local_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;

      const sosPayload = {
        reporter_name: settings.reporter_name || 'Citizen SOS Beacon',
        contact: settings.emergency_contact || undefined,
        latitude: activeLocation.latitude,
        longitude: activeLocation.longitude,
        accuracy: activeLocation.accuracy ?? 10.0,
        description: 'EMERGENCY SOS BEACON TRIGGERED',
        timestamp: new Date().toISOString(),
      };

      // 3. Attempt direct transmission
      let serverResponse: { id: string; incident_id: string; status: string; message: string } | null = null;
      let syncStatus: 'SENT' | 'PENDING_SYNC' = 'PENDING_SYNC';
      let incidentId = `SOS-${Math.random().toString(36).substring(2, 6).toUpperCase()}`;

      try {
        serverResponse = await apiService.sendSOS(sosPayload);
        syncStatus = 'SENT';
        incidentId = serverResponse.incident_id || incidentId;
      } catch (netErr: any) {
        console.warn('Network transmission failed during SOS, saving to offline queue:', netErr.message);
        syncStatus = 'PENDING_SYNC';
      }

      // 4. Save to local storage (Never silently discard an SOS)
      const localItem: LocalSOSItem = {
        local_id: localId,
        created_at: new Date().toISOString(),
        sync_status: syncStatus,
        payload: sosPayload,
        incident_id: incidentId,
        server_id: serverResponse?.id,
      };
      await storageService.addSOSItem(localItem);

      // 5. Navigate to SOS confirmation screen
      router.replace({
        pathname: '/sos-confirm',
        params: {
          incidentId,
          syncStatus,
          lat: String(activeLocation.latitude),
          lng: String(activeLocation.longitude),
          accuracy: String(activeLocation.accuracy ?? 10),
        },
      });
    } catch (criticalErr: any) {
      Alert.alert(
        'Emergency Signal Error',
        'Could not complete SOS. Please retry immediately or contact local emergency authorities.'
      );
    } finally {
      setIsSendingSOS(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scrollContainer} bounces={false}>
        {/* Top App Header */}
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.badgeText}>SANJIVINI EMERGENCY</Text>
            <Text style={styles.appTitle}>DISASTER ASSISTANCE</Text>
          </View>

          <TouchableOpacity
            style={styles.settingsIconBtn}
            onPress={() => router.push('/settings')}
            activeOpacity={0.7}
          >
            <Settings size={20} color="#94a3b8" />
          </TouchableOpacity>
        </View>

        {/* Offline Queue Notice Banner */}
        {pendingCount > 0 && (
          <TouchableOpacity
            style={styles.offlineBanner}
            onPress={() => router.push('/my-reports')}
            activeOpacity={0.8}
          >
            <WifiOff size={16} color="#fbbf24" />
            <Text style={styles.offlineBannerText}>
              {pendingCount} report{pendingCount > 1 ? 's' : ''} stored offline (Tap to sync)
            </Text>
          </TouchableOpacity>
        )}

        {/* DOMINANT SOS BUTTON SECTION */}
        <View style={styles.sosSection}>
          <View style={styles.haloRingOuter}>
            <View style={styles.haloRingInner}>
              <TouchableOpacity
                style={[styles.sosButton, isSendingSOS && styles.sosButtonDisabled]}
                onPress={handleTriggerSOS}
                disabled={isSendingSOS}
                activeOpacity={0.85}
              >
                {isSendingSOS ? (
                  <ActivityIndicator size="large" color="#ffffff" />
                ) : (
                  <>
                    <Radio size={36} color="#ffffff" style={styles.sosIcon} />
                    <Text style={styles.sosText}>SOS</Text>
                    <Text style={styles.sosSubtext}>PRESS FOR RESCUE</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </View>

          <Text style={styles.sosGuidanceText}>
            Instant high-priority signal broadcasted to disaster command center
          </Text>
        </View>

        {/* GPS STATUS CARD */}
        <View style={styles.gpsContainer}>
          <GPSIndicator
            location={location}
            state={lockState}
            onRefresh={refreshLocation}
            showCoordinates={true}
          />
        </View>

        {/* PRIMARY ACTION BUTTONS */}
        <View style={styles.actionsContainer}>
          {/* Action: Report Incident */}
          <TouchableOpacity
            style={[styles.actionCard, styles.actionCardRed]}
            onPress={() => router.push('/report')}
            activeOpacity={0.8}
          >
            <View style={[styles.actionIconCircle, { backgroundColor: '#450a0a' }]}>
              <AlertTriangle size={24} color="#ef4444" />
            </View>
            <View style={styles.actionInfo}>
              <Text style={styles.actionTitle}>REPORT INCIDENT</Text>
              <Text style={styles.actionDesc}>
                Submit flood, fire, injuries, trapped victims & supplies needed
              </Text>
            </View>
          </TouchableOpacity>

          {/* Action: My Reports & Offline Queue */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => router.push('/my-reports')}
            activeOpacity={0.8}
          >
            <View style={[styles.actionIconCircle, { backgroundColor: '#172554' }]}>
              <FileText size={22} color="#38bdf8" />
            </View>
            <View style={styles.actionInfo}>
              <View style={styles.actionTitleRow}>
                <Text style={styles.actionTitle}>MY REPORTS & QUEUE</Text>
                {pendingCount > 0 && (
                  <View style={styles.pendingPill}>
                    <Text style={styles.pendingPillText}>{pendingCount}</Text>
                  </View>
                )}
              </View>
              <Text style={styles.actionDesc}>Track status of submitted incident reports</Text>
            </View>
          </TouchableOpacity>

          {/* Action: Emergency Services */}
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => router.push('/services')}
            activeOpacity={0.8}
          >
            <View style={[styles.actionIconCircle, { backgroundColor: '#064e3b' }]}>
              <PhoneCall size={22} color="#10b981" />
            </View>
            <View style={styles.actionInfo}>
              <Text style={styles.actionTitle}>EMERGENCY SERVICES</Text>
              <Text style={styles.actionDesc}>Nearby hospitals, police stations & fire rescue</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* LIVE EMERGENCY RESPONSE ROADMAP & NEARBY ALERT RADAR */}
        <EmergencyRoadmap
          userLat={location?.latitude}
          userLng={location?.longitude}
          isOffline={pendingCount > 0}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#070a12',
  },
  scrollContainer: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 36,
    gap: 16,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 4,
  },
  badgeText: {
    color: '#ef4444',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.5,
  },
  appTitle: {
    color: '#ffffff',
    fontSize: 22,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  settingsIconBtn: {
    backgroundColor: '#131b2e',
    padding: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  offlineBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#451a03',
    borderWidth: 1,
    borderColor: '#b45309',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 10,
    gap: 8,
  },
  offlineBannerText: {
    color: '#fef3c7',
    fontSize: 12,
    fontWeight: '700',
  },
  sosSection: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 12,
    gap: 14,
  },
  haloRingOuter: {
    width: 230,
    height: 230,
    borderRadius: 115,
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  haloRingInner: {
    width: 195,
    height: 195,
    borderRadius: 97.5,
    backgroundColor: 'rgba(239, 68, 68, 0.25)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sosButton: {
    width: 165,
    height: 165,
    borderRadius: 82.5,
    backgroundColor: '#dc2626',
    borderWidth: 5,
    borderColor: '#fca5a5',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#ef4444',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.7,
    shadowRadius: 18,
    elevation: 12,
  },
  sosButtonDisabled: {
    backgroundColor: '#991b1b',
    borderColor: '#f87171',
  },
  sosIcon: {
    marginBottom: -4,
  },
  sosText: {
    color: '#ffffff',
    fontSize: 38,
    fontWeight: '900',
    letterSpacing: 2,
  },
  sosSubtext: {
    color: '#fee2e2',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  sosGuidanceText: {
    color: '#94a3b8',
    fontSize: 12,
    textAlign: 'center',
    maxWidth: 280,
    lineHeight: 16,
  },
  gpsContainer: {
    width: '100%',
  },
  actionsContainer: {
    width: '100%',
    gap: 12,
    marginTop: 4,
  },
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#1e293b',
    padding: 16,
    borderRadius: 14,
    gap: 14,
  },
  actionCardRed: {
    borderColor: 'rgba(239, 68, 68, 0.3)',
    backgroundColor: '#111827',
  },
  actionIconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionInfo: {
    flex: 1,
    gap: 2,
  },
  actionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  actionTitle: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  actionDesc: {
    color: '#94a3b8',
    fontSize: 12,
    lineHeight: 16,
  },
  pendingPill: {
    backgroundColor: '#f59e0b',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  pendingPillText: {
    color: '#000000',
    fontSize: 11,
    fontWeight: '900',
  },
});
