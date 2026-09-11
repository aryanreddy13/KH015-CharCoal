import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Linking,
  ActivityIndicator,
  Animated,
  Alert,
} from 'react-native';
import {
  Shield,
  Flame,
  Hospital,
  HeartHandshake,
  Phone,
  MapPin,
  Clock,
  Radio,
  Navigation,
  AlertTriangle,
  RefreshCw,
  Boxes,
} from 'lucide-react-native';
import { apiService } from '../services/api';
import { EmergencyService } from '../types';

interface RoadmapProps {
  userLat?: number;
  userLng?: number;
  incidentId?: string;
  isOffline?: boolean;
}

interface CategoryConfig {
  key: string;
  agencyType: 'POLICE' | 'FIRE_RESCUE' | 'HOSPITAL' | 'NGO';
  title: string;
  role: string;
  color: string;
  bgColor: string;
  borderColor: string;
  icon: (color: string) => React.ReactNode;
}

const CATEGORY_CONFIGS: CategoryConfig[] = [
  {
    key: 'police',
    agencyType: 'POLICE',
    title: 'POLICE CONTROL & SECURITY',
    role: 'Perimeter cordon, road clearing & traffic escort',
    color: '#818cf8',
    bgColor: 'rgba(99, 102, 241, 0.12)',
    borderColor: 'rgba(99, 102, 241, 0.3)',
    icon: (col) => <Shield size={20} color={col} />,
  },
  {
    key: 'fire',
    agencyType: 'FIRE_RESCUE',
    title: 'FIRE & WATER RESCUE',
    role: 'Flood boats, victim extrication & heavy rescue',
    color: '#f97316',
    bgColor: 'rgba(249, 115, 22, 0.12)',
    borderColor: 'rgba(249, 115, 22, 0.3)',
    icon: (col) => <Flame size={20} color={col} />,
  },
  {
    key: 'hospital',
    agencyType: 'HOSPITAL',
    title: 'EMERGENCY TRAUMA / ICU',
    role: 'Triage ambulance & emergency paramedic response',
    color: '#38bdf8',
    bgColor: 'rgba(56, 189, 248, 0.12)',
    borderColor: 'rgba(56, 189, 248, 0.3)',
    icon: (col) => <Hospital size={20} color={col} />,
  },
  {
    key: 'ngo',
    agencyType: 'NGO',
    title: 'DISASTER RELIEF HUB',
    role: 'Ready rations, clean drinking water & emergency tents',
    color: '#34d399',
    bgColor: 'rgba(52, 211, 153, 0.12)',
    borderColor: 'rgba(52, 211, 153, 0.3)',
    icon: (col) => <HeartHandshake size={20} color={col} />,
  },
];

