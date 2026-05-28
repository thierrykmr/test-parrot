import type { EventListResponse, FiltersState, StatsResponse } from "../types";

const BASE = "/api";
const TIMEOUT_MS = 10_000;

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function fetchJSON<T>(
  url: string,
  signal?: AbortSignal
): Promise<T> {
  const controller = signal ? null : new AbortController();
  const effectiveSignal = signal ?? controller!.signal;

  const timeoutId = controller
    ? setTimeout(() => controller.abort(), TIMEOUT_MS)
    : null;

  try {
    const res = await fetch(url, { signal: effectiveSignal });
    if (!res.ok) {
      throw new ApiError(res.status, `HTTP ${res.status}: ${res.statusText}`);
    }
    return (await res.json()) as T;
  } finally {
    if (timeoutId) clearTimeout(timeoutId);
  }
}

export function buildEventsUrl(
  filters: FiltersState,
  limit: number,
  offset: number,
  sort: "asc" | "desc"
): string {
  const params = new URLSearchParams();
  if (filters.device) params.set("device", filters.device);
  if (filters.status) params.set("status", filters.status);
  if (filters.anomalyOnly) params.set("anomaly_only", "true");
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  params.set("sort", sort);
  return `${BASE}/events?${params.toString()}`;
}

export async function getEvents(
  filters: FiltersState,
  limit: number,
  offset: number,
  sort: "asc" | "desc",
  signal?: AbortSignal
): Promise<EventListResponse> {
  const url = buildEventsUrl(filters, limit, offset, sort);
  return fetchJSON<EventListResponse>(url, signal);
}

export async function getStats(signal?: AbortSignal): Promise<StatsResponse> {
  return fetchJSON<StatsResponse>(`${BASE}/stats`, signal);
}
