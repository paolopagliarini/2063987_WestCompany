import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { usePolling } from '@/app/hooks/usePolling';
import {
  fetchSensorsLatest,
  fetchActuators,
  fetchRules,
  fetchNotifications,
  fetchIngestionHealth,
  fetchAutomationHealth,
  fetchRulesHealth,
  fetchNotificationsHealth,
  fetchActuatorsHealth,
  fetchHistoryHealth,
  NOTIFICATIONS_STREAM_URL,
  type Notification,
} from '@/app/lib/api';

// ---------------------------------------------------------------------------
// Health check definitions
// ---------------------------------------------------------------------------

const HEALTH_SERVICES = [
  { name: 'Ingestion', fn: fetchIngestionHealth },
  { name: 'Automation Engine', fn: fetchAutomationHealth },
  { name: 'Rule Manager', fn: fetchRulesHealth },
  { name: 'Notifications', fn: fetchNotificationsHealth },
  { name: 'Actuator Control', fn: fetchActuatorsHealth },
  { name: 'Data History', fn: fetchHistoryHealth },
] as const;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SystemStatus() {
  // ---- Summary data (US7) -------------------------------------------------

  const fetchSensors = useCallback(() => fetchSensorsLatest(), []);
  const fetchActs = useCallback(() => fetchActuators(), []);
  const fetchRls = useCallback(() => fetchRules(), []);
  const fetchNotifs = useCallback(() => fetchNotifications(30), []);

  const { data: sensorsData } = usePolling(fetchSensors, 10_000);
  const { data: actuatorsData } = usePolling(fetchActs, 10_000);
  const { data: rulesData } = usePolling(fetchRls, 15_000);
  const { data: notificationsData } = usePolling(fetchNotifs, 10_000);

  const warningCount = sensorsData
    ? Object.values(sensorsData.sensors).filter((s) => s.status === 'warning').length
    : 0;

  const activeRulesCount = rulesData
    ? rulesData.rules.filter((r) => r.is_active === true).length
    : 0;

  const actuatorsOnCount = actuatorsData
    ? Object.values(actuatorsData.actuators).filter((a) => a.state === 'ON').length
    : 0;

  // ---- Service health (US20) ----------------------------------------------

  const [health, setHealth] = useState<Record<string, 'online' | 'offline'>>({});

  useEffect(() => {
    const checkHealth = async () => {
      const results: Record<string, 'online' | 'offline'> = {};
      await Promise.all(
        HEALTH_SERVICES.map(async (svc) => {
          try {
            await svc.fn();
            results[svc.name] = 'online';
          } catch {
            results[svc.name] = 'offline';
          }
        }),
      );
      setHealth(results);
    };

    checkHealth();
    const id = setInterval(checkHealth, 15_000);
    return () => clearInterval(id);
  }, []);

  // ---- SSE alerts (US16) --------------------------------------------------

  useEffect(() => {
    const es = new EventSource(NOTIFICATIONS_STREAM_URL);

    es.onmessage = (event) => {
      try {
        const notification: Notification = JSON.parse(event.data);
        if (notification.severity === 'critical') {
          toast.error(notification.message);
        } else if (notification.severity === 'warning') {
          toast.warning(notification.message);
        }
      } catch {
        // ignore malformed messages
      }
    };

    return () => es.close();
  }, []);

  // ---- Notifications log (US17) -------------------------------------------

  const alertNotifications = notificationsData
    ? notificationsData.notifications.filter(
        (n) => n.severity === 'warning' || n.severity === 'critical',
      )
    : [];

  // ---- Render -------------------------------------------------------------

  return (
    <div>
      <h2 className="mb-6 text-xl font-semibold">System Status</h2>

      {/* Summary Cards (US7) */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Warnings */}
        <div className="border rounded-lg p-5">
          <p className="text-sm text-gray-500 mb-1">Warnings</p>
          <p className="text-3xl font-bold text-amber-500">{warningCount}</p>
        </div>

        {/* Active Rules */}
        <div className="border rounded-lg p-5">
          <p className="text-sm text-gray-500 mb-1">Active Rules</p>
          <p className="text-3xl font-bold text-blue-500">{activeRulesCount}</p>
        </div>

        {/* Actuators ON */}
        <div className="border rounded-lg p-5">
          <p className="text-sm text-gray-500 mb-1">Actuators ON</p>
          <p className="text-3xl font-bold text-green-500">{actuatorsOnCount}</p>
        </div>
      </div>

      {/* Service Health (US20) */}
      <div className="border rounded-lg p-4 mb-6">
        <p className="text-sm font-medium text-gray-500 mb-3">Service Health</p>
        <div className="flex flex-wrap gap-6">
          {HEALTH_SERVICES.map((svc) => {
            const status = health[svc.name];
            const isOnline = status === 'online';
            return (
              <div key={svc.name} className="flex items-center gap-2">
                <span
                  className={`w-3 h-3 rounded-full ${
                    status == null
                      ? 'bg-gray-300'
                      : isOnline
                        ? 'bg-green-500'
                        : 'bg-red-500'
                  }`}
                />
                <span className="text-sm">{svc.name}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Notifications Log (US17) */}
      <div className="border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50">
          <p className="text-sm font-medium text-gray-500">Recent Alerts</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 bg-gray-50">
                <th className="px-4 py-2 font-medium">Timestamp</th>
                <th className="px-4 py-2 font-medium">Severity</th>
                <th className="px-4 py-2 font-medium">Sensor</th>
                <th className="px-4 py-2 font-medium">Message</th>
              </tr>
            </thead>
            <tbody>
              {alertNotifications.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-gray-400">
                    No warning or critical notifications yet.
                  </td>
                </tr>
              ) : (
                alertNotifications.map((n) => (
                  <tr key={n.notification_id} className="border-t">
                    <td className="px-4 py-2 whitespace-nowrap font-mono text-xs text-gray-600">
                      {new Date(n.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                          n.severity === 'critical'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {n.severity}
                      </span>
                    </td>
                    <td className="px-4 py-2 font-mono text-xs">{n.sensor_id}</td>
                    <td className="px-4 py-2">{n.message}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
