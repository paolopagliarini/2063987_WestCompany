import { useState, useEffect } from 'react';
import { fetchSensorsLatest, fetchActuators, createRule, updateRule, type RulePayload } from '@/app/lib/api';

interface RuleBuilderProps {
  editingRule?: any | null;
  onSaved: () => void;
}

const OPERATORS = ['<', '<=', '=', '>', '>='];

export function RuleBuilder({ editingRule, onSaved }: RuleBuilderProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sensorId, setSensorId] = useState('');
  const [operator, setOperator] = useState('>');
  const [thresholdValue, setThresholdValue] = useState('');
  const [thresholdUnit, setThresholdUnit] = useState('');
  const [actuatorId, setActuatorId] = useState('');
  const [actuatorAction, setActuatorAction] = useState<'ON' | 'OFF'>('ON');

  const [sensorIds, setSensorIds] = useState<string[]>([]);
  const [actuatorIds, setActuatorIds] = useState<string[]>([]);

  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Fetch sensors and actuators on mount
  useEffect(() => {
    fetchSensorsLatest()
      .then((res) => {
        const ids = Object.keys(res.sensors);
        setSensorIds(ids.sort());
      })
      .catch(() => setSensorIds([]));

    fetchActuators()
      .then((res) => {
        const ids = Object.keys(res.actuators);
        setActuatorIds(ids.sort());
      })
      .catch(() => setActuatorIds([]));
  }, []);

  // Populate form when editingRule changes
  useEffect(() => {
    if (editingRule) {
      setName(editingRule.name ?? '');
      setDescription(editingRule.description ?? '');
      setSensorId(editingRule.sensor_id ?? '');
      setOperator(editingRule.operator ?? '>');
      setThresholdValue(
        editingRule.threshold_value != null
          ? String(editingRule.threshold_value)
          : '',
      );
      setThresholdUnit(editingRule.threshold_unit ?? '');
      setActuatorId(editingRule.actuator_id ?? '');
      setActuatorAction(editingRule.actuator_action === 'OFF' ? 'OFF' : 'ON');
    } else {
      setName('');
      setDescription('');
      setSensorId('');
      setOperator('>');
      setThresholdValue('');
      setThresholdUnit('');
      setActuatorId('');
      setActuatorAction('ON');
    }
    setError('');
  }, [editingRule]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!name.trim()) {
      setError('Name is required.');
      return;
    }
    if (!sensorId) {
      setError('Please select a sensor.');
      return;
    }
    if (!operator) {
      setError('Please select an operator.');
      return;
    }
    const parsedValue = Number(thresholdValue);
    if (thresholdValue.trim() === '' || isNaN(parsedValue)) {
      setError('Threshold value must be a valid number.');
      return;
    }
    if (!actuatorId) {
      setError('Please select an actuator.');
      return;
    }

    const payload: RulePayload = {
      name: name.trim(),
      description: description.trim() || undefined,
      sensor_id: sensorId,
      operator,
      threshold_value: parsedValue,
      threshold_unit: thresholdUnit.trim() || undefined,
      actuator_id: actuatorId,
      actuator_action: actuatorAction,
    };

    setSubmitting(true);
    try {
      if (editingRule) {
        await updateRule(editingRule.id, payload);
      } else {
        await createRule(payload);
      }
      onSaved();
    } catch (err: any) {
      setError(err?.message ?? 'An error occurred while saving the rule.');
    } finally {
      setSubmitting(false);
    }
  };

  const isEditing = Boolean(editingRule);

  return (
    <div className="max-w-[600px]">
      <h2 className="mb-4 text-xl font-semibold">
        {isEditing ? 'Edit Rule' : 'Create Rule'}
      </h2>

      <form
        onSubmit={handleSubmit}
        className="rounded-lg border border-gray-200 bg-white p-6"
      >
        {/* Name */}
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Rule Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter rule name"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Description */}
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Description (optional)
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter description"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* IF section */}
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          IF
        </div>

        {/* Sensor */}
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Sensor
          </label>
          <select
            value={sensorId}
            onChange={(e) => setSensorId(e.target.value)}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">Select a sensor</option>
            {sensorIds.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </div>

        {/* Operator */}
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Operator
          </label>
          <select
            value={operator}
            onChange={(e) => setOperator(e.target.value)}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            {OPERATORS.map((op) => (
              <option key={op} value={op}>
                {op}
              </option>
            ))}
          </select>
        </div>

        {/* Threshold Value */}
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Threshold Value
          </label>
          <input
            type="text"
            value={thresholdValue}
            onChange={(e) => setThresholdValue(e.target.value)}
            placeholder="Enter threshold value"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Threshold Unit */}
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Threshold Unit (optional)
          </label>
          <input
            type="text"
            value={thresholdUnit}
            onChange={(e) => setThresholdUnit(e.target.value)}
            placeholder="e.g. C, %, ppm"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Divider between IF and THEN */}
        <div className="my-5 border-t border-gray-200" />

        {/* THEN section */}
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          THEN
        </div>

        {/* Actuator */}
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Actuator
          </label>
          <select
            value={actuatorId}
            onChange={(e) => setActuatorId(e.target.value)}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">Select an actuator</option>
            {actuatorIds.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </div>

        {/* Action toggle */}
        <div className="mb-6">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Action
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setActuatorAction('ON')}
              className={`flex-1 rounded-md border px-4 py-2 text-sm font-medium transition-colors ${
                actuatorAction === 'ON'
                  ? 'border-green-600 bg-green-500 text-white'
                  : 'border-gray-300 bg-gray-100 text-gray-600'
              }`}
            >
              ON
            </button>
            <button
              type="button"
              onClick={() => setActuatorAction('OFF')}
              className={`flex-1 rounded-md border px-4 py-2 text-sm font-medium transition-colors ${
                actuatorAction === 'OFF'
                  ? 'border-red-600 bg-red-500 text-white'
                  : 'border-gray-300 bg-gray-100 text-gray-600'
              }`}
            >
              OFF
            </button>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {submitting
            ? 'Saving...'
            : isEditing
              ? 'Update Rule'
              : 'Create Rule'}
        </button>

        {/* Error message */}
        {error && (
          <p className="mt-3 text-sm text-red-600">{error}</p>
        )}
      </form>
    </div>
  );
}
