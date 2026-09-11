import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { MapPin, RefreshCw, AlertTriangle, CheckCircle2 } from 'lucide-react-native';
import { LocationData, LocationLockState } from '../types';

interface GPSIndicatorProps {
  location: LocationData | null;
  state: LocationLockState;
  onRefresh?: () => void;
  showCoordinates?: boolean;
}

export const GPSIndicator: React.FC<GPSIndicatorProps> = ({
  location,
  state,
  onRefresh,
  showCoordinates = true,
}) => {
  const getStatusDisplay = () => {
    switch (state) {
      case 'LOCKED':
        return {
          icon: <CheckCircle2 size={16} color="#10b981" />,
          title: 'GPS LOCKED',
          color: '#10b981',
          bg: 'rgba(16, 185, 129, 0.12)',
          border: 'rgba(16, 185, 129, 0.3)',
        };
      case 'ACQUIRING':
        return {
          icon: <ActivityIndicator size="small" color="#38bdf8" />,
          title: 'ACQUIRING GPS SIGNAL...',
          color: '#38bdf8',
          bg: 'rgba(56, 189, 248, 0.12)',
          border: 'rgba(56, 189, 248, 0.3)',
        };
      case 'PERMISSION_DENIED':
        return {
          icon: <AlertTriangle size={16} color="#ef4444" />,
          title: 'LOCATION PERMISSION DENIED',
          color: '#ef4444',
          bg: 'rgba(239, 68, 68, 0.12)',
          border: 'rgba(239, 68, 68, 0.3)',
        };
      case 'MANUAL':
        return {
          icon: <MapPin size={16} color="#f59e0b" />,
          title: 'MANUAL COORDINATES',
          color: '#f59e0b',
          bg: 'rgba(245, 158, 11, 0.12)',
          border: 'rgba(245, 158, 11, 0.3)',
        };
      default:
        return {
          icon: <AlertTriangle size={16} color="#f59e0b" />,
          title: 'LOCATION UNAVAILABLE',
          color: '#f59e0b',
          bg: 'rgba(245, 158, 11, 0.12)',
          border: 'rgba(245, 158, 11, 0.3)',
        };
    }
  };

  const status = getStatusDisplay();

  return (
    <View style={[styles.container, { backgroundColor: status.bg, borderColor: status.border }]}>
      <View style={styles.topRow}>
        <View style={styles.statusGroup}>
          {status.icon}
          <Text style={[styles.statusText, { color: status.color }]}>{status.title}</Text>
        </View>

        {onRefresh && (
          <TouchableOpacity
            style={styles.refreshButton}
            onPress={onRefresh}
            activeOpacity={0.7}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <RefreshCw size={14} color="#94a3b8" />
            <Text style={styles.refreshText}>Retry</Text>
          </TouchableOpacity>
        )}
      </View>

      {showCoordinates && location && (
        <View style={styles.coordRow}>
          <Text style={styles.coordText}>
            {location.latitude.toFixed(4)}°, {location.longitude.toFixed(4)}°
          </Text>
          {location.accuracy !== null && (
            <Text style={styles.accuracyText}>±{Math.round(location.accuracy)}m accuracy</Text>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    gap: 4,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  statusGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  refreshText: {
    fontSize: 11,
    color: '#94a3b8',
    fontWeight: '600',
  },
  coordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 2,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.06)',
  },
  coordText: {
    fontSize: 12,
    color: '#cbd5e1',
    fontFamily: 'Courier',
    fontWeight: '600',
  },
  accuracyText: {
    fontSize: 11,
    color: '#94a3b8',
    fontWeight: '500',
  },
});
