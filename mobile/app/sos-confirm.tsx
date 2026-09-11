import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import {
  CheckCircle2,
  AlertCircle,
  MapPin,
  ShieldAlert,
  ArrowLeft,
  PhoneForwarded,
  Info,
} from 'lucide-react-native';
import { EmergencyRoadmap } from '../src/components/EmergencyRoadmap';

export default function SOSConfirmScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    incidentId?: string;
    syncStatus?: string;
    lat?: string;
    lng?: string;
    accuracy?: string;
  }>();

  const incidentId = params.incidentId || 'SOS-7701';
  const isPendingSync = params.syncStatus === 'PENDING_SYNC';
  const lat = params.lat ? parseFloat(params.lat).toFixed(4) : '28.6139';
  const lng = params.lng ? parseFloat(params.lng).toFixed(4) : '77.2090';
  const accuracy = params.accuracy ? Math.round(parseFloat(params.accuracy)) : 10;

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container} bounces={false}>
        {/* Header Icon & Title */}
        <View style={styles.heroSection}>
          <View style={[styles.iconCircle, isPendingSync && styles.iconCircleAmber]}>
            {isPendingSync ? (
              <AlertCircle size={48} color="#fbbf24" />
            ) : (
              <CheckCircle2 size={48} color="#10b981" />
            )}
          </View>

          <Text style={[styles.mainHeading, isPendingSync && { color: '#fbbf24' }]}>
            {isPendingSync ? 'SOS STORED LOCALLY' : 'SOS ACTIVATED'}
          </Text>
          <Text style={styles.subHeading}>
            {isPendingSync
              ? 'Network connection unavailable. Emergency signal queued and will transmit automatically once connection returns.'
              : 'Emergency beacon transmitted directly to Command Center.'}
          </Text>
        </View>

        {/* Details Card */}
        <View style={styles.detailsCard}>
          {/* Incident ID */}
          <View style={styles.row}>
            <Text style={styles.rowLabel}>INCIDENT ID</Text>
            <View style={styles.incidentBadge}>
              <Text style={styles.incidentText}>{incidentId}</Text>
            </View>
          </View>

          {/* Status */}
          <View style={styles.row}>
            <Text style={styles.rowLabel}>SIGNAL STATUS</Text>
            <View style={styles.statusPill}>
              <View
                style={[
                  styles.statusDot,
                  { backgroundColor: isPendingSync ? '#f59e0b' : '#10b981' },
                ]}
              />
              <Text
                style={[
                  styles.statusValue,
                  { color: isPendingSync ? '#fbbf24' : '#34d399' },
                ]}
              >
                {isPendingSync ? 'QUEUED FOR SYNC' : 'AUTHORITY NOTIFIED'}
              </Text>
            </View>
          </View>

          {/* GPS Coordinates */}
          <View style={[styles.row, styles.noBorder]}>
            <Text style={styles.rowLabel}>GPS LOCATION</Text>
            <View style={styles.locationWrap}>
              <MapPin size={14} color="#38bdf8" />
              <Text style={styles.locationText}>
                {lat}°, {lng}° (±{accuracy}m)
              </Text>
            </View>
          </View>
        </View>

        {/* Live Multi-Agency Response Roadmap */}
        <EmergencyRoadmap
          userLat={parseFloat(lat)}
          userLng={parseFloat(lng)}
          incidentId={incidentId}
          isOffline={isPendingSync}
        />

        {/* Emergency Instructions */}
        <View style={styles.guidanceCard}>
          <View style={styles.guidanceHeader}>
            <ShieldAlert size={20} color="#f87171" />
            <Text style={styles.guidanceTitle}>CRITICAL INSTRUCTIONS</Text>
          </View>
          <View style={styles.guidanceList}>
            <Text style={styles.guidanceItem}>
              1. Stay in a safe, elevated, or reinforced location if possible.
            </Text>
            <Text style={styles.guidanceItem}>
              2. Conserve your phone battery; keep the screen off when not in use.
            </Text>
            <Text style={styles.guidanceItem}>
              3. If flood waters are rising, do NOT walk or drive through flowing water.
            </Text>
            <Text style={styles.guidanceItem}>
              4. Leave this app running in the background for continuous tracking.
            </Text>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.btnGroup}>
          <TouchableOpacity
            style={styles.primaryBtn}
            onPress={() => router.push('/my-reports')}
            activeOpacity={0.8}
          >
            <Text style={styles.primaryBtnText}>VIEW ALL MY REPORTS</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.secondaryBtn}
            onPress={() => router.replace('/')}
            activeOpacity={0.8}
          >
            <ArrowLeft size={18} color="#94a3b8" />
            <Text style={styles.secondaryBtnText}>RETURN TO HOME</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#070a12',
  },
  container: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 40,
    gap: 20,
  },
  heroSection: {
    alignItems: 'center',
    gap: 12,
  },
  iconCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderWidth: 2,
    borderColor: '#10b981',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconCircleAmber: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    borderColor: '#f59e0b',
  },
  mainHeading: {
    color: '#ffffff',
    fontSize: 26,
    fontWeight: '900',
    letterSpacing: 1,
    textAlign: 'center',
  },
  subHeading: {
    color: '#94a3b8',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    maxWidth: 320,
  },
  detailsCard: {
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#1e293b',
    borderRadius: 14,
    padding: 16,
    gap: 14,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  noBorder: {
    borderBottomWidth: 0,
    paddingBottom: 0,
  },
  rowLabel: {
    color: '#64748b',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  incidentBadge: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#334155',
  },
  incidentText: {
    color: '#ffffff',
    fontFamily: 'Courier',
    fontWeight: '800',
    fontSize: 14,
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusValue: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  locationWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  locationText: {
    color: '#cbd5e1',
    fontFamily: 'Courier',
    fontSize: 12,
    fontWeight: '600',
  },
  guidanceCard: {
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.25)',
    borderRadius: 14,
    padding: 16,
    gap: 10,
  },
  guidanceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  guidanceTitle: {
    color: '#f87171',
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  guidanceList: {
    gap: 6,
  },
  guidanceItem: {
    color: '#e2e8f0',
    fontSize: 12,
    lineHeight: 18,
  },
  btnGroup: {
    gap: 12,
    marginTop: 8,
  },
  primaryBtn: {
    backgroundColor: '#ef4444',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryBtnText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  secondaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#1e293b',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  secondaryBtnText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '700',
  },
});
