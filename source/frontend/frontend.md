# Frontend

Web interface for the Mars Habitat Automation Platform.

## Responsibilities

- Real-time dashboard for sensor visualization
- Automation rule management (CRUD)
- Manual actuator control
- System status monitoring
- Streaming telemetry visualization

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | React 18 |
| Build Tool | Vite 6 |
| Routing | React Router 7 |
| UI Components | Radix UI (shadcn/ui style) |
| Styling | Tailwind CSS 4 |
| Charts | Recharts |
| State | React hooks (useState, useEffect) |
| Icons | Lucide React |

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx              # Main component with navigation
│   │   └── components/
│   │       ├── SensorDashboard.tsx    # REST sensors dashboard
│   │       ├── TelemetryPage.tsx       # Streaming telemetry page
│   │       ├── ActuatorsControl.tsx    # Actuator control
│   │       ├── RuleBuilder.tsx         # Rule creation/editing
│   │       ├── RuleList.tsx             # Existing rules list
│   │       ├── SystemStatus.tsx         # Service status
│   │       └── ui/                      # Radix UI components
│   └── main.tsx
├── package.json
├── vite.config.ts
└── Dockerfile
```

## Application Pages

### 1. Sensors (`SensorDashboard`)
- Displays all REST sensors in real time
- Periodic polling from ingestion service `/sensors/latest` endpoint
- Cards with current value, unit, status

### 2. Telemetry (`TelemetryPage`)
- Displays streaming data from telemetry sensors
- SSE connection for real-time updates
- Charts with Recharts for trends

### 3. Actuators (`ActuatorsControl`)
- Lists actuators with current state
- ON/OFF controls for manual operation
- Command history per actuator

### 4. Rule Builder (`RuleBuilder`)
- Form to create new rules
- Sensor, operator, threshold value selection
- Actuator and action selection
- Supports editing existing rules

### 5. Rules (`RuleList`)
- Table of all rules
- Enable/disable toggle
- Edit button (opens RuleBuilder)
- Rule deletion

### 6. Status (`SystemStatus`)
- Health check for all services
- RabbitMQ, Database connection status
- Statistics for each service

## API Endpoints Used

| Service | Endpoint | Usage |
|---------|----------|-------|
| ingestion | `GET /sensors/latest` | Latest sensor values |
| ingestion | `GET /sensors/latest/{id}` | Specific sensor value |
| actuator-control | `GET /actuators` | List actuators |
| actuator-control | `POST /actuators/{id}` | Manual control |
| actuator-control | `GET /actuators/{id}/history` | Command history |
| rule-manager | `GET /rules` | List rules |
| rule-manager | `POST /rules` | Create rule |
| rule-manager | `PUT /rules/{id}` | Update rule |
| rule-manager | `DELETE /rules/{id}` | Delete rule |
| rule-manager | `PATCH /rules/{id}/toggle` | Enable/disable |
| notification | `GET /notifications/stream` | SSE real-time notifications |
| notification | `GET /notifications` | List notifications |
| data-history | `GET /history` | History query |
| data-history | `GET /history/{id}/aggregate` | Aggregations |
| automation-engine | `GET /health` | Engine status |
| automation-engine | `GET /rules/active` | Active rules |

## SSE Connection for Notifications

```javascript
const eventSource = new EventSource('http://localhost:8004/notifications/stream');

eventSource.addEventListener('connected', (event) => {
  console.log('Connected to notification stream');
});

eventSource.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  // Update UI with notification
};
```

## Development Commands

```bash
# Install dependencies
cd source/frontend
npm install

# Start development server
npm run dev

# Production build
npm run build
```

## Docker Compose Configuration

```yaml
frontend:
  build: ./frontend
  container_name: frontend
  restart: always
  ports:
    - "5173:5173"
  depends_on:
    - ingestion
    - actuator-control-service
    - rule-manager-service
    - notification-service
    - data-history-service
    - automation-engine
```

## Environment Variables

The frontend can be configured with environment variables for API endpoints:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_INGESTION_URL` | `http://localhost:8001` | Ingestion service URL |
| `VITE_ACTUATOR_URL` | `http://localhost:8005` | Actuator control URL |
| `VITE_RULE_URL` | `http://localhost:8003` | Rule manager URL |
| `VITE_NOTIFICATION_URL` | `http://localhost:8004` | Notification service URL |
| `VITE_HISTORY_URL` | `http://localhost:8006` | Data history URL |

## UI Components

Components in the `ui/` folder follow the shadcn/ui pattern:
- Based on Radix UI primitives
- Styled with Tailwind CSS
- Fully typed with TypeScript
- Accessible and keyboard-friendly

Components used:
- `Button`, `Input`, `Select` for forms
- `Card`, `Badge` for display
- `Dialog`, `AlertDialog` for modals
- `Table` for lists
- `Tabs` for alternative navigation
- `Chart` for graphs (Recharts wrapper)

## Data Flow

```
User → Frontend (React)
         ↓
    API Call (fetch/axios)
         ↓
    Backend Service
         ↓
    Database/RabbitMQ
         ↓
    Response JSON
         ↓
    Frontend (state update)
         ↓
    UI Re-render
```

For real-time notifications:
```
Backend → RabbitMQ → Notification Service
                              ↓
                        SSE Stream
                              ↓
                    Frontend (EventSource)
                              ↓
                        UI Update
```