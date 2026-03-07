import { useState } from 'react';
import { SensorDashboard } from './components/SensorDashboard';
import { TelemetryPage } from './components/TelemetryPage';
import { ActuatorsControl } from './components/ActuatorsControl';
import { RuleBuilder } from './components/RuleBuilder';
import { RuleList } from './components/RuleList';
import { SystemStatus } from './components/SystemStatus';

export default function App() {
  const [currentPage, setCurrentPage] = useState('sensors');

  const renderPage = () => {
    switch (currentPage) {
      case 'sensors':
        return <SensorDashboard />;
      case 'telemetry':
        return <TelemetryPage />;
      case 'actuators':
        return <ActuatorsControl />;
      case 'rule-builder':
        return <RuleBuilder />;
      case 'rule-list':
        return <RuleList />;
      case 'system-status':
        return <SystemStatus />;
      default:
        return <SensorDashboard />;
    }
  };

  return (
    <div className="size-full bg-[#f5f5f5] flex flex-col">
      <header className="bg-white border-b-2 border-[#333] px-6 py-4">
        <h1 className="text-[24px] font-normal">MARS HABITAT AUTOMATION DASHBOARD</h1>
      </header>

      <nav className="bg-[#e0e0e0] border-b-2 border-[#999] px-6 py-2">
        <div className="flex gap-2">
          {[
            { id: 'sensors', label: '[Sensors]' },
            { id: 'telemetry', label: '[Telemetry]' },
            { id: 'actuators', label: '[Actuators]' },
            { id: 'rule-builder', label: '[Rule Builder]' },
            { id: 'rule-list', label: '[Rules]' },
            { id: 'system-status', label: '[Status]' }
          ].map(page => (
            <button
              key={page.id}
              onClick={() => setCurrentPage(page.id)}
              className={`px-4 py-2 border-2 ${
                currentPage === page.id
                  ? 'bg-white border-[#333]'
                  : 'bg-[#d0d0d0] border-[#999]'
              }`}
            >
              {page.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="flex-1 p-6 overflow-auto">
        {renderPage()}
      </main>
    </div>
  );
}