// ---------------------------------------------------------------------------
// Mars Habitat Automation Platform – API layer
// ---------------------------------------------------------------------------

// ---- Data types -----------------------------------------------------------

export interface SensorEvent {
  event_id: string;
  sensor_id: string;
  timestamp: string;
  metric: string;
  value: number;
  unit: string;
  source: string;
  status: string;
  raw_schema: string;
}

export interface Actuator {
  actuator_id: string;
  state: string;
  updated_at: string;
}

export interface ActuatorCommand {
  id: number;
  actuator_id: string;
  previous_state: string;
  new_state: string;
  source: string;
  reason: string;
  rule_id: number | null;
  executed_at: string;
}

export interface Rule {
  id: number;
  name: string;
  description: string | null;
  sensor_id: string;
  operator: string;
  threshold_value: number;
  threshold_unit: string | null;
  actuator_id: string;
  actuator_action: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RulePayload {
  name: string;
  description?: string;
  sensor_id: string;
  operator: string;
  threshold_value: number;
  threshold_unit?: string;
  actuator_id: string;
  actuator_action: string;
}

export interface Notification {
  notification_id: string;
  event_id: string;
  sensor_id: string;
  metric: string;
  value: number;
  unit: string;
  status: string;
  rule_id: number | null;
  rule_name: string | null;
  actuator_id: string | null;
  actuator_action: string | null;
  message: string;
  timestamp: string;
  severity: string;
}

// ---- Response shapes ------------------------------------------------------

export interface SensorsLatestResponse {
  count: number;
  sensors: Record<string, SensorEvent>;
}

export interface ActuatorsResponse {
  count: number;
  actuators: Record<string, Actuator>;
}

export interface ActuatorToggleResponse {
  actuator_id: string;
  state: string;
  message: string;
}

export interface ActuatorHistoryResponse {
  count: number;
  commands: ActuatorCommand[];
}

export interface RulesResponse {
  count: number;
  rules: Rule[];
}

export interface NotificationsResponse {
  count: number;
  notifications: Notification[];
}

export interface HealthResponse {
  status: string;
  [key: string]: unknown;
}

// ---- Helpers --------------------------------------------------------------

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

let lastSensorId = 0;
const cachedSensorsData: Record<string, SensorEvent> = {};

export async function fetchSensorsLatest(): Promise<SensorsLatestResponse> {
  const res = await request<{ last_id: number; count: number; events: SensorEvent[] }>(
    `/api/history/sensors/latest?last_id=${lastSensorId}`
  );

  if (res.events && res.events.length > 0) {
    lastSensorId = res.last_id;
    for (const ev of res.events) {
      const key = `${ev.sensor_id}_${ev.metric}`;
      cachedSensorsData[key] = { ...ev };
    }
  }

  return {
    count: Object.keys(cachedSensorsData).length,
    sensors: { ...cachedSensorsData },
  };
}

// ---- Actuators ------------------------------------------------------------

export function fetchActuators(): Promise<ActuatorsResponse> {
  return request<ActuatorsResponse>('/api/actuators/actuators');
}

export function toggleActuator(
  id: string,
  state: 'ON' | 'OFF',
): Promise<ActuatorToggleResponse> {
  return request<ActuatorToggleResponse>(`/api/actuators/actuators/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state }),
  });
}

export function fetchActuatorHistory(
  id: string,
): Promise<ActuatorHistoryResponse> {
  return request<ActuatorHistoryResponse>(
    `/api/actuators/actuators/${id}/history`,
  );
}

// ---- Rules ----------------------------------------------------------------

export function fetchRules(): Promise<RulesResponse> {
  return request<RulesResponse>('/api/rules/rules');
}

export async function createRule(payload: RulePayload): Promise<Rule> {
  const rule = await request<Rule>('/api/rules/rules', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  await reloadAutomationRules().catch(console.error);
  return rule;
}

export async function updateRule(
  id: number,
  payload: Partial<RulePayload>,
): Promise<Rule> {
  const rule = await request<Rule>(`/api/rules/rules/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  await reloadAutomationRules().catch(console.error);
  return rule;
}

export async function deleteRule(id: number): Promise<void> {
  await request<void>(`/api/rules/rules/${id}`, { method: 'DELETE' });
  await reloadAutomationRules().catch(console.error);
}

export async function toggleRule(id: number): Promise<Rule> {
  const rule = await request<Rule>(`/api/rules/rules/${id}/toggle`, { method: 'PATCH' });
  await reloadAutomationRules().catch(console.error);
  return rule;
}

function reloadAutomationRules(): Promise<void> {
  return request<void>('/api/automation/rules/reload', { method: 'POST' });
}

// ---- Notifications --------------------------------------------------------

export function fetchNotifications(
  limit: number = 50,
): Promise<NotificationsResponse> {
  return request<NotificationsResponse>(
    `/api/notifications/notifications?limit=${limit}`,
  );
}

/** SSE endpoint for real-time notification streaming. */
export const NOTIFICATIONS_STREAM_URL =
  '/api/notifications/notifications/stream';

// ---- Health ---------------------------------------------------------------

export function fetchIngestionHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/ingestion/health');
}

export function fetchAutomationHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/automation/health');
}

export function fetchRulesHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/rules/health');
}

export function fetchNotificationsHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/notifications/health');
}

export function fetchActuatorsHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/actuators/health');
}

export function fetchHistoryHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/history/health');
}
