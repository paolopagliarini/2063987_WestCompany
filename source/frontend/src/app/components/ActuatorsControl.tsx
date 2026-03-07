import { useState } from 'react';

export function ActuatorsControl() {
  const [actuators, setActuators] = useState([
    { name: 'cooling_fan', label: 'Cooling Fan', state: false },
    { name: 'entrance_humidifier', label: 'Entrance Humidifier', state: true },
    { name: 'hall_ventilation', label: 'Hall Ventilation', state: false },
    { name: 'habitat_heater', label: 'Habitat Heater', state: true }
  ]);

  const toggleActuator = (index: number) => {
    const newActuators = [...actuators];
    newActuators[index].state = !newActuators[index].state;
    setActuators(newActuators);
  };

  return (
    <div>
      <h2 className="mb-6 text-[20px]">Actuator Control</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {actuators.map((actuator, idx) => (
          <div key={idx} className="bg-white border-2 border-[#333] p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="text-[16px]">{actuator.label}</div>
              <div className={`px-3 py-1 border-2 ${
                actuator.state
                  ? 'bg-[#90EE90] border-[#006400]'
                  : 'bg-[#FFB6C1] border-[#8B0000]'
              } text-[14px]`}>
                {actuator.state ? 'ON' : 'OFF'}
              </div>
            </div>

            <div className="text-[12px] text-[#666] mb-3">
              ID: {actuator.name}
            </div>

            <button
              onClick={() => toggleActuator(idx)}
              className="w-full border-2 border-[#333] bg-[#e0e0e0] px-4 py-3 hover:bg-[#d0d0d0]"
            >
              [ TOGGLE ]
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
