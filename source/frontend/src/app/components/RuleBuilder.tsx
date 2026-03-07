import { useState } from 'react';

export function RuleBuilder() {
  const [sensor, setSensor] = useState('');
  const [operator, setOperator] = useState('>');
  const [value, setValue] = useState('');
  const [actuator, setActuator] = useState('');
  const [action, setAction] = useState('ON');

  const sensors = [
    'temperature',
    'humidity',
    'co2',
    'water_tank_level',
    'air_quality'
  ];

  const actuators = [
    'cooling_fan',
    'entrance_humidifier',
    'hall_ventilation',
    'habitat_heater'
  ];

  const operators = ['<', '<=', '=', '>', '>='];

  const handleCreate = () => {
    if (sensor && value && actuator) {
      alert(`Rule created:\nIF ${sensor} ${operator} ${value}\nTHEN ${actuator} = ${action}`);
    } else {
      alert('Please fill all fields');
    }
  };

  return (
    <div>
      <h2 className="mb-6 text-[20px]">Rule Builder</h2>
      <div className="bg-white border-2 border-[#333] p-6 max-w-2xl">
        <div className="space-y-4">
          <div>
            <label className="block text-[14px] mb-2">IF Sensor</label>
            <select
              value={sensor}
              onChange={(e) => setSensor(e.target.value)}
              className="w-full border-2 border-[#999] bg-white px-3 py-2"
            >
              <option value="">[ Select Sensor ]</option>
              {sensors.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[14px] mb-2">Operator</label>
            <select
              value={operator}
              onChange={(e) => setOperator(e.target.value)}
              className="w-full border-2 border-[#999] bg-white px-3 py-2"
            >
              {operators.map(op => (
                <option key={op} value={op}>{op}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[14px] mb-2">Value</label>
            <input
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="[ Enter value ]"
              className="w-full border-2 border-[#999] bg-white px-3 py-2"
            />
          </div>

          <div className="border-t-2 border-[#999] pt-4 mt-4">
            <div className="text-[14px] mb-4">THEN</div>

            <div className="mb-4">
              <label className="block text-[14px] mb-2">Actuator</label>
              <select
                value={actuator}
                onChange={(e) => setActuator(e.target.value)}
                className="w-full border-2 border-[#999] bg-white px-3 py-2"
              >
                <option value="">[ Select Actuator ]</option>
                {actuators.map(a => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[14px] mb-2">Action</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setAction('ON')}
                  className={`flex-1 border-2 px-4 py-2 ${
                    action === 'ON'
                      ? 'bg-[#90EE90] border-[#006400]'
                      : 'bg-[#e0e0e0] border-[#999]'
                  }`}
                >
                  [ ON ]
                </button>
                <button
                  onClick={() => setAction('OFF')}
                  className={`flex-1 border-2 px-4 py-2 ${
                    action === 'OFF'
                      ? 'bg-[#FFB6C1] border-[#8B0000]'
                      : 'bg-[#e0e0e0] border-[#999]'
                  }`}
                >
                  [ OFF ]
                </button>
              </div>
            </div>
          </div>

          <button
            onClick={handleCreate}
            className="w-full border-2 border-[#333] bg-[#4169E1] text-white px-6 py-3 mt-4 hover:bg-[#315bb5]"
          >
            [ CREATE RULE ]
          </button>
        </div>
      </div>
    </div>
  );
}
