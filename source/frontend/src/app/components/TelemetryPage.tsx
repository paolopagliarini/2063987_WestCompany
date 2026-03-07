export function TelemetryPage() {
  const charts = [
    { title: 'Solar Array Power', unit: 'kW', maxValue: 50 },
    { title: 'Radiation Level', unit: 'μSv/h', maxValue: 100 },
    { title: 'Power Consumption', unit: 'kW', maxValue: 40 },
    { title: 'Thermal Loop Temperature', unit: '°C', maxValue: 100 }
  ];

  return (
    <div>
      <h2 className="mb-4 text-[20px]">Real-Time Telemetry</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {charts.map((chart, idx) => (
          <div key={idx} className="bg-white border-2 border-[#333] p-3">
            <h3 className="mb-2 text-[16px]">{chart.title}</h3>
            <div className="border-2 border-[#999] p-3 bg-[#f9f9f9] h-[180px] flex flex-col">
              <div className="text-[11px] text-[#666] mb-1">VALUE ({chart.unit})</div>

              <div className="flex-1 relative min-h-0">
                <svg className="w-full h-full" viewBox="0 0 350 140" preserveAspectRatio="none">
                  {/* Grid lines */}
                  {Array.from({ length: 4 }, (_, i) => (
                    <line
                      key={`grid-y-${i}`}
                      x1="50"
                      y1={15 + i * 25}
                      x2="340"
                      y2={15 + i * 25}
                      stroke="#ddd"
                      strokeWidth="1"
                      strokeDasharray="3,3"
                      vectorEffect="non-scaling-stroke"
                    />
                  ))}

                  {/* Y-axis */}
                  <line x1="50" y1="15" x2="50" y2="105" stroke="#333" strokeWidth="2" vectorEffect="non-scaling-stroke" />
                  
                  {/* X-axis */}
                  <line x1="50" y1="105" x2="340" y2="105" stroke="#333" strokeWidth="2" vectorEffect="non-scaling-stroke" />

                  {/* Y-axis labels and ticks */}
                  {Array.from({ length: 4 }, (_, i) => {
                    const value = chart.maxValue - (i * chart.maxValue / 3);
                    const y = 15 + i * 25;
                    return (
                      <g key={`y-tick-${i}`}>
                        <line
                          x1="47"
                          y1={y}
                          x2="53"
                          y2={y}
                          stroke="#333"
                          strokeWidth="2"
                          vectorEffect="non-scaling-stroke"
                        />
                        <text
                          x="43"
                          y={y + 3}
                          textAnchor="end"
                          fontSize="10"
                          fill="#666"
                        >
                          {Math.round(value)}
                        </text>
                      </g>
                    );
                  })}

                  {/* X-axis labels and ticks */}
                  {Array.from({ length: 7 }, (_, i) => {
                    const x = 50 + i * 48.33;
                    const timeLabel = `-${6 - i}m`;
                    return (
                      <g key={`x-tick-${i}`}>
                        <line
                          x1={x}
                          y1="102"
                          x2={x}
                          y2="108"
                          stroke="#333"
                          strokeWidth="2"
                          vectorEffect="non-scaling-stroke"
                        />
                        <text
                          x={x}
                          y="120"
                          textAnchor="middle"
                          fontSize="10"
                          fill="#666"
                        >
                          {timeLabel}
                        </text>
                      </g>
                    );
                  })}

                  {/* Data line */}
                  <polyline
                    points="50,70 98.33,55 146.66,62 195,45 243.33,52 291.66,38 340,48"
                    fill="none"
                    stroke="#666"
                    strokeWidth="2.5"
                    vectorEffect="non-scaling-stroke"
                  />
                </svg>
              </div>

              <div className="text-[11px] text-[#666] mt-1 text-center">TIME (minutes ago)</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}