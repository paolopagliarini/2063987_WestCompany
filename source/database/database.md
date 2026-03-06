Schema 
  Tabella principale: automation_rules                                                                                                                               
  ┌─────────────────┬───────────────┬──────────────────────────────────┐
  │      Campo      │     Tipo      │           Descrizione            │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ id              │ SERIAL PK     │ Identificativo univoco           │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ name            │ VARCHAR(100)  │ Nome della regola                │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ description     │ TEXT          │ Descrizione opzionale            │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ sensor_id       │ VARCHAR(100)  │ ID del sensore da monitorare     │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ operator        │ VARCHAR(10)   │ Operatore: <, <=, =, >, >=       │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ threshold_value │ DECIMAL(10,2) │ Valore soglia                    │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ threshold_unit  │ VARCHAR(20)   │ Unità di misura                  │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ actuator_id     │ VARCHAR(100)  │ ID dell'attuatore da controllare │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ actuator_action │ VARCHAR(20)   │ Azione: ON, OFF, OPEN, CLOSED    │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ is_active       │ BOOLEAN       │ Regola attiva/disattiva          │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ created_at      │ TIMESTAMP     │ Data creazione                   │
  ├─────────────────┼───────────────┼──────────────────────────────────┤
  │ updated_at      │ TIMESTAMP     │ Data ultima modifica             │
  └─────────────────┴───────────────┴──────────────────────────────────┘

  Tabelle opzionali (per analytics e audit):

  - sensor_readings - Storico letture sensori
  - actuator_commands - Storico comandi (con reference alla regola che li ha triggerati)