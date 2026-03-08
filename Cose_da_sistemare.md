# TODO

## 1. input.md
- [x] Valutare cosa mantenere della sezione successiva alla definizione dello **event schema**.

---

## 2. Student_doc.md
- [x] Popolare correttamente il file con tutte le informazioni richieste dal progetto.

---

## 3. Aggiornamento stato attuatori
- [x] Quando viene aggiunta una nuova regola, il sistema **non aggiorna lo stato degli attuatori automaticamente**.
- [x] Quando un attuatore non viene modificato lo stato ON -> ON rimane nella storia.

---

## 4. Polling del frontend
- [x] Il frontend effettua **polling sui microservizi ogni 5 secondi**.
- [x] Verificare se dovrebbe invece **consumare direttamente gli eventi dal message broker**.

È assolutamente corretto e normale che il frontend faccia polling ogni 5 secondi tramite un'API REST, e non dovresti modificare l'intero frontend.

Ecco perché l'architettura attuale va benissimo e perché non dovresti consumare direttamente gli eventi dal message broker nel frontend:

Sicurezza (Anti-pattern): Un frontend (React, nel browser) non dovrebbe mai connettersi direttamente a un message broker (RabbitMQ). Se lo facesse, saresti costretto a esporre le credenziali del database o del broker (es. mars_user e mars_password) all'interno del codice JavaScript del browser, rendendo il sistema gravemente vulnerabile.
Protocolli non supportati: I browser web non supportano nativamente il protocollo AMQP usato da RabbitMQ. Anche se RabbitMQ dispone di plugin per WebStomp o MQTT su WebSocket, esporre il demone al pubblico resta una cattiva idea.
Soddisfa i requisiti: La User Story #3 ("I want the dashboard to update automatically without refreshing the page") richiede semplicemente che l'interfaccia si aggiorni da sola. Il meccanismo di polling (effettuare richieste fetch automatiche ogni 5 secondi in background) soddisfa pienamente questo requisito in modo semplice e stateless.
Coerenza con il progetto: Se noti, per gli eventi urgenti (come i trigger delle regole), il progetto usa già il notification-service che invia aggiornamenti al frontend tramite Server-Sent Events (SSE). Questo è l'approccio corretto: usare SSE/Websockets per le priorità alte (notifiche) e il polling per lo stato generale dei sensori, in modo da non sovraccaricare il server mantenendo troppe connessioni persistenti aperte per i grafici.
Quindi puoi spuntare quella voce nei TODO o rimuoverla completamente: l'approccio a polling ogni 5 secondi per la dashboard è corretto e non richiede modifiche.

---

## 5. Actuator-control-service
- [x] L'actuator-control-service non prende gli eventi dall ingestion.

In realtà, da un punto di vista dell'architettura a microservizi (e in ambito IoT in generale), **è assolutamente corretto che l'`actuator-control-service` comunichi direttamente con il simulatore** senza passare per l'`ingestion`. Anzi, è una best practice del design.

Ti spiego perché l'architettura attuale è valida e coerente con i principi di un sistema distribuito:

1. **Separation of Concerns (Single Responsibility)**: In un'architettura IoT, il caricamento dati (Data Ingestion) e il controllo dei dispositivi (Command & Control) sono due flussi concettualmente diversi.
   - L'***Ingestion Service*** si occupa esclusivamente di "ascoltare" il mondo esterno: preleva i dati grezzi dei sensori, li normalizza in un formato standard e li inietta nel sistema (versandoli in RabbitMQ).
   - L'***Actuator Control Service*** fa il percorso inverso: raccoglie comandi generati dall'interno del sistema (es. dall'`automation-engine` tramite RabbitMQ o da richieste REST manuali) e li trasforma in chiamate HTTP verso il dispositivo "fisico" (in questo caso il simulatore). 
   Far fare all'Ingestion Service anche le chiamate in uscita verso gli attuatori violerebbe il principio di singola responsabilità, trasformandolo in un monolite che fa da "collo di bottiglia" verso l'esterno.

2. **Isolamento dei guasti (Fault Tolerance)**: Immagina che l'`ingestion` vada in crash (magari per via di un carico anomalo sui WebSockets di telemetria, o per un blocco della rete sui sensori). Grazie a questa separazione netta, l'`actuator-control-service` **rimane in piedi**. Questo è un requisito salvavita per un habitat spaziale: anche se la dashboard dovesse smettere di plottare i grafici perché l'ingestor è giù, tu potresti comunque usare il frontend per inviare manualmente comandi di emergenza agli attuatori (es. accendere le ventole), perché quel comando passa dall'API al broker e dritto all'actuator-control, bypassando completamente l'ingestion rotto.

3. **Rispetto delle indicazioni**: Se leggi la primissima riga della descrizione del componente *Ingestion* generata sulle specifiche di partenza, dice chiaramente: *"Polls REST sensors, subscribes to SSE telemetry streams..."*. Non cita mai le scritture. Al contrario, la definizione nativa dell'*actuator-control-service* lo descrive proprio come colui che effettua chiamate API verso il simulatore IoT per cambiare gli stati.

Quindi ti direi che non è un errore e non va contro le indicazioni, anzi dimostra che il progetto è stato strutturato su logiche di decoupling (disaccoppiamento) estremamente valide per sistemi *mission-critical*. Puoi tranquillamente mantenere questa struttura per l'esame/progetto!

---

## 6. Messages destination

Tutti i microservizi ricevono tutti i messaggi perche i topic hanno tutti lo stesso nome. (EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "mars_events"))

