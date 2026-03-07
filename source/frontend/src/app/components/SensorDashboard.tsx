export function SensorDashboard() {
  const sensors = [
    { name: 'Temperature', value: '22.5', unit: '°C', lastUpdate: '2s ago' },
    { name: 'Humidity', value: '45', unit: '%', lastUpdate: '3s ago' },
    { name: 'CO2', value: '420', unit: 'ppm', lastUpdate: '1s ago' },
    { name: 'Water Tank Level', value: '78', unit: '%', lastUpdate: '5s ago' },
    { name: 'Air Quality', value: 'Good', unit: 'AQI', lastUpdate: '2s ago' }
  ];

  return (
    <div>
      <h2 className="mb-6 text-[20px]">Sensor Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sensors.map((sensor, idx) => (
          <div key={idx} className="bg-white border-2 border-[#333] p-4">
            <div className="mb-3">
              <div className="text-[14px] text-[#666] mb-1">{sensor.name}</div>
              <div className="text-[32px] font-normal">{sensor.value} <span className="text-[18px]">{sensor.unit}</span></div>
              <div className="text-[12px] text-[#999] mt-1">Last update: {sensor.lastUpdate}</div>
            </div>

            <div className="border-2 border-[#999] p-3 bg-[#f9f9f9]">
              <div className="text-[11px] text-[#666] mb-2">MINI CHART</div>
              <div className="flex items-end gap-1 h-[40px]">
                {Array.from({ length: 10 }, (_, i) => (
                  <div
                    key={i}
                    className="flex-1 bg-[#666]"
                    style={{ height: `${Math.random() * 100}%` }}
                  />
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
