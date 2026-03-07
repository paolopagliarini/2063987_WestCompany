export function TelemetryPage() {
  const charts = [
    { title: 'Solar Array Power', unit: 'kW', maxValue: 50 },
    { title: 'Radiation Level', unit: 'μSv/h', maxValue: 100 },
    { title: 'Power Consumption', unit: 'kW', maxValue: 40 },
    { title: 'Thermal Loop Temperature', unit: '°C', maxValue: 100 }
  ];

  return (
    <div>
      <h2 className="mb-6 text-[20px]">Real-Time Telemetry</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {charts.map((chart, idx) => (
          <div key={idx} className="bg-white border-2 border-[#333] p-4">
            <h3 className="mb-3 text-[16px]">{chart.title}</h3>
            <div className="border-2 border-[#999] p-4 bg-[#f9f9f9] h-[280px] flex flex-col">
              <div className="text-[11px] text-[#666] mb-2">VALUE ({chart.unit})</div>

              <div className="flex-1 relative">
                <svg className="w-full h-full" viewBox="0 0 350 180" preserveAspectRatio="xMidYMid meet">
                  {/* Grid lines */}
                  {Array.from({ length: 5 }, (_, i) => (
                    <line
                      key={`grid-y-${i}`}
                      x1="40"
                      y1={20 + i * 30}
                      x2="330"
                      y2={20 + i * 30}
                      stroke="#ddd"
                      strokeWidth="1"
                      strokeDasharray="2,2"
                    />
                  ))}

                  {/* Y-axis */}
                  <line x1="40" y1="20" x2="40" y2="140" stroke="#333" strokeWidth="2" />
                  
                  {/* X-axis */}
                  <line x1="40" y1="140" x2="330" y2="140" stroke="#333" strokeWidth="2" />

                  {/* Y-axis labels and ticks */}
                  {Array.from({ length: 5 }, (_, i) => {
                    const value = chart.maxValue - (i * chart.maxValue / 4);
                    const y = 20 + i * 30;
                    return (
                      <g key={`y-tick-${i}`}>
                        <line
                          x1="38"
                          y1={y}
                          x2="42"
                          y2={y}
                          stroke="#333"
                          strokeWidth="2"
                        />
                        <text
                          x="35"
                          y={y + 4}
                          textAnchor="end"
                          className="text-[10px]"
                          fill="#666"
                        >
                          {Math.round(value)}
                        </text>
                      </g>
                    );
                  })}

                  {/* X-axis labels and ticks */}
                  {Array.from({ length: 7 }, (_, i) => {
                    const x = 40 + i * 48.33;
                    const timeLabel = `-${6 - i}m`;
                    return (
                      <g key={`x-tick-${i}`}>
                        <line
                          x1={x}
                          y1="138"
                          x2={x}
                          y2="142"
                          stroke="#333"
                          strokeWidth="2"
                        />
                        <text
                          x={x}
                          y="155"
                          textAnchor="middle"
                          className="text-[10px]"
                          fill="#666"
                        >
                          {timeLabel}
                        </text>
                      </g>
                    );
                  })}

                  {/* Data line */}
                  <polyline
                    points="40,90 88,75 136,85 184,60 232,70 280,50 328,65"
                    fill="none"
                    stroke="#666"
                    strokeWidth="2.5"
                  />
                </svg>
              </div>

              <div className="text-[11px] text-[#666] mt-2 text-center">TIME (minutes ago)</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}