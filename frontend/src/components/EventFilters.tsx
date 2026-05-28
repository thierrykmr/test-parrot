import type { FiltersState } from "../types";

const DEVICES = [
  { value: "", label: "Tous" },
  { value: "anafi", label: "Anafi" },
  { value: "bebop", label: "Bebop" },
  { value: "disco", label: "Disco" },
  { value: "skycontroller", label: "Skycontroller" },
];

const STATUSES = [
  { value: "", label: "Tous" },
  { value: "flying", label: "En vol (flying)" },
  { value: "landing", label: "Atterrissage (landing)" },
  { value: "idle", label: "Inactif (idle)" },
  { value: "takeoff", label: "Décollage (takeoff)" },
];

interface Props {
  filters: FiltersState;
  onChange: (filters: FiltersState) => void;
}

export function EventFilters({ filters, onChange }: Props) {
  return (
    <div className="filters">
      <label>
        Device
        <select
          value={filters.device}
          onChange={(e) => onChange({ ...filters, device: e.target.value })}
        >
          {DEVICES.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        Status
        <select
          value={filters.status}
          onChange={(e) => onChange({ ...filters, status: e.target.value })}
        >
          {STATUSES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </label>

      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={filters.anomalyOnly}
          onChange={(e) => onChange({ ...filters, anomalyOnly: e.target.checked })}
        />
        <span className="checkbox-text">Anomalies uniquement</span>
      </label>
    </div>
  );
}
