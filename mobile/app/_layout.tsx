import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { syncService } from '../src/services/syncService';

export default function RootLayout() {
  useEffect(() => {
    // Initialize background network sync listener
    syncService.init();

    return () => {
      syncService.cleanup();
    };
  }, []);

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: '#0c1220',
          },
          headerTintColor: '#ffffff',
          headerTitleStyle: {
            fontWeight: '800',
            fontSize: 16,
          },
          headerShadowVisible: false,
          contentStyle: {
            backgroundColor: '#070a12',
          },
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen
          name="index"
          options={{
            headerShown: false,
          }}
        />
        <Stack.Screen
          name="sos-confirm"
          options={{
            headerShown: false,
            gestureEnabled: false,
          }}
        />
        <Stack.Screen
          name="report"
          options={{
            title: 'Report Incident',
            headerBackTitle: 'Back',
          }}
        />
        <Stack.Screen
          name="my-reports"
          options={{
            title: 'My Reports & Queue',
            headerBackTitle: 'Home',
          }}
        />
        <Stack.Screen
          name="services"
          options={{
            title: 'Emergency Services',
            headerBackTitle: 'Home',
          }}
        />
        <Stack.Screen
          name="settings"
          options={{
            title: 'Settings',
            headerBackTitle: 'Home',
          }}
        />
      </Stack>
    </SafeAreaProvider>
  );
}