export const EmergencyRoadmap: React.FC<RoadmapProps> = ({
  userLat,
  userLng,
  incidentId,
  isOffline = false,
}) => {
  const [services, setServices] = useState<EmergencyService[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [pulseAnim] = useState(new Animated.Value(1));

  useEffect(() => {
    // Pulse animation for radar active effect
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.08,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [pulseAnim]);

  const loadNearby = useCallback(async () => {
    if (userLat === undefined || userLng === undefined) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getNearbyServices(userLat, userLng, 10000);
      setServices(data || []);
    } catch (err: any) {
      setError('Live emergency locations unavailable');
    } finally {
      setLoading(false);
    }
  }, [userLat, userLng]);

  useEffect(() => {
    loadNearby();
  }, [loadNearby]);

  const handleCall = async (number?: string) => {
    if (!number) return;
    const cleanNumber = number.replace(/[^0-9+]/g, '');
    const url = `tel:${cleanNumber}`;
    try {
      const canOpen = await Linking.canOpenURL(url);
      if (canOpen) {
        await Linking.openURL(url);
      } else {
        Alert.alert(
          'Emergency Contact Number',
          `Direct Facility Number:\n\n${number}\n\nPlease dial this directly from your mobile dialer.`,
          [{ text: 'OK' }]
        );
      }
    } catch {
      Alert.alert(
        'Emergency Contact Number',
        `Direct Facility Number:\n\n${number}\n\nPlease dial this directly from your mobile dialer.`,
        [{ text: 'OK' }]
      );
    }
  };

  const handleOpenMaps = (mapsUrl?: string, lat?: number | null, lng?: number | null) => {
    if (mapsUrl) {
      Linking.openURL(mapsUrl).catch(() => {});
      return;
    }
    if (lat !== undefined && lat !== null && lng !== undefined && lng !== null) {
      const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
      Linking.openURL(url).catch(() => {});
    }
  };

  // State 1: GPS Unavailable
  if (userLat === undefined || userLng === undefined) {
    return (
      <View style={styles.container}>
        <View style={styles.headerRow}>
          <View style={styles.headerLeft}>
            <View style={[styles.radarBadge, { borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.15)' }]}>
              <AlertTriangle size={14} color="#f59e0b" />
            </View>
            <View>
              <Text style={styles.title}>EMERGENCY RESPONSE ROADMAP</Text>
              <Text style={[styles.subtitle, { color: '#fbbf24' }]}>Live location unavailable</Text>
            </View>
          </View>
        </View>
        <View style={styles.stateContainer}>
          <Text style={styles.stateText}>
            Enable GPS permissions to discover real nearby Police, Fire, Hospital and Relief facilities.
          </Text>
        </View>
      </View>
    );
  }

  // State 2: Loading State
  if (loading && services.length === 0) {
    return (
      <View style={styles.container}>
        <View style={styles.headerRow}>
          <View style={styles.headerLeft}>
            <Animated.View style={[styles.radarBadge, { transform: [{ scale: pulseAnim }] }]}>
              <Radio size={14} color="#ef4444" />
            </Animated.View>
            <View>
              <Text style={styles.title}>EMERGENCY RESPONSE ROADMAP</Text>
              <Text style={styles.subtitle}>Finding nearby supplies...</Text>
            </View>
          </View>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color="#38bdf8" />
          <Text style={styles.loadingText}>Finding nearby supplies...</Text>
        </View>
      </View>
    );
  }

  // State 3: Error / Offline with no services
  if (error && services.length === 0) {
    return (
      <View style={styles.container}>
        <View style={styles.headerRow}>
          <View style={styles.headerLeft}>
            <View style={[styles.radarBadge, { borderColor: '#ef4444' }]}>
              <AlertTriangle size={14} color="#ef4444" />
            </View>
            <View>
              <Text style={styles.title}>EMERGENCY RESPONSE ROADMAP</Text>
              <Text style={[styles.subtitle, { color: '#f87171' }]}>{error}</Text>
            </View>
          </View>
          <TouchableOpacity onPress={loadNearby} style={styles.retryBtn}>
            <RefreshCw size={14} color="#94a3b8" />
          </TouchableOpacity>
        </View>
        <View style={styles.stateContainer}>
          <Text style={styles.stateText}>
            Emergency SOS beacons remain active. Nearby facility routing will refresh automatically.
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header with Live Alert Radar */}
      <View style={styles.headerRow}>
        <View style={styles.headerLeft}>
          <Animated.View style={[styles.radarBadge, { transform: [{ scale: pulseAnim }] }]}>
            <Radio size={14} color="#ef4444" />
          </Animated.View>
          <View>
            <Text style={styles.title}>EMERGENCY RESPONSE ROADMAP</Text>
            <Text style={styles.subtitle}>
              {isOffline
                ? 'Offline Mode: Local Emergency Routing'
                : 'Live Supplies & Multi-Agency Dispatch'}
            </Text>
          </View>
        </View>
        <TouchableOpacity onPress={loadNearby} style={styles.retryBtn} activeOpacity={0.7}>
          <RefreshCw size={14} color="#94a3b8" />
        </TouchableOpacity>
      </View>

      {/* Progress Line & Station Steps */}
      <View style={styles.timeline}>
        {CATEGORY_CONFIGS.map((config, idx) => {
          // Find matching real service for this category from backend
          const match = services.find((s) => {
            const st = (s.agency_type || s.type || '').toUpperCase();
            if (config.agencyType === 'POLICE' && st.includes('POLICE')) return true;
            if (config.agencyType === 'FIRE_RESCUE' && st.includes('FIRE')) return true;
            if (config.agencyType === 'HOSPITAL' && (st.includes('HOSPITAL') || st.includes('MEDIC'))) return true;
            if (config.agencyType === 'NGO' && (st.includes('NGO') || st.includes('RELIEF') || st.includes('GOV'))) return true;
            return false;
          });

          const isLast = idx === CATEGORY_CONFIGS.length - 1;
          const facilityName = match?.name || `${config.title} (Scanning)`;
          const distanceDisplay = match?.distance_text || (match?.distance_km !== undefined && match?.distance_km !== null ? `${match.distance_km.toFixed(1)} km away` : 'Locating...');
          const etaDisplay = match?.eta_text || (match?.eta_minutes !== undefined && match?.eta_minutes !== null ? `ETA ~${match.eta_minutes} min` : 'Calculating ETA...');
          const phone = match?.phone || match?.contact_number;
          const mapsUrl = match?.maps_url;
          const stockInfo = match?.available_resources && match.available_resources.length > 0 ? match.available_resources[0] : null;

          return (
            <View key={config.key} style={styles.stepContainer}>
              {/* Left Timeline Column */}
              <View style={styles.timelineColumn}>
                <View style={[styles.stepCircle, { backgroundColor: config.bgColor, borderColor: config.color }]}>
                  {config.icon(config.color)}
                </View>
                {!isLast && <View style={[styles.timelineLine, { borderColor: config.color }]} />}
              </View>

              {/* Right Content Card */}
              <View style={[styles.card, { borderColor: config.borderColor }]}>
                {/* Top Row: Title & Status */}
                <View style={styles.cardHeader}>
                  <View style={styles.cardTitleWrap}>
                    <Text style={[styles.stationTitle, { color: config.color }]}>{config.title}</Text>
                    <Text style={styles.stationName} numberOfLines={1}>{facilityName}</Text>
                  </View>
                  <View style={[styles.statusBadge, { backgroundColor: isOffline ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)' }]}>
                    <View style={[styles.statusDot, { backgroundColor: isOffline ? '#f59e0b' : '#10b981' }]} />
                    <Text style={[styles.statusText, { color: isOffline ? '#fbbf24' : '#34d399' }]}>
                      {match?.is_registered_provider ? 'REGISTERED' : 'LIVE'}
                    </Text>
                  </View>
                </View>

                {/* Role Description */}
                <Text style={styles.roleText}>{config.role}</Text>

                {/* Metrics Row: Real Distance & Real Traffic ETA */}
                <View style={styles.metricsRow}>
                  <View style={styles.metricItem}>
                    <MapPin size={13} color="#94a3b8" />
                    <Text style={styles.metricText}>{distanceDisplay}</Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Clock size={13} color="#38bdf8" />
                    <Text style={[styles.metricText, { color: '#38bdf8', fontWeight: '700' }]}>
                      {etaDisplay}
                    </Text>
                  </View>
                </View>

                {/* Registered Resource Inventory Stock Badge if Available */}
                {stockInfo && (
                  <View style={styles.stockBadge}>
                    <Boxes size={12} color="#10b981" />
                    <Text style={styles.stockText}>
                      Stock: {stockInfo.available_quantity} {stockInfo.unit} Available ({stockInfo.name})
                    </Text>
                  </View>
                )}

                {/* Quick Action Buttons */}
                <View style={styles.actionsRow}>
                  {config.agencyType === 'POLICE' ? (
                    // Police Policy: No auto phone calls
                    <View style={styles.pagerDutyBadge}>
                      <Text style={styles.pagerDutyText}>PERIMETER ESCORT & CORDON</Text>
                    </View>
                  ) : phone ? (
                    <TouchableOpacity
                      style={styles.callBtn}
                      onPress={() => handleCall(phone)}
                      activeOpacity={0.7}
                    >
                      <Phone size={13} color="#ffffff" />
                      <Text style={styles.callBtnText}>CALL: {phone}</Text>
                    </TouchableOpacity>
                  ) : (
                    <View style={styles.unavailableBadge}>
                      <Text style={styles.unavailableText}>PHONE UNAVAILABLE</Text>
                    </View>
                  )}

                  <TouchableOpacity
                    style={styles.mapsBtn}
                    onPress={() => handleOpenMaps(mapsUrl, match?.latitude, match?.longitude)}
                    activeOpacity={0.7}
                  >
                    <Navigation size={13} color="#38bdf8" />
                    <Text style={styles.mapsBtnText}>MAPS</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#0f172a',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
    padding: 16,
    gap: 16,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  retryBtn: {
    padding: 6,
    borderRadius: 6,
    backgroundColor: '#1e293b',
  },
  radarBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderWidth: 1,
    borderColor: '#ef4444',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  subtitle: {
    color: '#94a3b8',
    fontSize: 11,
    marginTop: 2,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 16,
    justifyContent: 'center',
  },
  loadingText: {
    color: '#94a3b8',
    fontSize: 12,
  },
  stateContainer: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  stateText: {
    color: '#64748b',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
  timeline: {
    gap: 12,
  },
  stepContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  timelineColumn: {
    alignItems: 'center',
    width: 36,
  },
  stepCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2,
  },
  timelineLine: {
    flex: 1,
    width: 2,
    borderLeftWidth: 2,
    borderStyle: 'dashed',
    marginVertical: 4,
    opacity: 0.4,
  },
  card: {
    flex: 1,
    backgroundColor: '#070a12',
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    gap: 8,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 8,
  },
  cardTitleWrap: {
    flex: 1,
  },
  stationTitle: {
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  stationName: {
    color: '#f8fafc',
    fontSize: 13,
    fontWeight: '700',
    marginTop: 2,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  roleText: {
    color: '#cbd5e1',
    fontSize: 11,
    lineHeight: 15,
  },
  metricsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    paddingVertical: 4,
  },
  metricItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metricText: {
    color: '#94a3b8',
    fontSize: 11,
  },
  stockBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.25)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  stockText: {
    color: '#34d399',
    fontSize: 10,
    fontWeight: '700',
  },
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 2,
  },
  callBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderRadius: 6,
    gap: 6,
  },
  callBtnText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '700',
  },
  pagerDutyBadge: {
    flex: 1,
    backgroundColor: 'rgba(129, 140, 248, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(129, 140, 248, 0.3)',
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pagerDutyText: {
    color: '#a5b4fc',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  unavailableBadge: {
    flex: 1,
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  unavailableText: {
    color: '#64748b',
    fontSize: 10,
    fontWeight: '700',
  },
  mapsBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#1e293b',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 6,
    gap: 4,
  },
  mapsBtnText: {
    color: '#38bdf8',
    fontSize: 10,
    fontWeight: '700',
  },
});
