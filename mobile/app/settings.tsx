import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import {
  User,
  Phone,
  Server,
  Save,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  HelpCircle,
} from 'lucide-react-native';
import { storageService } from '../src/services/storage';
import { apiService } from '../src/services/api';
import { UserSettings } from '../src/types';

export default function SettingsScreen() {
  const [reporterName, setReporterName] = useState('');
  const [emergencyContact, setEmergencyContact] = useState('');
  const [customApiUrl, setCustomApiUrl] = useState('');
  const [showDeveloperSection, setShowDeveloperSection] = useState(false);

  const [saving, setSaving] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);

  // Load existing settings
  useEffect(() => {
    const load = async () => {
      const s = await storageService.getSettings();
      setReporterName(s.reporter_name || '');
      setEmergencyContact(s.emergency_contact || '');
      setCustomApiUrl(s.custom_api_url || '');
    };
    load();
  }, []);

  // Save Settings
  const handleSave = async () => {
    setSaving(true);
    try {
      const updated: UserSettings = {
        reporter_name: reporterName.trim(),
        emergency_contact: emergencyContact.trim(),
        custom_api_url: customApiUrl.trim(),
      };
      await storageService.saveSettings(updated);
      Alert.alert('Settings Saved', 'Your emergency profile and preferences have been updated.');
    } catch (e: any) {
      Alert.alert('Error', 'Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  // Test Server Connection
  const handleTestConnection = async () => {
    setTestingConnection(true);
    setTestResult(null);
    try {
      // Save temporary url if user entered one
      if (customApiUrl.trim()) {
        await storageService.saveSettings({
          reporter_name: reporterName,
          emergency_contact: emergencyContact,
          custom_api_url: customApiUrl.trim(),
        });
      }

      const isHealthy = await apiService.checkHealth();
      if (isHealthy) {
        setTestResult({
          ok: true,
          message: 'Connected successfully to Sanjivini Command Server!',
        });
      } else {
        setTestResult({
          ok: false,
          message: 'Server responded, but system health check failed.',
        });
      }
    } catch (err: any) {
      setTestResult({
        ok: false,
        message: err.message || 'Could not connect to server at this address.',
      });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleResetDefaultUrl = async () => {
    setCustomApiUrl('');
    await storageService.saveSettings({
      reporter_name: reporterName,
      emergency_contact: emergencyContact,
      custom_api_url: '',
    });
    setTestResult(null);
    Alert.alert('Reset', 'Server URL reset to environment default.');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Profile Section */}
      <View style={styles.section}>
        <Text style={styles.sectionHeader}>CITIZEN PROFILE</Text>
        <Text style={styles.sectionSubtitle}>
          These details are automatically attached to your emergency SOS beacons and reports.
        </Text>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>REPORTER FULL NAME</Text>
          <View style={styles.inputWrap}>
            <User size={18} color="#94a3b8" />
            <TextInput
              style={styles.input}
              placeholder="e.g. John Doe / Citizen"
              placeholderTextColor="#64748b"
              value={reporterName}
              onChangeText={setReporterName}
            />
          </View>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>EMERGENCY CONTACT NUMBER</Text>
          <View style={styles.inputWrap}>
            <Phone size={18} color="#94a3b8" />
            <TextInput
              style={styles.input}
              placeholder="e.g. +91 98765 43210"
              placeholderTextColor="#64748b"
              keyboardType="phone-pad"
              value={emergencyContact}
              onChangeText={setEmergencyContact}
            />
          </View>
        </View>
      </View>

      {/* Save Button */}
      <TouchableOpacity
        style={[styles.saveBtn, saving && styles.saveBtnDisabled]}
        onPress={handleSave}
        disabled={saving}
        activeOpacity={0.8}
      >
        {saving ? (
          <ActivityIndicator size="small" color="#ffffff" />
        ) : (
          <>
            <Save size={18} color="#ffffff" />
            <Text style={styles.saveBtnText}>SAVE PROFILE</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Advanced / Developer Configuration Section */}
      <View style={styles.devSection}>
        <TouchableOpacity
          style={styles.devToggle}
          onPress={() => setShowDeveloperSection(!showDeveloperSection)}
          activeOpacity={0.7}
        >
          <View style={styles.devToggleLeft}>
            <Server size={18} color="#94a3b8" />
            <Text style={styles.devToggleTitle}>Advanced / Developer Network Config</Text>
          </View>
          {showDeveloperSection ? (
            <ChevronUp size={18} color="#94a3b8" />
          ) : (
            <ChevronDown size={18} color="#94a3b8" />
          )}
        </TouchableOpacity>

        {showDeveloperSection && (
          <View style={styles.devBody}>
            <View style={styles.infoBanner}>
              <HelpCircle size={16} color="#38bdf8" />
              <Text style={styles.infoBannerText}>
                Default: Uses EXPO_PUBLIC_API_URL. When testing on physical devices on Wi-Fi, use
                your computer LAN IP (e.g. http://192.168.1.100:8000).
              </Text>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>CUSTOM BACKEND URL OVERRIDE</Text>
              <TextInput
                style={styles.inputDev}
                placeholder="http://192.168.x.x:8000"
                placeholderTextColor="#64748b"
                autoCapitalize="none"
                autoCorrect={false}
                value={customApiUrl}
                onChangeText={setCustomApiUrl}
              />
            </View>

            <View style={styles.devBtnRow}>
              <TouchableOpacity
                style={styles.testBtn}
                onPress={handleTestConnection}
                disabled={testingConnection}
                activeOpacity={0.8}
              >
                {testingConnection ? (
                  <ActivityIndicator size="small" color="#38bdf8" />
                ) : (
                  <Text style={styles.testBtnText}>TEST CONNECTION</Text>
                )}
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.resetBtn}
                onPress={handleResetDefaultUrl}
                activeOpacity={0.8}
              >
                <Text style={styles.resetBtnText}>RESET TO DEFAULT</Text>
              </TouchableOpacity>
            </View>

            {testResult && (
              <View
                style={[
                  styles.testResultBox,
                  testResult.ok ? styles.testResultOk : styles.testResultErr,
                ]}
              >
                {testResult.ok ? (
                  <CheckCircle2 size={16} color="#10b981" />
                ) : (
                  <AlertCircle size={16} color="#f87171" />
                )}
                <Text
                  style={[
                    styles.testResultText,
                    testResult.ok ? { color: '#34d399' } : { color: '#f87171' },
                  ]}
                >
                  {testResult.message}
                </Text>
              </View>
            )}
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#070a12',
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
    gap: 20,
  },
  section: {
    backgroundColor: '#0f172a',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
    padding: 16,
    gap: 16,
  },
  sectionHeader: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  sectionSubtitle: {
    color: '#94a3b8',
    fontSize: 12,
    lineHeight: 16,
    marginTop: -8,
  },
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#070a12',
    borderWidth: 1,
    borderColor: '#1e293b',
    borderRadius: 10,
    paddingHorizontal: 12,
  },
  input: {
    flex: 1,
    color: '#ffffff',
    fontSize: 14,
    paddingVertical: 12,
  },
  saveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#ef4444',
    paddingVertical: 14,
    borderRadius: 12,
  },
  saveBtnDisabled: {
    backgroundColor: '#991b1b',
  },
  saveBtnText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  devSection: {
    backgroundColor: '#0f172a',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
    overflow: 'hidden',
  },
  devToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  devToggleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  devToggleTitle: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '700',
  },
  devBody: {
    padding: 16,
    paddingTop: 0,
    gap: 14,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
  },
  infoBanner: {
    flexDirection: 'row',
    gap: 8,
    backgroundColor: 'rgba(56, 189, 248, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(56, 189, 248, 0.2)',
    padding: 10,
    borderRadius: 8,
    marginTop: 12,
  },
  infoBannerText: {
    color: '#bae6fd',
    fontSize: 11,
    lineHeight: 16,
    flex: 1,
  },
  inputDev: {
    backgroundColor: '#070a12',
    borderWidth: 1,
    borderColor: '#1e293b',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#ffffff',
    fontFamily: 'Courier',
    fontSize: 13,
  },
  devBtnRow: {
    flexDirection: 'row',
    gap: 10,
  },
  testBtn: {
    flex: 1,
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#38bdf8',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  testBtnText: {
    color: '#38bdf8',
    fontSize: 11,
    fontWeight: '800',
  },
  resetBtn: {
    flex: 1,
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#475569',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  resetBtnText: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '800',
  },
  testResultBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
  },
  testResultOk: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  testResultErr: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  testResultText: {
    fontSize: 12,
    flex: 1,
    fontWeight: '600',
  },
});
