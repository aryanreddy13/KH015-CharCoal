import * as Location from 'expo-location';
import { LocationData, LocationLockState } from '../types';

export const locationService = {
  /**
   * Request foreground location permission.
   */
  async requestPermission(): Promise<boolean> {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      return status === 'granted';
    } catch (e) {
      console.warn('Failed to request location permission:', e);
      return false;
    }
  },

  /**
   * Check if location permission is currently granted.
   */
  async hasPermission(): Promise<boolean> {
    try {
      const { status } = await Location.getForegroundPermissionsAsync();
      return status === 'granted';
    } catch (e) {
      return false;
    }
  },

  /**
   * Acquire high-accuracy GPS coordinates.
   * If high accuracy takes too long or fails, fall back to last known location.
   */
  async getCurrentLocation(): Promise<{ data: LocationData | null; state: LocationLockState }> {
    const granted = await this.requestPermission();
    if (!granted) {
      return { data: null, state: 'PERMISSION_DENIED' };
    }

    // 1. Fast check for fresh last known position to prevent stalls
    try {
      const lastKnown = await Location.getLastKnownPositionAsync();
      if (lastKnown && Date.now() - (lastKnown.timestamp || 0) < 60000) {
        return {
          data: {
            latitude: lastKnown.coords.latitude,
            longitude: lastKnown.coords.longitude,
            accuracy: lastKnown.coords.accuracy,
            timestamp: lastKnown.timestamp,
          },
          state: 'LOCKED',
        };
      }
    } catch (e) {
      // continue to live query
    }

    try {
      // 2. Try current position with 3.5s timeout
      const position = await Promise.race([
        Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.Balanced,
        }),
        new Promise<null>((_, reject) =>
          setTimeout(() => reject(new Error('GPS timeout')), 3500)
        ),
      ]);

      if (position && 'coords' in position) {
        return {
          data: {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: position.timestamp,
          },
          state: 'LOCKED',
        };
      }
    } catch (err) {
      console.warn('Location query attempt timed out/failed, falling back to last known:', err);
    }

    // 3. Fallback to any last known position
    try {
      const lastKnown = await Location.getLastKnownPositionAsync();
      if (lastKnown) {
        return {
          data: {
            latitude: lastKnown.coords.latitude,
            longitude: lastKnown.coords.longitude,
            accuracy: lastKnown.coords.accuracy,
            timestamp: lastKnown.timestamp,
          },
          state: 'LOCKED',
        };
      }
    } catch (err) {
      console.warn('Last known location also unavailable:', err);
    }

    return { data: null, state: 'UNAVAILABLE' };
  },

  /**
   * Provide a manual coordinate fallback (e.g. city center or manual input)
   * so emergency reporting is never blocked completely.
   */
  createManualFallback(lat: number = 28.6139, lng: number = 77.2090): LocationData {
    return {
      latitude: lat,
      longitude: lng,
      accuracy: 100.0,
      timestamp: Date.now(),
      isManualFallback: true,
    };
  },
};
