export interface TelemetryEvent {
  id: number;
  device: string;
  status: string;
  battery: number;
  timestamp: string;
  is_anomaly: boolean;
  anomaly_reason: string | null;
}

export interface EventListResponse {
  items: TelemetryEvent[];
  total: number;
  limit: number;
  offset: number;
  anomaly_count: number;
}

export interface ByStatusEntry {
  status: string;
  count: number;
}

export interface StatsResponse {
  total: number;
  avg_battery: number;
  by_status: ByStatusEntry[];
}

export interface FiltersState {
  device: string;
  status: string;
  anomalyOnly: boolean;
}
