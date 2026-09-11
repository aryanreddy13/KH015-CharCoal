import React, { useState } from 'react';
import { apiService } from '../services/api';
import {
  ShieldAlert,
  MapPin,
  Camera,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  Loader2,
  Send,
  LifeBuoy,
  HeartPulse,
  Utensils,
  Droplets,
  Home,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const ReporterPage: React.FC = () => {
  const [disasterType, setDisasterType] = useState('Flood');
  const [description, setDescription] = useState('');
  const [peopleAffected, setPeopleAffected] = useState(10);
  const [injured, setInjured] = useState(0);
  const [missing, setMissing] = useState(0);
  const [latitude, setLatitude] = useState(28.6139);
  const [longitude, setLongitude] = useState(77.2090);
  const [locating, setLocating] = useState(false);
  const [locationStatus, setLocationStatus] = useState<string | null>(null);
  const [selectedResources, setSelectedResources] = useState<string[]>(['Rescue']);
  const [photoSelected, setPhotoSelected] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [reportId, setReportId] = useState<string | null>(null);

  const disasterTypes = ['Flood', 'Earthquake', 'Cyclone', 'Fire', 'Landslide', 'Building Collapse'];
  const resourceOptions = [
    { name: 'Rescue', icon: LifeBuoy },
    { name: 'Medical', icon: HeartPulse },
    { name: 'Food', icon: Utensils },
    { name: 'Water', icon: Droplets },
    { name: 'Shelter', icon: Home },
  ];

  const handleGetLocation = () => {
    setLocating(true);
    setLocationStatus(null);
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLatitude(parseFloat(pos.coords.latitude.toFixed(5)));
          setLongitude(parseFloat(pos.coords.longitude.toFixed(5)));
          setLocating(false);
          setLocationStatus('GPS Coordinates Locked');
        },
        (err) => {
          setLocating(false);
          // Fallback simulation coordinates for demo
          setLatitude(28.6145);
          setLongitude(77.2085);
          setLocationStatus('Coordinates Acquired (Demo Sector A)');
        },
        { timeout: 8000 }
      );
    } else {
      setLocating(false);
      setLocationStatus('GPS Not Supported (Using Demo Coordinates)');
    }
  };

  const toggleResource = (name: string) => {
    setSelectedResources((prev) =>
      prev.includes(name) ? prev.filter((r) => r !== name) : [...prev, name]
    );
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setPhotoSelected(e.target.files[0].name);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    try {
      setSubmitting(true);
      const res = await apiService.createReport({
        disaster_type: disasterType,
        description: `${description} [Requested: ${selectedResources.join(', ')}]`,
        people_affected: Number(peopleAffected) || 1,
        injured_people: Number(injured) || 0,
        missing_people: Number(missing) || 0,
        latitude,
        longitude,
        photo_url: photoSelected ? `https://photos.emergency.gov/${photoSelected}` : undefined,
      });

      setReportId(res.id);
      setSubmitted(true);
    } catch (err: any) {
      console.error('Error submitting report:', err);
      alert('Failed to submit report. Please try again or call emergency helpline 112.');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-ops-bg text-slate-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-ops-surface border border-ops-border rounded-2xl p-6 text-center space-y-5 shadow-2xl">
          <div className="w-16 h-16 rounded-full bg-emerald-950/80 border border-emerald-500/50 text-emerald-400 mx-auto flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.3)]">
            <CheckCircle2 className="w-9 h-9" />
          </div>

          <div className="space-y-1">
            <h1 className="text-xl font-bold font-mono text-white tracking-wide">
              REPORT RECEIVED
            </h1>
            <p className="text-xs text-slate-400">
              Your disaster report has been transmitted to the central AI coordinator.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Status:</span>
              <span className="font-mono font-bold text-amber-400 px-2 py-0.5 rounded bg-amber-950/80 border border-amber-500/40">
                PENDING REVIEW
              </span>
            </div>
            {reportId && (
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-slate-500">Incident ID:</span>
                <span className="text-slate-300 truncate max-w-[150px]">{reportId}</span>
              </div>
            )}
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-500">Coordinates:</span>
              <span className="text-slate-300 font-mono">
                {latitude.toFixed(4)}°N, {longitude.toFixed(4)}°E
              </span>
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <button
              onClick={() => {
                setSubmitted(false);
                setDescription('');
                setPhotoSelected(null);
              }}
              className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium rounded-xl text-xs transition-colors"
            >
              Submit Another Report
            </button>

            <Link
              to="/dashboard"
              className="block w-full py-3 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl text-xs shadow-md transition-all text-center"
            >
              Go to Command Center
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-ops-bg text-slate-100 flex flex-col justify-between py-6 px-4">
      <div className="w-full max-w-md mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Link
            to="/dashboard"
            className="flex items-center space-x-1 text-xs text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Command Center</span>
          </Link>
          <span className="text-xs font-mono font-bold text-rose-500 px-2 py-0.5 rounded bg-rose-950/60 border border-rose-500/30">
            EMERGENCY PORTAL
          </span>
        </div>

        <div className="space-y-1">
          <h1 className="text-xl font-extrabold text-white tracking-wide">
            DISASTER REPORT
          </h1>
          <p className="text-xs text-slate-400">
            Report hazards, trapped victims, or supply needs directly to first responders.
          </p>
        </div>

        {/* Emergency Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Disaster Type */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Disaster Type</label>
            <div className="grid grid-cols-3 gap-2">
              {disasterTypes.map((type) => (
                <button
                  type="button"
                  key={type}
                  onClick={() => setDisasterType(type)}
                  className={`py-2 px-1 text-center rounded-lg text-xs font-medium border transition-all ${
                    disasterType === type
                      ? 'bg-rose-600 text-white border-rose-500 shadow-sm'
                      : 'bg-slate-900/90 text-slate-300 border-slate-800 hover:bg-slate-850'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">
              Situation Description <span className="text-rose-500">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is happening? Describe water level, trapped persons, or building damage..."
              className="w-full p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-rose-500 transition-colors"
            />
          </div>

          {/* Casualty Counts */}
          <div className="grid grid-cols-3 gap-2">
            <div className="space-y-1">
              <label className="text-[11px] text-slate-400">People Affected</label>
              <input
                type="number"
                min="0"
                value={peopleAffected}
                onChange={(e) => setPeopleAffected(Number(e.target.value))}
                className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-center font-mono font-bold text-white focus:outline-none focus:border-rose-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] text-slate-400">Injured</label>
              <input
                type="number"
                min="0"
                value={injured}
                onChange={(e) => setInjured(Number(e.target.value))}
                className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-center font-mono font-bold text-amber-400 focus:outline-none focus:border-rose-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] text-slate-400">Missing / Trapped</label>
              <input
                type="number"
                min="0"
                value={missing}
                onChange={(e) => setMissing(Number(e.target.value))}
                className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-center font-mono font-bold text-rose-400 focus:outline-none focus:border-rose-500"
              />
            </div>
          </div>

          {/* Required Resources Checklist */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Required Resources</label>
            <div className="grid grid-cols-5 gap-1.5">
              {resourceOptions.map((res) => {
                const isSelected = selectedResources.includes(res.name);
                const Icon = res.icon;
                return (
                  <button
                    type="button"
                    key={res.name}
                    onClick={() => toggleResource(res.name)}
                    className={`p-2 rounded-lg text-center flex flex-col items-center justify-center space-y-1 border text-[10px] font-medium transition-colors ${
                      isSelected
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/60'
                        : 'bg-slate-900 text-slate-400 border-slate-800'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{res.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* GPS Location & Photo Buttons */}
          <div className="space-y-2 pt-1">
            <button
              type="button"
              onClick={handleGetLocation}
              disabled={locating}
              className="w-full py-2.5 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 text-xs font-medium flex items-center justify-center space-x-2 transition-colors"
            >
              {locating ? (
                <Loader2 className="w-4 h-4 animate-spin text-rose-400" />
              ) : (
                <MapPin className="w-4 h-4 text-rose-500" />
              )}
              <span>{locating ? 'Acquiring GPS...' : 'USE MY LOCATION'}</span>
            </button>

            {locationStatus && (
              <div className="text-[11px] font-mono text-emerald-400 text-center">
                ✓ {locationStatus} ({latitude.toFixed(4)}°, {longitude.toFixed(4)}°)
              </div>
            )}

            {/* Photo Attachment */}
            <label className="w-full py-2.5 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-dashed border-slate-700 text-slate-300 text-xs font-medium flex items-center justify-center space-x-2 cursor-pointer transition-colors">
              <Camera className="w-4 h-4 text-sky-400" />
              <span>{photoSelected ? `Attached: ${photoSelected}` : 'Attach Photo (Optional)'}</span>
              <input type="file" accept="image/*" onChange={handlePhotoUpload} className="hidden" />
            </label>
          </div>

          {/* Big Submit Button */}
          <button
            type="submit"
            disabled={submitting || !description.trim()}
            className="w-full py-3.5 rounded-xl bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-extrabold text-sm tracking-wider uppercase shadow-[0_0_15px_rgba(225,29,72,0.4)] flex items-center justify-center space-x-2 transition-all"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Transmitting Incident...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>SUBMIT REPORT</span>
              </>
            )}
          </button>
        </form>
      </div>

      <div className="text-center text-[10px] text-slate-400 mt-4">
        PS20 Disaster Response Network • 24/7 National Coordination Grid
      </div>
    </div>
  );
};
