/**
 * Type definitions for API requests and responses
 */

// Device types
export interface Device {
  _id: string;
  device_id: string;
  name?: string;
  type?: string;
  created_at: string;
  last_seen: string;
  metadata?: Record<string, any>;
}

export interface DeviceCreate {
  device_id: string;
  name?: string;
  type?: string;
  metadata?: Record<string, any>;
}

export interface DeviceUpdate {
  name?: string;
  metadata?: Record<string, any>;
}

// Session types
export interface Session {
  _id: string;
  session_id: string;
  device_id: string;
  started_at: string;
  ended_at?: string;
  technique_name?: string;
  param_version: string;
  target_rr?: number;
  status: 'active' | 'completed' | 'cancelled';
  metadata?: Record<string, any>;
}

export interface SessionCreate {
  device_id: string;
  technique_name?: string;
  param_version?: string;
  target_rr?: number;
  metadata?: Record<string, any>;
}

export interface SessionUpdate {
  technique_name?: string;
  target_rr?: number;
  metadata?: Record<string, any>;
}

// Signal types
export type SignalType = 'ecg' | 'hr_derived' | 'resp_rr' | 'guidance' | 'BreathTarget';

export interface SignalRecord {
  _id: string;
  device_id: string;
  session_id?: string;
  signal: SignalType;
  ts: number; // milliseconds
  dt: string; // "DD-MM-YYYY HH:MM:SS:MMM"
  
  // Signal-specific fields
  samples?: number[]; // ECG samples
  bpm?: number; // Heart rate
  estRR?: number; // Respiratory rate
  tijd?: string;
  inhale?: string;
  exhale?: string;
  
  // Guidance fields
  text?: string;
  audio_text?: string;
  color?: 'ok' | 'warn' | 'bad' | 'accent';
  target?: number;
  actual?: number;
  
  // BreathTarget fields
  breath_cycle?: {
    in: number;
    hold1?: number;
    out: number;
    hold2?: number;
  };
}

export interface RecordIngest {
  device_id: string;
  signal: SignalType;
  ts: number;
  dt?: string;
  [key: string]: any; // Flexible for signal-specific fields
}

// Technique types
export interface Technique {
  _id: string;
  name: string;
  description?: string;
  param_version?: string;
  protocol: Array<[number, number, number, number, number?]>; // [in, hold1, out, hold2, repeats]
  show_in_app: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface TechniqueCreate {
  name: string;
  description?: string;
  protocol: {
    in: number;
    hold1?: number;
    out: number;
    hold2?: number;
  };
  show_in_app?: boolean;
  is_active?: boolean;
}

// Feedback types
export interface FeedbackRules {
  _id: string;
  settings: {
    stability_threshold: number;
    min_stable_time: number;
    feedback_delay: number;
  };
  rules: Array<{
    condition: string;
    visual_text: string;
    audio_text: string;
    color: 'ok' | 'warn' | 'bad' | 'accent';
  }>;
  updated_at: string;
}

// Parameter Set types
export interface ParameterSet {
  _id: string;
  version: string;
  is_default: boolean;
  parameters: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  skip: number;
}

// Status types
export interface SystemStatus {
  status: 'ok' | 'error';
  database: 'connected' | 'disconnected';
  version: string;
  timestamp: string;
}
