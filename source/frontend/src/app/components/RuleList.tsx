import { useState, useEffect, useCallback } from 'react';
import { fetchRules, deleteRule, toggleRule, toggleActuator, type Rule } from '@/app/lib/api';

interface RuleListProps {
  onEditRule: (rule: any) => void;
}

export function RuleList({ onEditRule }: RuleListProps) {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRules = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchRules();
      setRules(data.rules);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load rules');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  const handleDelete = async (id: number, name: string) => {
    if (!window.confirm(`Are you sure you want to delete rule "${name}"?`)) {
      return;
    }
    try {
      const rule = rules.find((r) => r.id === id);
      await deleteRule(id);

      if (rule && rule.is_active) {
        const oppositeAction = rule.actuator_action === 'ON' ? 'OFF' : 'ON';
        await toggleActuator(rule.actuator_id, oppositeAction);
      }

      await loadRules();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete rule');
    }
  };

  const handleToggle = async (ruleId: number) => {
    try {
      const rule = rules.find((r) => r.id === ruleId);
      if (!rule) return;

      const newActiveStatus = !rule.is_active;
      await toggleRule(ruleId);

      // If we disabled the rule, send the opposite command to the actuator
      if (!newActiveStatus) {
        const oppositeAction = rule.actuator_action === 'ON' ? 'OFF' : 'ON';
        await toggleActuator(rule.actuator_id, oppositeAction);
      }

      await loadRules();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle rule');
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
        Loading rules...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-8 text-center text-red-600">
        <p>{error}</p>
        <button
          onClick={loadRules}
          className="mt-4 rounded px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-100"
        >
          Retry
        </button>
      </div>
    );
  }

  if (rules.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
        No rules configured
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-gray-50 text-xs font-medium uppercase tracking-wider text-gray-500">
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Condition</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.id} className="border-t border-gray-100">
                <td className="px-4 py-3 font-medium text-gray-900">
                  {rule.name}
                </td>
                <td className="px-4 py-3 font-mono text-gray-700">
                  {rule.sensor_id} {rule.operator} {rule.threshold_value}
                  {rule.threshold_unit ? ` ${rule.threshold_unit}` : ''}
                </td>
                <td className="px-4 py-3 font-mono text-gray-700">
                  {rule.actuator_id} &rarr; {rule.actuator_action}
                </td>
                <td className="px-4 py-3">
                  {rule.is_active ? (
                    <span className="inline-block rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                      Active
                    </span>
                  ) : (
                    <span className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">
                      Inactive
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => onEditRule(rule)}
                      className="rounded px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleToggle(rule.id)}
                      className="rounded px-2.5 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50"
                    >
                      {rule.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      onClick={() => handleDelete(rule.id, rule.name)}
                      className="rounded px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
