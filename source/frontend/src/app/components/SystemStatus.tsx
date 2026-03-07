export function SystemStatus() {
  const services = [
    {
      name: 'Message Broker',
      id: 'mqtt_broker',
      status: 'Running',
      uptime: '48h 23m',
      details: 'Port: 1883 | Clients: 12'
    },
    {
      name: 'Ingestion Service',
      id: 'data_ingestion',
      status: 'Running',
      uptime: '48h 23m',
      details: 'Messages/sec: 24 | Queue: 0'
    },
    {
      name: 'Automation Engine',
      id: 'rule_engine',
      status: 'Running',
      uptime: '48h 23m',
      details: 'Active Rules: 4 | Last eval: 1s ago'
    },
    {
      name: 'Frontend WebSocket',
      id: 'websocket',
      status: 'Connected',
      uptime: '2h 15m',
      details: 'Latency: 12ms | Messages: 1,247'
    }
  ];

  return (
    <div>
      <h2 className="mb-6 text-[20px]">System Status</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {services.map((service, idx) => (
          <div key={idx} className="bg-white border-2 border-[#333] p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-[16px] mb-1">{service.name}</h3>
                <div className="text-[12px] text-[#666] font-mono">{service.id}</div>
              </div>
              <div className={`px-3 py-1 border-2 text-[14px] ${
                service.status === 'Running' || service.status === 'Connected'
                  ? 'bg-[#90EE90] border-[#006400]'
                  : 'bg-[#FFB6C1] border-[#8B0000]'
              }`}>
                {service.status}
              </div>
            </div>

            <div className="border-t-2 border-[#ddd] pt-4 space-y-2">
              <div className="flex justify-between text-[14px]">
                <span className="text-[#666]">Uptime:</span>
                <span className="font-mono">{service.uptime}</span>
              </div>
              <div className="flex justify-between text-[14px]">
                <span className="text-[#666]">Details:</span>
                <span className="font-mono text-[12px]">{service.details}</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t-2 border-[#ddd]">
              <div className="text-[11px] text-[#666] mb-2">LOAD</div>
              <div className="flex items-end gap-1 h-[30px]">
                {Array.from({ length: 20 }, (_, i) => (
                  <div
                    key={i}
                    className="flex-1 bg-[#4169E1]"
                    style={{ height: `${20 + Math.random() * 80}%` }}
                  />
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 bg-white border-2 border-[#333] p-6">
        <h3 className="text-[16px] mb-4">System Logs</h3>
        <div className="bg-[#1e1e1e] text-[#00ff00] font-mono text-[12px] p-4 h-[200px] overflow-auto">
          <div>[2026-03-06 14:23:45] INFO: Data ingestion service started</div>
          <div>[2026-03-06 14:23:47] INFO: Connected to message broker</div>
          <div>[2026-03-06 14:23:48] INFO: Automation engine initialized</div>
          <div>[2026-03-06 14:23:50] INFO: Loaded 4 automation rules</div>
          <div>[2026-03-06 14:24:12] INFO: Sensor data received: temperature=22.5</div>
          <div>[2026-03-06 14:24:15] INFO: Rule R001 evaluated: condition=false</div>
          <div>[2026-03-06 14:24:18] INFO: Sensor data received: humidity=45</div>
          <div>[2026-03-06 14:24:21] INFO: WebSocket client connected</div>
        </div>
      </div>
    </div>
  );
}
