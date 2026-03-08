import { useState, useEffect } from 'react';
import { Toaster } from 'sonner';
import { SensorDashboard } from './components/SensorDashboard';
import { TelemetryPage } from './components/TelemetryPage';
import { ActuatorsControl } from './components/ActuatorsControl';
import { RuleBuilder } from './components/RuleBuilder';
import { RuleList } from './components/RuleList';
import { SystemStatus } from './components/SystemStatus';

const tabs = [
  { id: 'sensors', label: 'Sensors' },
  { id: 'telemetry', label: 'Telemetry' },
  { id: 'actuators', label: 'Actuators' },
  { id: 'rule-builder', label: 'Rule Builder' },
  { id: 'rules', label: 'Rules' },
  { id: 'status', label: 'Status' },
];

export default function App() {
  const [currentPage, setCurrentPage] = useState<string>(() => {
    return localStorage.getItem('currentPage') || 'sensors';
  });
  const [editingRule, setEditingRule] = useState<any | null>(null);

  useEffect(() => {
    localStorage.setItem('currentPage', currentPage);
  }, [currentPage]);

  const handleEditRule = (rule: any) => {
    setEditingRule(rule);
    setCurrentPage('rule-builder');
  };

  const handleRuleSaved = () => {
    setEditingRule(null);
    setCurrentPage('rules');
  };

  const handleTabClick = (tabId: string) => {
    if (tabId !== 'rule-builder') {
      setEditingRule(null);
    }
    setCurrentPage(tabId);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'sensors':
        return <SensorDashboard />;
      case 'telemetry':
        return <TelemetryPage />;
      case 'actuators':
        return <ActuatorsControl />;
      case 'rule-builder':
        return <RuleBuilder editingRule={editingRule} onSaved={handleRuleSaved} />;
      case 'rules':
        return <RuleList onEditRule={handleEditRule} />;
      case 'status':
        return <SystemStatus />;
      default:
        return <SensorDashboard />;
    }
  };

  return (
    <div className="size-full bg-background text-foreground flex flex-col">
      <Toaster position="top-right" />

      <header className="bg-background border-b border-border px-6 py-4">
        <h1 className="text-xl font-semibold">Mars Habitat Dashboard</h1>
      </header>

      <nav className="bg-background border-b border-border px-6 py-2">
        <div className="flex gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${currentPage === tab.id
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="flex-1 overflow-auto p-6">
        {renderPage()}
      </main>
    </div>
  );
}
