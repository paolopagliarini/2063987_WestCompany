import { useRef, useCallback, useEffect } from 'react';
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

const COLORS = ['#2563eb', '#dc2626', '#16a34a', '#ca8a04', '#9333ea', '#0891b2'];
const MAX_HISTORY_POINTS = 60;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTopicName(id: string): string {
  return id
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

function groupBySensorId(
  sensors: Record<string, SensorEvent>,
): Map<string, SensorEvent[]> {
  const groups = new Map<string, SensorEvent[]>();
  for (const event of Object.values(sensors)) {
    if (event.source !== 'stream') continue;
    const list = groups.get(event.sensor_id) ?? [];
    list.push(event);
    groups.set(event.sensor_id, list);
  }
  return groups;
}

function metricKey(event: SensorEvent): string {
  return `${event.sensor_id}_${event.metric}`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function TelemetryPage() {
  const { data, loading, error } = usePolling(fetchSensorsLatest, 5000);

  // Chart history: Map<metricKey, Array<{time, ...metricValues}>>
  // We store per-topic history where each entry has time + all metric values
  const historyRef = useRef<Map<string, Array<{ time: string; value: number }>>>(
    new Map(),
  );

  // Append new data points on each poll
  useEffect(() => {
    if (!data?.sensors) return;
    const map = historyRef.current;
    for (const event of Object.values(data.sensors)) {
      if (event.source !== 'stream') continue;
      const key = metricKey(event);
      let arr = map.get(key);
      if (!arr) {
        arr = [];
        map.set(key, arr);
      }
      arr.push({
        time: new Date(event.timestamp).toLocaleTimeString(),
        value: event.value,
      });
      if (arr.length > MAX_HISTORY_POINTS) {
        arr.splice(0, arr.length - MAX_HISTORY_POINTS);
      }
    }
  }, [data]);

  // Build merged chart data per topic: array of { time, metric1, metric2, ... }
  const buildChartData = useCallback(
    (events: SensorEvent[]): Array<Record<string, string | number>> => {
      if (events.length === 0) return [];

      // Find the longest history among all metrics in this topic
      const metricHistories = events.map((e) => ({
        metric: e.metric,
        history: historyRef.current.get(metricKey(e)) ?? [],
      }));

      const maxLen = Math.max(...metricHistories.map((h) => h.history.length));
      if (maxLen === 0) return [];

      const merged: Array<Record<string, string | number>> = [];
      for (let i = 0; i < maxLen; i++) {
        const point: Record<string, string | number> = { time: '' };
        for (const { metric, history } of metricHistories) {
          if (i < history.length) {
            point.time = history[i].time;
            point[metric] = history[i].value;
          }
        }
        merged.push(point);
      }
      return merged;
    },
    [],
  );

  // ---------- Derived data ----------

  const groups = data?.sensors
    ? groupBySensorId(data.sensors)
    : new Map<string, SensorEvent[]>();

  const sortedGroups = Array.from(groups.entries()).sort(([a], [b]) =>
    a.localeCompare(b),
  );

  // ---------- Render ----------

  if (loading && !data) {
    return (
      <div>
        <h2 className="mb-6 text-xl font-semibold">Real-Time Telemetry</h2>
        <p className="text-muted-foreground">Loading telemetry data...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div>
        <h2 className="mb-6 text-xl font-semibold">Real-Time Telemetry</h2>
        <p className="text-destructive">Error: {error}</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="mb-6 text-xl font-semibold">Real-Time Telemetry</h2>

      {error && (
        <p className="mb-4 text-sm text-destructive">Polling error: {error}</p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {sortedGroups.map(([sensorId, events]) => {
          const chartData = buildChartData(events);

          return (
            <div
              key={sensorId}
              className="rounded-lg border bg-white p-4"
            >
              {/* Card header */}
              <h3 className="mb-3 text-sm font-semibold text-foreground">
                {formatTopicName(sensorId)}
              </h3>

              {/* Metrics list */}
              <div className="mb-4 space-y-2">
                {events.map((event) => (
                  <div
                    key={metricKey(event)}
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
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          event.status === 'warning'
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

              {/* Chart — always visible */}
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 10 }}
                  />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  {events.map((event, idx) => (
                    <Line
                      key={metricKey(event)}
                      dataKey={event.metric}
                      name={event.metric}
                      type="monotone"
                      stroke={COLORS[idx % COLORS.length]}
                      dot={false}
                      strokeWidth={2}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          );
        })}
      </div>

      {sortedGroups.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No telemetry streams available.
        </p>
      )}
    </div>
  );
}
