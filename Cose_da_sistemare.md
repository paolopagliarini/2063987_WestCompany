## TODO

1. **input.md**
   - Valutare cosa mantenere della sezione successiva alla definizione dello **event schema**.

2. **Student_doc.md**
   - Popolare correttamente il file con tutte le informazioni richieste dal progetto.

3. **Aggiornamento stato attuatori**
   - Quando viene aggiunta una nuova regola, il sistema **non aggiorna lo stato degli attuatori automaticamente**.
   - Gli attuatori vengono accesi o spenti **solo manualmente**.
   - Verificare se il problema dipende da:
     - il **frontend** (polling),
     - oppure dall'**automation-engine**.

4. **Polling del frontend**
   - Attualmente il frontend effettua **polling sui microservizi ogni 5 secondi**.
   - Verificare se dovrebbe invece **consumare direttamente gli eventi dal message broker**.

5. **Slides**
   - Completare le slide della presentazione.

6. **Tecnologie utilizzate**
   - Documentare **tutte le tecnologie utilizzate** nel progetto.
   - Specificare anche **le versioni**, utili per il report finale.

7. **README.md**
   - Aggiornare il `README.md`.
   - Valutare l'inserimento nella cartella `booklets` di **file Markdown aggiuntivi** se ritenuti necessari.