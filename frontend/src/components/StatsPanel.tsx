import type { StatsResponse } from "../types";

interface Props {
  data: StatsResponse | null;
  loading: boolean;
  error: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  flying: "#3b82f6",
  landing: "#f59e0b",
  idle: "#10b981",
  takeoff: "#8b5cf6",
};

export function StatsPanel({ data, loading, error }: Props) {
  if (error) return <div className="error-banner">Stats indisponibles : {error}</div>;

  const validTotal = data?.by_status.reduce((sum, s) => sum + s.count, 0) ?? 0;

  return (
    <div className="stats-panel">
      {/* Total Events */}
      <div className="stat-card">
        <div className="stat-card-icon" style={{ color: "var(--blue)" }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
        </div>
        <div className="stat-card-content">
          <span className="stat-label">Événements total</span>
          <span className="stat-value">
            {loading ? "…" : (data?.total.toLocaleString() ?? "—")}
          </span>
        </div>
      </div>

      {/* Average Battery */}
      <div className="stat-card">
        <div className="stat-card-icon" style={{ color: "var(--green)" }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="1" y="6" width="18" height="12" rx="2" ry="2"></rect>
            <line x1="23" y1="11" x2="23" y2="13"></line>
          </svg>
        </div>
        <div className="stat-card-content">
          <span className="stat-label">Batterie moyenne</span>
          <span className="stat-value">
            {loading ? "…" : data ? `${data.avg_battery}%` : "—"}
          </span>
        </div>
      </div>

      {/* Breakdown */}
      <div className="stat-card stat-breakdown">
        <span className="stat-label">Répartition par status</span>
        {loading && <span>Chargement...</span>}
        {!loading && data && (
          <ul className="breakdown-list">
            {data.by_status.map((s) => {
              const pct = validTotal > 0 ? (s.count / validTotal) * 100 : 0;
              const barColor = STATUS_COLORS[s.status] ?? "#6b7280";
              return (
                <li key={s.status} className="breakdown-item">
                  <div className="breakdown-info">
                    <span className={`chip chip-status chip-${s.status}`}>
                      {s.status}
                    </span>
                    <div style={{ display: "flex", alignItems: "center" }}>
                      <span className="breakdown-count">{s.count.toLocaleString()}</span>
                      <span className="breakdown-pct">({pct.toFixed(1)}%)</span>
                    </div>
                  </div>
                  <div className="breakdown-bar-bg">
                    <div
                      className="breakdown-bar-fill"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: barColor,
                        boxShadow: `0 0 8px ${barColor}40`,
                      }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