---

## 7. Slides
- [x] Tradurre slides.
- [ ] Completare le slide della presentazione.

---

## 8. Tecnologie utilizzate
- [ ] Documentare **tutte le tecnologie utilizzate** nel progetto.
- [ ] Specificare anche **le versioni** per il report finale.

---

## 9. README.md
- [ ] Aggiornare il `README.md`.
- [ ] Valutare l'inserimento nella cartella `booklets` di **file Markdown aggiuntivi** se ritenuti necessari.






## Risposta al dubbio:
L'architettura attuale è assolutamente corretta e conforme a quanto richiesto nel PDF, e non devi far passare le scritture per il message broker né creare un altro Ingestor.

Leggendo il file Laboratory_of_Advanced_Programming_March_2026.pdf, ci sono due passaggi fondamentali che confermano in modo inequivocabile le scelte architetturali dell'attuale codice sorgente:

1. Come comandare gli attuatori? (Sezione 3.4)
A pagina 3, sezione 3.4 (Actuator APIs), il testo dice chiaramente:

To change a state, POST a JSON payload to the actuator resource, for example: curl -X POST http://localhost:8080/api/actuators/cooling_fan \ -H 'Content-Type: application/json' \ -d '{"state":"ON"}' [...] Actuators are controlled exclusively via REST.

Questo significa che il simulatore non accetta comandi MQTT, AMQP o altri eventi di coda. Per accendere o spegnere un attuatore devi fargli per forza una chiamata HTTP POST. Pertanto, l'actuator-control-service deve chiamare le API REST del simulatore, esattamente come sta già facendo ora, ed è il modo in cui ci si aspetta che funzioni.

2. Ruolo del Message Broker interno (Sezione 4)
A pagina 4, nelle Deliverables (Sezione 4. point 3), il testo dice:

3. Uses an event-driven architecture internally (message broker required)

Il message broker (RabbitMQ) serve per la comunicazione interna fra i tuoi microservizi (ad esempio: per inviare l'evento normalizzato dall'Ingestor al Data History e all'Automation Engine, e poi dall'Automation Engine all'Actuator Control Service), non per comunicare verso l'esterno con i sensori o con gli attuatori del simulatore fornito.

Conclusione
L'Ingestor funge, nel pattern dell'architettura IoT, da Gateway d'ingresso (Source): fa da "traduttore" raccogliendo protocolli disparati (polling HTTP da una parte e websocket/SSE dall'altra) e uniformandoli nel formato standard per iniettarli in RabbitMQ. L'Actuator Control Service è il Gateway di uscita (Sink): riceve i messaggi interni dalla coda di RabbitMQ (lanciati dall'Automation Engine) e li traduce nella chiamata HTTP POST obbligatoria che si aspetta il simulatore.

Questo è il modo da manuale di isolare il "mondo esterno" (il simulatore di Marte) dal "mondo interno" (la tua logica di business e le tue code). La tua architettura attuale dimostra che hai compreso appieno non solo le specifiche fornite dal professore, ma anche i concetti architetturali che stanno alla base dei sistemi cyber-fisici moderni. Mantenetela esattamente così com'è!