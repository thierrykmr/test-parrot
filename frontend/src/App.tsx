import { useCallback, useEffect, useRef, useState } from "react";
import { BatteryChart } from "./components/BatteryChart";
import { EventFilters } from "./components/EventFilters";
import { EventList } from "./components/EventList";
import { StatsPanel } from "./components/StatsPanel";
import { useEvents } from "./hooks/useEvents";
import { useStats } from "./hooks/useStats";
import type { FiltersState } from "./types";

const AUTO_REFRESH_MS = 30_000;

export default function App() {
  const [filters, setFilters] = useState<FiltersState>({ device: "", status: "", anomalyOnly: false });
  const [globalTick, setGlobalTick] = useState(0);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const refresh = useCallback(() => {
    setGlobalTick((t) => t + 1);
    setLastRefresh(new Date());
  }, []);

  // Auto-refresh every 30s
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    timerRef.current = setInterval(refresh, AUTO_REFRESH_MS);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [refresh]);

  const {
    data: eventsData,
    loading: eventsLoading,
    error: eventsError,
    page,
    sort,
    setPage,
    setSort,
    refresh: refreshEvents,
  } = useEvents(filters);

  const { data: statsData, chartData, loading: statsLoading, error: statsError } =
    useStats(globalTick);

  // Propagate global tick to events too
  useEffect(() => {
    refreshEvents();
  }, [globalTick]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSortToggle = useCallback(() => {
    setSort(sort === "desc" ? "asc" : "desc");
  }, [sort, setSort]);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1>Telemetry Dashboard</h1>
          <span className="subtitle">Drone Fleet Monitor</span>
        </div>
        <div className="header-right">
          <span className="last-refresh">
            Mis à jour : {lastRefresh.toLocaleTimeString("fr-FR")}
          </span>
          <button className="btn-refresh" onClick={refresh} title="Forcer le rafraîchissement">
            ↺ Rafraîchir
          </button>
        </div>
      </header>

      <main className="app-main">
        <section className="top-section">
          <StatsPanel data={statsData} loading={statsLoading} error={statsError} />
          <BatteryChart data={chartData} />
        </section>

        <section className="search-section">
          <h2>Événements</h2>
          <EventFilters filters={filters} onChange={setFilters} />
          <EventList
            data={eventsData}
            loading={eventsLoading}
            error={eventsError}
            page={page}
            sort={sort}
            onPageChange={setPage}
            onSortToggle={handleSortToggle}
          />
        </section>
      </main>
    </div>
  );
}
