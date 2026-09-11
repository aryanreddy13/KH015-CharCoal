import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Image,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import {
  Camera,
  Image as ImageIcon,
  MapPin,
  Plus,
  Minus,
  Check,
  X,
  AlertTriangle,
  Upload,
} from 'lucide-react-native';
import { locationService } from '../src/services/location';
import { storageService } from '../src/services/storage';
import { apiService } from '../src/services/api';
import { GPSIndicator } from '../src/components/GPSIndicator';
import {
  DisasterType,
  RequiredResource,
  LocationData,
  LocationLockState,
  LocalReportItem,
} from '../src/types';

const DISASTER_TYPES: DisasterType[] = [
  'Flood',
  'Earthquake',
  'Cyclone',
  'Fire',
  'Landslide',
  'Other',
];

const RESOURCE_OPTIONS: RequiredResource[] = [
  'Rescue',
  'Medical',
  'Medicine',
  'Food',
  'Water',
  'Shelter',
];

export default function ReportScreen() {
  const router = useRouter();

  // Form states
  const [disasterType, setDisasterType] = useState<DisasterType>('Flood');
  const [description, setDescription] = useState('');
  const [peopleAffected, setPeopleAffected] = useState(1);
  const [injuredPeople, setInjuredPeople] = useState(0);
  const [missingPeople, setMissingPeople] = useState(0);
  const [selectedResources, setSelectedResources] = useState<RequiredResource[]>(['Rescue', 'Medical']);

  // GPS state
  const [location, setLocation] = useState<LocationData | null>(null);
  const [lockState, setLockState] = useState<LocationLockState>('ACQUIRING');

  // Photo state
  const [photoUri, setPhotoUri] = useState<string | null>(null);

  // Submitting
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch Location on mount
  const acquireLocation = async () => {
    setLockState('ACQUIRING');
    const res = await locationService.getCurrentLocation();
    if (res.data) {
      setLocation(res.data);
      setLockState('LOCKED');
    } else {
      setLockState(res.state);
      // Fallback coordinates
      setLocation(locationService.createManualFallback());
    }
  };

  useEffect(() => {
    acquireLocation();
  }, []);

  // Resource toggle
  const toggleResource = (res: RequiredResource) => {
    if (selectedResources.includes(res)) {
      setSelectedResources(selectedResources.filter((r) => r !== res));
    } else {
      setSelectedResources([...selectedResources, res]);
    }
  };

  // Photo capture
  const handleTakePhoto = async () => {
    try {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Camera Permission', 'Camera permission is required to capture incident evidence.');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.6, // Keep compressed for fast emergency transmission
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        setPhotoUri(result.assets[0].uri);
      }
    } catch (err: any) {
      console.warn('Camera launch error:', err);
      Alert.alert('Camera Error', 'Could not open camera.');
    }
  };

  // Photo pick from library
  const handlePickPhoto = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Gallery Permission', 'Media permission is required to select photos.');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.6,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        setPhotoUri(result.assets[0].uri);
      }
    } catch (err: any) {
      console.warn('Image picker error:', err);
    }
  };

  // Submit report handler
  const handleSubmitReport = async () => {
    if (!description.trim()) {
      Alert.alert('Description Required', 'Please enter a brief description of the incident.');
      return;
    }

    setIsSubmitting(true);

    try {
      const activeLoc = location || locationService.createManualFallback();
      const settings = await storageService.getSettings();
      const localId = `report_local_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;

      const reportPayload = {
        disaster_type: disasterType,
        description: description.trim(),
        people_affected: Math.max(1, peopleAffected),
        injured_people: Math.max(0, injuredPeople),
        missing_people: Math.max(0, missingPeople),
        latitude: activeLoc.latitude,
        longitude: activeLoc.longitude,
        required_resources: selectedResources,
        photo_url: photoUri ? `evidence_${localId}.jpg` : undefined,
        status: 'PENDING REVIEW',
      };

      let syncStatus: 'SENT' | 'PENDING_SYNC' = 'PENDING_SYNC';
      let serverResponse: any = null;

      try {
        serverResponse = await apiService.sendReport(reportPayload);
        syncStatus = 'SENT';
      } catch (netErr: any) {
        console.warn('Direct report send failed, storing offline:', netErr.message);
        syncStatus = 'PENDING_SYNC';
      }

      // Store in local storage
      const localItem: LocalReportItem = {
        local_id: localId,
        created_at: new Date().toISOString(),
        sync_status: syncStatus,
        payload: reportPayload,
        server_id: serverResponse?.id,
        server_status: serverResponse?.status || 'PENDING REVIEW',
        photo_uri: photoUri || undefined,
      };

      await storageService.addReportItem(localItem);

      Alert.alert(
        syncStatus === 'SENT' ? 'Report Submitted' : 'Report Stored Offline',
        syncStatus === 'SENT'
          ? 'Your incident report has been received by the Command Center.'
          : 'You are currently offline. Report has been saved and will transmit as soon as connection is restored.',
        [
          {
            text: 'View Reports',
            onPress: () => router.replace('/my-reports'),
          },
        ]
      );
    } catch (err: any) {
      Alert.alert('Submission Error', err.message || 'Failed to process incident report.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Numeric input sanitization helper
  const handleNumericInput = (setter: React.Dispatch<React.SetStateAction<number>>, text: string, minVal = 0) => {
    const sanitized = text.replace(/[^0-9]/g, '');
    if (sanitized === '') {
      setter(minVal);
    } else {
      const parsed = parseInt(sanitized, 10);
      setter(isNaN(parsed) ? minVal : Math.max(minVal, parsed));
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Disaster Type Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>DISASTER TYPE *</Text>
        <View style={styles.chipGrid}>
          {DISASTER_TYPES.map((type) => {
            const isSelected = disasterType === type;
            return (
              <TouchableOpacity
                key={type}
                style={[styles.chip, isSelected && styles.chipSelected]}
                onPress={() => setDisasterType(type)}
                activeOpacity={0.7}
              >
                <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                  {type}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Description */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>INCIDENT DESCRIPTION *</Text>
        <TextInput
          style={styles.textArea}
          placeholder="Describe what happened, current hazards, stranded people, access road blockages..."
          placeholderTextColor="#64748b"
          multiline
          numberOfLines={4}
          value={description}
          onChangeText={setDescription}
        />
      </View>

      {/* People Counts / Casualties */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>CASUALTIES & AFFECTED PEOPLE</Text>
          <Text style={styles.sectionHint}>Type numbers directly or use +/-</Text>
        </View>

        {/* Total Affected */}
        <View style={styles.counterRow}>
          <View>
            <Text style={styles.counterLabel}>Total Affected</Text>
            <Text style={styles.counterSubtext}>Estimated population impacted</Text>
          </View>
          <View style={styles.counterControls}>
            <TouchableOpacity
              style={styles.counterBtn}
              onPress={() => setPeopleAffected(Math.max(1, peopleAffected - 1))}
              activeOpacity={0.7}
            >
              <Minus size={16} color="#ffffff" />
            </TouchableOpacity>

            <TextInput
              style={styles.counterInput}
              keyboardType="number-pad"
              value={String(peopleAffected)}
              onChangeText={(txt) => handleNumericInput(setPeopleAffected, txt, 1)}
              selectTextOnFocus
              maxLength={6}
            />

            <TouchableOpacity
              style={styles.counterBtn}
              onPress={() => setPeopleAffected(peopleAffected + 1)}
              activeOpacity={0.7}
            >
              <Plus size={16} color="#ffffff" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Injured People */}
        <View style={styles.counterRow}>
          <View>
            <Text style={[styles.counterLabel, { color: '#f87171' }]}>Injured People</Text>
            <Text style={styles.counterSubtext}>Requiring medical/triage aid</Text>
          </View>
          <View style={styles.counterControls}>
            <TouchableOpacity
              style={styles.counterBtn}
              onPress={() => setInjuredPeople(Math.max(0, injuredPeople - 1))}
              activeOpacity={0.7}
            >
              <Minus size={16} color="#ffffff" />
            </TouchableOpacity>

            <TextInput
              style={[styles.counterInput, styles.counterInputAlert]}
              keyboardType="number-pad"
              value={String(injuredPeople)}
              onChangeText={(txt) => handleNumericInput(setInjuredPeople, txt, 0)}
              selectTextOnFocus
              maxLength={6}
            />

            <TouchableOpacity
              style={styles.counterBtn}
              onPress={() => setInjuredPeople(injuredPeople + 1)}
              activeOpacity={0.7}
            >
              <Plus size={16} color="#ffffff" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Missing / Trapped */}
        <View style={styles.counterRow}>
          <View>
            <Text style={[styles.counterLabel, { color: '#fbbf24' }]}>Missing / Trapped</Text>
            <Text style={styles.counterSubtext}>Requiring search & extrication</Text>
          </View>
          <View style={styles.counterControls}>
            <TouchableOpacity
              style={styles.counterBtn}
              onPress={() => setMissingPeople(Math.max(0, missingPeople - 1))}
              activeOpacity={0.7}
            >
              <Minus size={16} color="#ffffff" />
            </TouchableOpacity>

            <TextInput
              style={[styles.counterInput, styles.counterInputWarning]}
              keyboardType="number-pad"
              value={String(missingPeople)}
              onChangeText={(txt) => handleNumericInput(setMissingPeople, txt, 0)}
              selectTextOnFocus
              maxLength={6}
            />

            <TouchableOpacity
              style={styles.counterBtn}
              onPress={() => setMissingPeople(missingPeople + 1)}
              activeOpacity={0.7}
            >
              <Plus size={16} color="#ffffff" />
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Required Resources Multi-select */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>REQUIRED RELIEF RESOURCES</Text>
        <View style={styles.chipGrid}>
          {RESOURCE_OPTIONS.map((resource) => {
            const isSelected = selectedResources.includes(resource);
            return (
              <TouchableOpacity
                key={resource}
                style={[styles.resourceChip, isSelected && styles.resourceChipSelected]}
                onPress={() => toggleResource(resource)}
                activeOpacity={0.7}
              >
                {isSelected && <Check size={14} color="#38bdf8" />}
                <Text
                  style={[
                    styles.resourceChipText,
                    isSelected && styles.resourceChipTextSelected,
                  ]}
                >
                  {resource}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* GPS Location Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>INCIDENT LOCATION</Text>
        <GPSIndicator
          location={location}
          state={lockState}
          onRefresh={acquireLocation}
          showCoordinates={true}
        />
      </View>

      {/* Photo Capture Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>EVIDENCE PHOTO (OPTIONAL)</Text>

        {photoUri ? (
          <View style={styles.previewContainer}>
            <Image source={{ uri: photoUri }} style={styles.imagePreview} />
            <TouchableOpacity
              style={styles.removePhotoBtn}
              onPress={() => setPhotoUri(null)}
              activeOpacity={0.8}
            >
              <X size={16} color="#ffffff" />
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.photoActionRow}>
            <TouchableOpacity
              style={styles.photoBtn}
              onPress={handleTakePhoto}
              activeOpacity={0.8}
            >
              <Camera size={20} color="#38bdf8" />
              <Text style={styles.photoBtnText}>TAKE PHOTO</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.photoBtn}
              onPress={handlePickPhoto}
              activeOpacity={0.8}
            >
              <ImageIcon size={20} color="#94a3b8" />
              <Text style={styles.photoBtnText}>GALLERY</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Submit Button */}
      <TouchableOpacity
        style={[styles.submitButton, isSubmitting && styles.submitButtonDisabled]}
        onPress={handleSubmitReport}
        disabled={isSubmitting}
        activeOpacity={0.85}
      >
        {isSubmitting ? (
          <ActivityIndicator color="#ffffff" />
        ) : (
          <>
            <Upload size={20} color="#ffffff" />
            <Text style={styles.submitButtonText}>SUBMIT EMERGENCY REPORT</Text>
          </>
        )}
      </TouchableOpacity>
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
    gap: 8,
  },
  sectionTitle: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  chipGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  chipSelected: {
    backgroundColor: '#dc2626',
    borderColor: '#f87171',
  },
  chipText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '700',
  },
  chipTextSelected: {
    color: '#ffffff',
  },
  textArea: {
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#1e293b',
    borderRadius: 12,
    padding: 14,
    color: '#ffffff',
    fontSize: 14,
    minHeight: 100,
    textAlignVertical: 'top',
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionHint: {
    color: '#64748b',
    fontSize: 11,
    fontWeight: '600',
  },
  counterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#0f172a',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 6,
  },
  counterLabel: {
    color: '#e2e8f0',
    fontSize: 14,
    fontWeight: '700',
  },
  counterSubtext: {
    color: '#64748b',
    fontSize: 11,
    marginTop: 2,
  },
  counterControls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  counterBtn: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
    alignItems: 'center',
    justifyContent: 'center',
  },
  counterInput: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '800',
    minWidth: 54,
    paddingHorizontal: 8,
    paddingVertical: 6,
    backgroundColor: '#070a12',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
    textAlign: 'center',
  },
  counterInputAlert: {
    borderColor: 'rgba(239, 68, 68, 0.4)',
    color: '#f87171',
  },
  counterInputWarning: {
    borderColor: 'rgba(245, 158, 11, 0.4)',
    color: '#fbbf24',
  },
  resourceChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  resourceChipSelected: {
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    borderColor: '#38bdf8',
  },
  resourceChipText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '700',
  },
  resourceChipTextSelected: {
    color: '#38bdf8',
  },
  photoActionRow: {
    flexDirection: 'row',
    gap: 12,
  },
  photoBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#1e293b',
    paddingVertical: 14,
    borderRadius: 12,
  },
  photoBtnText: {
    color: '#e2e8f0',
    fontSize: 12,
    fontWeight: '800',
  },
  previewContainer: {
    position: 'relative',
    borderRadius: 12,
    overflow: 'hidden',
    height: 180,
    backgroundColor: '#0f172a',
  },
  imagePreview: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  removePhotoBtn: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    backgroundColor: '#ef4444',
    paddingVertical: 18,
    borderRadius: 14,
    marginTop: 10,
  },
  submitButtonDisabled: {
    backgroundColor: '#991b1b',
  },
  submitButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
});
