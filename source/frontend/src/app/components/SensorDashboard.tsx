import { useState, useRef, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { usePolling } from '@/app/hooks/usePolling';
import { fetchSensorsLatest, type SensorEvent } from '@/app/lib/api';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// Only REST-polled sensors appear here; SSE/telemetry sensors are in TelemetryPage
const SENSOR_CATEGORIES: Record<string, string> = {
  greenhouse_temperature: 'environmental',
  entrance_humidity: 'environmental',
  corridor_pressure: 'environmental',
  co2_hall: 'chemical',
  hydroponic_ph: 'chemical',
  air_quality_voc: 'chemical',
  air_quality_pm25: 'chemical',
  water_tank_level: 'physical',
};

const CATEGORY_LABELS = ['all', 'environmental', 'chemical', 'physical'] as const;

const CHART_COLORS = [
  'var(--primary, #2563eb)',
  '#f59e0b',
  '#10b981',
  '#ef4444',
  '#8b5cf6',
  '#ec4899',
];

const MAX_HISTORY_POINTS = 60;
const OFFLINE_THRESHOLD_MS = 30_000;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatSensorId(id: string): string {
  return id
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

/** Group an array of SensorEvents by their sensor_id. */
function groupBySensorId(
  sensors: Record<string, SensorEvent>,
): Map<string, SensorEvent[]> {
  const groups = new Map<string, SensorEvent[]>();
  for (const event of Object.values(sensors)) {
    const list = groups.get(event.sensor_id) ?? [];
    list.push(event);
    groups.set(event.sensor_id, list);
  }
  return groups;
}

/** Build the cache key the same way the backend does. */
function cacheKey(event: SensorEvent): string {
  return `${event.sensor_id}_${event.metric}${event.unit ? '_' + event.unit : ''}`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SensorDashboard() {
  const { data, loading, error } = usePolling(fetchSensorsLatest, 5000);

  // Category filter - null means "all"
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  // Which sensor_ids have their chart expanded
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  // Chart history keyed by cache key
  const historyRef = useRef<Map<string, Array<{ time: string; value: number }>>>(
    new Map(),
  );

  // Push new data points into history whenever polling data changes
  useEffect(() => {
    if (!data?.sensors) return;
    const map = historyRef.current;
    for (const event of Object.values(data.sensors)) {
      const key = cacheKey(event);
      let arr = map.get(key);
      if (!arr) {
        arr = [];
        map.set(key, arr);
      }
      arr.push({
        time: new Date(event.timestamp).toLocaleTimeString(),
        value: event.value,
      });
      // Keep last 60
      if (arr.length > MAX_HISTORY_POINTS) {
        arr.splice(0, arr.length - MAX_HISTORY_POINTS);
      }
    }
  }, [data]);

  const toggleExpanded = useCallback((sensorId: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(sensorId)) {
        next.delete(sensorId);
      } else {
        next.add(sensorId);
      }
      return next;
    });
  }, []);

  // ---------- Derived data ----------

  const groups = data?.sensors ? groupBySensorId(data.sensors) : new Map<string, SensorEvent[]>();

  const filteredGroups = Array.from(groups.entries()).filter(([sensorId]) => {
    if (!activeCategory) return true;
    return SENSOR_CATEGORIES[sensorId] === activeCategory;
  });

  // ---------- Render ----------

  if (loading && !data) {
    return (
      <div>
        <h2 className="mb-6 text-xl font-semibold">Sensor Dashboard</h2>
        <p className="text-muted-foreground">Loading sensors...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div>
        <h2 className="mb-6 text-xl font-semibold">Sensor Dashboard</h2>
        <p className="text-destructive">Error: {error}</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="mb-6 text-xl font-semibold">Sensor Dashboard</h2>

      {/* Category filter buttons */}
      <div className="mb-6 flex flex-wrap gap-2">
        {CATEGORY_LABELS.map((cat) => {
          const isActive =
            (cat === 'all' && activeCategory === null) ||
            cat === activeCategory;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat === 'all' ? null : cat)}
              className={`rounded-md px-4 py-1.5 text-sm font-medium capitalize transition-colors ${isActive
                ? 'bg-primary text-primary-foreground'
                : 'border bg-background text-foreground hover:bg-muted'
                }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {error && (
        <p className="mb-4 text-sm text-destructive">
          Polling error: {error}
        </p>
      )}

      {/* Sensor cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredGroups.map(([sensorId, events]) => {
          const isExpanded = expanded.has(sensorId);

          // Determine connectivity - newest timestamp in the group
          const newestTs = Math.max(
            ...events.map((e) => new Date(e.timestamp).getTime()),
          );
          const isOffline = Date.now() - newestTs > OFFLINE_THRESHOLD_MS;

          return (
            <div
              key={sensorId}
              className="cursor-pointer rounded-lg border bg-white p-4"
              onClick={() => toggleExpanded(sensorId)}
            >
              {/* Card header */}
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground">
                  {formatSensorId(sensorId)}
                </h3>
                <div className="flex items-center gap-2">
                  {isOffline && (
                    <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                      offline
                    </span>
                  )}
                </div>
              </div>

              {/* Metrics */}
              <div className="space-y-2">
                {events.map((event) => (
                  <div
                    key={cacheKey(event)}
                    className="flex items-center justify-between"
                  >
                    <span className="text-xs text-muted-foreground">
                      {event.metric}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-foreground">
                        {typeof event.value === 'number'
                          ? event.value.toFixed(2)
                          : event.value}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {event.unit}
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${event.status === 'warning'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-green-100 text-green-700'
                          }`}
                      >
                        {event.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Expanded chart */}
              {isExpanded && (
                <div
                  className="mt-4"
                  onClick={(e) => e.stopPropagation()}
                >
                  <ResponsiveContainer width="100%" height={150}>
                    <LineChart>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="time"
                        allowDuplicatedCategory={false}
                        tick={{ fontSize: 10 }}
                      />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip />
                      {events.map((event, idx) => {
                        const key = cacheKey(event);
                        const lineData = historyRef.current.get(key) ?? [];
                        return (
                          <Line
                            key={key}
                            data={lineData}
                            dataKey="value"
                            name={event.metric}
                            type="monotone"
                            stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                            dot={false}
                            strokeWidth={2}
                          />
                        );
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filteredGroups.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No sensors found for the selected category.
        </p>
      )}
    </div>
  );
}
