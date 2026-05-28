import { useCallback, useEffect, useRef, useState } from "react";
import { getEvents } from "../api/client";
import type { EventListResponse, FiltersState } from "../types";

const DEBOUNCE_MS = 300;
const PAGE_SIZE = 10;

interface UseEventsResult {
  data: EventListResponse | null;
  loading: boolean;
  error: string | null;
  page: number;
  sort: "asc" | "desc";
  setPage: (p: number) => void;
  setSort: (s: "asc" | "desc") => void;
  refresh: () => void;
}

export function useEvents(filters: FiltersState): UseEventsResult {
  const [data, setData] = useState<EventListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [sort, setSort] = useState<"asc" | "desc">("desc");
  const [tick, setTick] = useState(0);

  // Reset to first page when filters change
  const prevFiltersRef = useRef(filters);
  useEffect(() => {
    const prev = prevFiltersRef.current;
    if (
      prev.device !== filters.device ||
      prev.status !== filters.status ||
      prev.anomalyOnly !== filters.anomalyOnly
    ) {
      setPage(0);
    }
    prevFiltersRef.current = filters;
  }, [filters]);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    const controller = new AbortController();

    const debounceId = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await getEvents(
          filters,
          PAGE_SIZE,
          page * PAGE_SIZE,
          sort,
          controller.signal
        );
        setData(result);
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError((err as Error).message);
        }
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => {
      clearTimeout(debounceId);
      controller.abort();
    };
  }, [filters, page, sort, tick]);

  return { data, loading, error, page, sort, setPage, setSort, refresh };
}
