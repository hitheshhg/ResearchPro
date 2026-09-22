export type Sector = "LEFT" | "CENTER" | "RIGHT";

export interface DoAEvent {
  type: "doa_event";
  source?: string;
  sector: Sector;
  angle_deg: number;
  confidence: number;
  intensity: number;
  peak_lag: number;
  peak_ncc?: number;
  dsp_us?: number;
  nn_us?: number;
  timestamp?: number;
}

export interface TelemetryState {
  connected: boolean;
  port: string;
  sector: Sector;
  angle: number;
  confidence: number;
  intensity: number;
  peakLag: number;
  peakNcc: number;
  dspLatencyUs: number;
  nnLatencyUs: number;
  audioMuted: boolean;
}
