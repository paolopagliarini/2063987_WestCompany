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