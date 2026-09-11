import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SyncStatus, ReportServerStatus } from '../types';

interface StatusBadgeProps {
  status: SyncStatus | ReportServerStatus | string;
  size?: 'small' | 'medium';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'small' }) => {
  const getStyle = () => {
    switch (status) {
      case 'PENDING_SYNC':
      case 'PENDING SYNC':
        return {
          bg: '#451a03',
          border: '#f59e0b',
          text: '#fbbf24',
          label: 'PENDING SYNC',
        };
      case 'SYNCING':
        return {
          bg: '#172554',
          border: '#3b82f6',
          text: '#60a5fa',
          label: 'SYNCING...',
        };
      case 'SENT':
        return {
          bg: '#052e16',
          border: '#22c55e',
          text: '#4ade80',
          label: 'TRANSMITTED',
        };
      case 'PENDING REVIEW':
      case 'PENDING_REVIEW':
        return {
          bg: '#1e1b4b',
          border: '#818cf8',
          text: '#a5b4fc',
          label: 'PENDING REVIEW',
        };
      case 'VERIFIED':
      case 'ACTIONED':
      case 'RESOLVED':
        return {
          bg: '#064e3b',
          border: '#10b981',
          text: '#34d399',
          label: status,
        };
      case 'FAILED':
      case 'REJECTED':
        return {
          bg: '#450a0a',
          border: '#ef4444',
          text: '#f87171',
          label: status,
        };
      default:
        return {
          bg: '#1e293b',
          border: '#475569',
          text: '#cbd5e1',
          label: status,
        };
    }
  };

  const badge = getStyle();
  const isSmall = size === 'small';

  return (
    <View
      style={[
        styles.badge,
        { backgroundColor: badge.bg, borderColor: badge.border },
        isSmall ? styles.badgeSmall : styles.badgeMedium,
      ]}
    >
      <View style={[styles.dot, { backgroundColor: badge.text }]} />
      <Text style={[styles.label, { color: badge.text }, isSmall && styles.labelSmall]}>
        {badge.label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  badgeSmall: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    gap: 4,
  },
  badgeMedium: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    gap: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  label: {
    fontFamily: 'System',
    fontWeight: '700',
    fontSize: 11,
    letterSpacing: 0.5,
  },
  labelSmall: {
    fontSize: 10,
  },
});
