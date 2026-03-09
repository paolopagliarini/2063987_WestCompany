# Frontend

Interfaccia web della Mars Habitat Automation Platform.

## Responsabilità

- Dashboard real-time per visualizzazione sensori
- Gestione regole di automazione (CRUD)
- Controllo manuale attuatori
- Monitoraggio stato sistema
- Visualizzazione telemetria streaming

## Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| Framework | React 18 |
| Build Tool | Vite 6 |
| Routing | React Router 7 |
| UI Components | Radix UI (shadcn/ui style) |
| Styling | Tailwind CSS 4 |
| Charts | Recharts |
| State | React hooks (useState, useEffect) |
| Icons | Lucide React |

## Struttura Progetto

```
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx              # Componente principale con navigazione
│   │   └── components/
│   │       ├── SensorDashboard.tsx    # Dashboard sensori REST
│   │       ├── TelemetryPage.tsx       # Pagina telemetria streaming
│   │       ├── ActuatorsControl.tsx    # Controllo attuatori
│   │       ├── RuleBuilder.tsx         # Creazione/modifica regole
│   │       ├── RuleList.tsx             # Lista regole esistenti
│   │       ├── SystemStatus.tsx         # Stato servizi
│   │       └── ui/                      # Componenti Radix UI
│   └── main.tsx
├── package.json
├── vite.config.ts
└── Dockerfile
```

## Pagine dell'Applicazione

### 1. Sensors (`SensorDashboard`)
- Visualizza tutti i sensori REST in tempo reale
- Polling periodico dall'endpoint `/sensors/latest` dell'ingestion service
- Card con valore attuale, unità, stato

### 2. Telemetry (`TelemetryPage`)
- Visualizza dati streaming dai sensori telemetria
- Connessione SSE per aggiornamenti real-time
- Grafici con Recharts per trend

### 3. Actuators (`ActuatorsControl`)
- Lista attuatori con stato attuale
- Controlli ON/OFF per azionamento manuale
- Storico comandi per attuatore

### 4. Rule Builder (`RuleBuilder`)
- Form per creare nuove regole
- Selezione sensore, operatore, valore soglia
- Selezione attuatore e azione
- Supporta modifica regole esistenti

### 5. Rules (`RuleList`)
- Tabella tutte le regole
- Attivazione/disattivazione toggle
- Pulsante modifica (apre RuleBuilder)
- Eliminazione regole

### 6. Status (`SystemStatus`)
- Health check di tutti i servizi
- Stato connessioni RabbitMQ, Database
- Statistiche per ogni servizio

## Endpoint API Utilizzati

| Servizio | Endpoint | Uso |
|----------|----------|-----|
| ingestion | `GET /sensors/latest` | Ultimi valori sensori |
| ingestion | `GET /sensors/latest/{id}` | Valore sensore specifico |
| actuator-control | `GET /actuators` | Lista attuatori |
| actuator-control | `POST /actuators/{id}` | Controllo manuale |
| actuator-control | `GET /actuators/{id}/history` | Storico comandi |
| rule-manager | `GET /rules` | Lista regole |
| rule-manager | `POST /rules` | Crea regola |
| rule-manager | `PUT /rules/{id}` | Modifica regola |
| rule-manager | `DELETE /rules/{id}` | Elimina regola |
| rule-manager | `PATCH /rules/{id}/toggle` | Attiva/disattiva |
| notification | `GET /notifications/stream` | SSE notifiche real-time |
| notification | `GET /notifications` | Lista notifiche |
| data-history | `GET /history` | Query storico |
| data-history | `GET /history/{id}/aggregate` | Aggregazioni |
| automation-engine | `GET /health` | Stato motore |
| automation-engine | `GET /rules/active` | Regole attive |

## Connessione SSE per Notifiche

```javascript
const eventSource = new EventSource('http://localhost:8004/notifications/stream');

eventSource.addEventListener('connected', (event) => {
  console.log('Connected to notification stream');
});

eventSource.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  // Aggiorna UI con la notifica
};
```

## Comandi di Sviluppo

```bash
# Installazione dipendenze
cd source/frontend
npm install

# Avvio development server
npm run dev

# Build per produzione
npm run build
```

## Configurazione Docker Compose

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

## Variabili d'Ambiente

Il frontend può essere configurato con variabili d'ambiente per gli endpoint API:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `VITE_INGESTION_URL` | `http://localhost:8001` | URL ingestion service |
| `VITE_ACTUATOR_URL` | `http://localhost:8005` | URL actuator control |
| `VITE_RULE_URL` | `http://localhost:8003` | URL rule manager |
| `VITE_NOTIFICATION_URL` | `http://localhost:8004` | URL notification service |
| `VITE_HISTORY_URL` | `http://localhost:8006` | URL data history |

## Componenti UI

I componenti nella cartella `ui/` seguono il pattern shadcn/ui:
- Basati su Radix UI primitives
- Styling con Tailwind CSS
- Completamente tipizzati con TypeScript
- Accessibili e keyboard-friendly

Componenti utilizzati:
- `Button`, `Input`, `Select` per form
- `Card`, `Badge` per visualizzazione
- `Dialog`, `AlertDialog` per modali
- `Table` per liste
- `Tabs` per navigazione alternativa
- `Chart` per grafici (Recharts wrapper)

## Flusso Dati

```
Utente → Frontend (React)
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

Per notifiche real-time:
```
Backend → RabbitMQ → Notification Service
                              ↓
                        SSE Stream
                              ↓
                    Frontend (EventSource)
                              ↓
                        UI Update
```