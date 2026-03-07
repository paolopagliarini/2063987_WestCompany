export function RuleList() {
  const rules = [
    {
      id: 'R001',
      condition: 'temperature > 25',
      action: 'cooling_fan = ON',
      status: 'Active',
      lastTriggered: '2 min ago'
    },
    {
      id: 'R002',
      condition: 'humidity < 40',
      action: 'entrance_humidifier = ON',
      status: 'Active',
      lastTriggered: '15 min ago'
    },
    {
      id: 'R003',
      condition: 'co2 > 600',
      action: 'hall_ventilation = ON',
      status: 'Active',
      lastTriggered: 'Never'
    },
    {
      id: 'R004',
      condition: 'temperature < 18',
      action: 'habitat_heater = ON',
      status: 'Inactive',
      lastTriggered: '3 hours ago'
    }
  ];

  return (
    <div>
      <h2 className="mb-6 text-[20px]">Active Automation Rules</h2>
      <div className="bg-white border-2 border-[#333]">
        <div className="grid grid-cols-5 gap-4 bg-[#e0e0e0] border-b-2 border-[#333] p-4">
          <div className="text-[14px]">Rule ID</div>
          <div className="text-[14px]">Condition</div>
          <div className="text-[14px]">Action</div>
          <div className="text-[14px]">Status</div>
          <div className="text-[14px]">Last Triggered</div>
        </div>

        {rules.map((rule, idx) => (
          <div
            key={rule.id}
            className={`grid grid-cols-5 gap-4 p-4 ${
              idx < rules.length - 1 ? 'border-b-2 border-[#ddd]' : ''
            }`}
          >
            <div className="text-[14px] font-mono">{rule.id}</div>
            <div className="text-[14px] font-mono">{rule.condition}</div>
            <div className="text-[14px] font-mono">{rule.action}</div>
            <div>
              <span className={`inline-block px-2 py-1 border-2 text-[12px] ${
                rule.status === 'Active'
                  ? 'bg-[#90EE90] border-[#006400]'
                  : 'bg-[#FFD700] border-[#8B8000]'
              }`}>
                {rule.status}
              </span>
            </div>
            <div className="text-[14px] text-[#666]">{rule.lastTriggered}</div>
          </div>
        ))}
      </div>

      <div className="mt-4 flex gap-2">
        <button className="border-2 border-[#333] bg-[#e0e0e0] px-4 py-2 hover:bg-[#d0d0d0]">
          [ EDIT ]
        </button>
        <button className="border-2 border-[#333] bg-[#FFB6C1] px-4 py-2 hover:bg-[#ff9fb1]">
          [ DELETE ]
        </button>
        <button className="border-2 border-[#333] bg-[#e0e0e0] px-4 py-2 hover:bg-[#d0d0d0]">
          [ ENABLE/DISABLE ]
        </button>
      </div>
    </div>
  );
}
