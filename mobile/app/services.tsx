import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
  Alert,
  RefreshControl,
} from 'react-native';
import {
  Hospital,
  Shield,
  Flame,
  Phone,
  MapPin,
  AlertCircle,
  Building2,
} from 'lucide-react-native';
import { locationService } from '../src/services/location';
import { apiService } from '../src/services/api';
import { EmergencyService, LocationData } from '../src/types';

export default function EmergencyServicesScreen() {
  const [services, setServices] = useState<EmergencyService[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>('ALL');
  const [userLocation, setUserLocation] = useState<LocationData | null>(null);

  const fetchServices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Acquire user coordinates for distance sorting
      const locRes = await locationService.getCurrentLocation();
      const loc = locRes.data;
      setUserLocation(loc);

      const data = await apiService.getNearbyServices(
        loc?.latitude,
        loc?.longitude,
        10000,
        activeFilter === 'ALL' ? undefined : activeFilter
      );

      setServices(data);
    } catch (err: any) {
      console.warn('Failed to fetch emergency services:', err.message);
      setError('Emergency services directory currently unreachable from backend server.');
    } finally {
      setLoading(false);
    }
  }, [activeFilter]);

  useEffect(() => {
    fetchServices();
  }, [fetchServices]);

  const handleCall = async (phoneNumber?: string) => {
    if (!phoneNumber) {
      Alert.alert('Phone Unavailable', 'No direct contact phone number listed for this facility.');
      return;
    }
    const cleanNumber = phoneNumber.replace(/[^0-9+]/g, '');
    const url = `tel:${cleanNumber}`;
    try {
      const canOpen = await Linking.canOpenURL(url);
      if (canOpen) {
        await Linking.openURL(url);
      } else {
        Alert.alert(
          'Emergency Contact Number',
          `Direct Facility Number:\n\n${phoneNumber}\n\nPlease dial this directly from your mobile dialer.`,
          [{ text: 'OK' }]
        );
      }
    } catch {
      Alert.alert(
        'Emergency Contact Number',
        `Direct Facility Number:\n\n${phoneNumber}\n\nPlease dial this directly from your mobile dialer.`,
        [{ text: 'OK' }]
      );
    }
  };

  const getServiceTypeDetails = (type: string) => {
    const t = type.toUpperCase();
    if (t.includes('FIRE')) {
      return {
        label: 'FIRE & RESCUE',
        icon: <Flame size={20} color="#f97316" />,
        bg: 'rgba(249, 115, 22, 0.12)',
        color: '#fb923c',
      };
    }
    if (t.includes('HOSPITAL') || t.includes('MEDIC')) {
      return {
        label: 'HOSPITAL / MEDICAL',
        icon: <Hospital size={20} color="#38bdf8" />,
        bg: 'rgba(56, 189, 248, 0.12)',
        color: '#38bdf8',
      };
    }
    if (t.includes('POLICE')) {
      return {
        label: 'POLICE STATION',
        icon: <Shield size={20} color="#a855f7" />,
        bg: 'rgba(168, 85, 247, 0.12)',
        color: '#c084fc',
      };
    }
    return {
      label: 'GOVERNMENT / RELIEF',
      icon: <Building2 size={20} color="#10b981" />,
      bg: 'rgba(16, 185, 129, 0.12)',
      color: '#34d399',
    };
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

  const renderServiceItem = ({ item }: { item: EmergencyService }) => {
    const typeInfo = getServiceTypeDetails(item.type);
    const isPolice = (item.agency_type || item.type || '').toUpperCase().includes('POLICE');
    const phone = item.phone || item.contact_number;
    const distanceDisplay = item.distance_text || (item.distance_km !== null && item.distance_km !== undefined ? `${item.distance_km} km away` : item.address || 'Operational Sector');
    const etaDisplay = item.eta_text || (item.eta_minutes !== null && item.eta_minutes !== undefined ? `ETA ~${item.eta_minutes} min` : null);

    return (
      <View style={styles.card}>
        <View style={styles.cardTop}>
          <View style={[styles.iconCircle, { backgroundColor: typeInfo.bg }]}>
            {typeInfo.icon}
          </View>
          <View style={styles.headerInfo}>
            <View style={styles.typeBadge}>
              <Text style={[styles.typeText, { color: typeInfo.color }]}>{typeInfo.label}</Text>
            </View>
            <Text style={styles.serviceName}>{item.name}</Text>
          </View>
        </View>

        <View style={styles.cardBottom}>
          <View style={styles.locationGroup}>
            <MapPin size={14} color="#94a3b8" />
            <Text style={styles.distanceText}>{distanceDisplay}</Text>
            {etaDisplay && (
              <Text style={[styles.distanceText, { color: '#38bdf8', fontWeight: '700' }]}>
                • {etaDisplay}
              </Text>
            )}
          </View>

          <View style={{ flexDirection: 'row', gap: 6, alignItems: 'center' }}>
            {!isPolice && phone ? (
              <TouchableOpacity
                style={styles.callButton}
                onPress={() => handleCall(phone)}
                activeOpacity={0.8}
              >
                <Phone size={13} color="#ffffff" />
                <Text style={styles.callButtonText}>{phone}</Text>
              </TouchableOpacity>
            ) : isPolice ? (
              <View style={[styles.callButton, { backgroundColor: 'rgba(129, 140, 248, 0.15)', borderWidth: 1, borderColor: 'rgba(129, 140, 248, 0.3)' }]}>
                <Text style={[styles.callButtonText, { color: '#a5b4fc', fontSize: 10 }]}>PERIMETER</Text>
              </View>
            ) : null}

            <TouchableOpacity
              style={[styles.callButton, { backgroundColor: '#0f172a', borderWidth: 1, borderColor: '#1e293b' }]}
              onPress={() => handleOpenMaps(item.maps_url, item.latitude, item.longitude)}
              activeOpacity={0.8}
            >
              <Text style={[styles.callButtonText, { color: '#38bdf8', fontSize: 11 }]}>MAPS</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Category Filter Chips */}
      <View style={styles.filterBar}>
        {['ALL', 'HOSPITAL', 'POLICE', 'FIRE_RESCUE', 'GOVERNMENT'].map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.filterChip, activeFilter === f && styles.filterChipActive]}
            onPress={() => setActiveFilter(f)}
          >
            <Text
              style={[
                styles.filterChipText,
                activeFilter === f && styles.filterChipTextActive,
              ]}
            >
              {f === 'ALL'
                ? 'All Services'
                : f === 'FIRE_RESCUE'
                ? 'Fire'
                : f.charAt(0) + f.slice(1).toLowerCase()}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.centerBox}>
          <ActivityIndicator size="large" color="#38bdf8" />
          <Text style={styles.loadingText}>Finding nearby supplies...</Text>
        </View>
      ) : error ? (
        <View style={styles.centerBox}>
          <AlertCircle size={44} color="#f59e0b" />
          <Text style={styles.errorTitle}>Live Directory Unavailable</Text>
          <Text style={styles.errorSubtitle}>{error}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={fetchServices}>
            <Text style={styles.retryBtnText}>RETRY LOOKUP</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={services}
          keyExtractor={(item) => item.id}
          renderItem={renderServiceItem}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={loading}
              onRefresh={fetchServices}
              tintColor="#38bdf8"
              colors={['#38bdf8']}
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyBox}>
              <AlertCircle size={40} color="#64748b" />
              <Text style={styles.emptyTitle}>No Services In Search Radius</Text>
              <Text style={styles.emptySubtitle}>
                No verified {activeFilter !== 'ALL' ? activeFilter.toLowerCase() : ''} emergency
                stations found within 50km.
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
  filterBar: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  filterChipActive: {
    backgroundColor: '#1e293b',
    borderColor: '#38bdf8',
  },
  filterChipText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '700',
  },
  filterChipTextActive: {
    color: '#ffffff',
  },
  listContent: {
    padding: 16,
    paddingBottom: 40,
    gap: 12,
  },
  card: {
    backgroundColor: '#0f172a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
    padding: 16,
    gap: 14,
  },
  cardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerInfo: {
    flex: 1,
    gap: 2,
  },
  typeBadge: {
    alignSelf: 'flex-start',
  },
  typeText: {
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  serviceName: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '800',
  },
  cardBottom: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
  },
  locationGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
  },
  distanceText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
  callButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#10b981',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  callButtonText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '800',
  },
  centerBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  loadingText: {
    color: '#94a3b8',
    fontSize: 13,
  },
  errorTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '800',
  },
  errorSubtitle: {
    color: '#94a3b8',
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 18,
  },
  retryBtn: {
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#38bdf8',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 8,
  },
  retryBtnText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '800',
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
    maxWidth: 280,
    lineHeight: 18,
  },
});
