import { useState, useCallback } from 'react';
import { usePolling } from '@/app/hooks/usePolling';
import { fetchActuators, toggleActuator, fetchActuatorHistory, type Actuator, type ActuatorCommand } from '@/app/lib/api';

function formatId(id: string): string {
  return id.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatTimestamp(ts: string): string {
  const date = new Date(ts);
  return date.toLocaleString();
}

export function ActuatorsControl() {
  const { data, loading, error, refetch } = usePolling(fetchActuators, 5000);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [historyData, setHistoryData] = useState<Record<string, ActuatorCommand[]>>({});
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [toggleError, setToggleError] = useState<string | null>(null);

  const actuators: Actuator[] = data
    ? Object.values(data.actuators)
    : [];

  const handleToggle = useCallback(async (id: string, currentState: string) => {
    setTogglingId(id);
    setToggleError(null);
    const newState = currentState === 'ON' ? 'OFF' : 'ON';
    try {
      await toggleActuator(id, newState);
      await refetch();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Toggle failed';
      setToggleError(`Failed to toggle ${formatId(id)}: ${message}`);
    } finally {
      setTogglingId(null);
    }
  }, [refetch]);

  const handleToggleHistory = useCallback(async (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });

    if (!expandedIds.has(id)) {
      try {
        const result = await fetchActuatorHistory(id);
        setHistoryData((prev) => ({ ...prev, [id]: result.commands }));
      } catch {
        setHistoryData((prev) => ({ ...prev, [id]: [] }));
      }
    }
  }, [expandedIds]);

  if (loading && actuators.length === 0) {
    return <div className="text-gray-500">Loading actuators...</div>;
  }

  if (error && actuators.length === 0) {
    return <div className="text-red-600">Error loading actuators: {error.message}</div>;
  }

  return (
    <div>
      <h2 className="mb-6 text-xl font-semibold">Actuator Control</h2>

      {toggleError && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700">
          {toggleError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {actuators.map((actuator) => {
          const isOn = actuator.state === 'ON';
          const isToggling = togglingId === actuator.actuator_id;
          const isExpanded = expandedIds.has(actuator.actuator_id);
          const history = historyData[actuator.actuator_id];

          return (
            <div
              key={actuator.actuator_id}
              className="rounded-lg border border-gray-200 bg-white p-5"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-medium">
                  {formatId(actuator.actuator_id)}
                </h3>
                <span
                  className={`inline-block rounded-full px-4 py-1 text-lg font-bold ${isOn
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                    }`}
                >
                  {actuator.state}
                </span>
              </div>

              <div className="mb-4 text-xs text-gray-500">
                Last updated: {formatTimestamp(actuator.updated_at)}
              </div>

              <button
                onClick={() => handleToggle(actuator.actuator_id, actuator.state)}
                disabled={isToggling}
                className="w-full rounded border border-gray-300 bg-white px-4 py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isToggling ? 'Toggling...' : `Turn ${isOn ? 'OFF' : 'ON'}`}
              </button>

              <button
                onClick={() => handleToggleHistory(actuator.actuator_id)}
                className="mt-2 w-full rounded border border-gray-200 bg-gray-50 px-4 py-2 text-xs text-gray-600 hover:bg-gray-100"
              >
                {isExpanded ? 'Hide History' : 'Show History'}
              </button>

              {isExpanded && (
                <div className="mt-3">
                  {!history ? (
                    <div className="text-xs text-gray-400">Loading history...</div>
                  ) : history.length === 0 ? (
                    <div className="text-xs text-gray-400">No history available.</div>
                  ) : (
                    <ul className="space-y-0">
                      {history.map((cmd) => (
                        <li
                          key={cmd.id}
                          className="border-b border-gray-100 py-2 text-xs text-gray-600 last:border-b-0"
                        >
                          <div className="flex items-center justify-between">
                            <span>
                              {cmd.previous_state} &rarr; {cmd.new_state}
                            </span>
                            <span className="text-gray-400">
                              {formatTimestamp(cmd.executed_at)}
                            </span>
                          </div>
                          <div className="mt-0.5 flex items-center gap-2">
                            <span
                              className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-medium ${cmd.source === 'manual'
                                ? 'bg-blue-50 text-blue-600'
                                : cmd.source?.includes('automation')
                                  ? 'bg-purple-50 text-purple-600'
                                  : 'bg-gray-100 text-gray-500'
                                }`}
                            >
                              {cmd.source === 'manual'
                                ? 'Manual'
                                : cmd.source?.includes('automation')
                                  ? 'Rule'
                                  : cmd.source ?? 'Unknown'}
                            </span>
                            {cmd.reason && (
                              <span className="text-gray-400">{cmd.reason}</span>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
