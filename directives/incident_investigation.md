# Investigazione Incidenti con ICE

## Obiettivo
Guidare l'LLM nell'analisi di un incidente applicativo usando i tool MCP di ICE.

## Flusso di investigazione

### Step 1: Identificazione del servizio
- L'utente indica il nome del servizio problematico (es. "backend", "auth-service")
- Se non specificato, chiedere all'utente quale servizio investigare

### Step 2: Raccolta contesto rapida
- Usare il tool `get_incident_context` per raccogliere tutto il contesto in un'unica chiamata
- Questo tool aggrega: pod status, deployment info, build recenti, commit recenti

### Step 3: Analisi dettagliata (se necessario)
Se il contesto rapido non è sufficiente:

1. **Pod in crash/restart?**
   - Usare `get_pod_status` con il nome del servizio
   - Se ci sono restart, controllare i log con `get_pod_logs`
   - Cercare: OOMKilled, NullPointerException, ConnectionRefused, Timeout

2. **Problema di deployment?**
   - Usare `get_deployment_info` per verificare immagine e repliche
   - Confrontare l'immagine con la build più recente

3. **Build fallita?**
   - Usare `get_build_info` per controllare lo stato delle ultime build
   - Se una build è fallita, controllare il commit associato

4. **Commit sospetto?**
   - Usare `get_recent_commits` per vedere le ultime modifiche
   - Correlare il commit con la build e il deployment

### Step 4: Correlazione
Collegare le informazioni raccolte:
- **Pod crashloop** → Log mostrano eccezione → Commit X ha introdotto il bug → Build Y ha deployato il commit
- **OOMKilled** → Resource usage elevato → Immagine diversa dalla precedente → Build recente ha cambiato configurazione
- **Readiness probe failure** → Servizio dipendente non raggiungibile → Controllare altri pod nel namespace

### Step 5: Report
Presentare all'utente:
- Il problema identificato
- La causa probabile
- Il commit/build responsabile
- Suggerimenti per la risoluzione

## Casi limite
- **oc non raggiungibile**: il token potrebbe essere scaduto, suggerire `oc login` manuale
- **Azure DevOps non raggiungibile**: verificare che il PAT sia valido e non scaduto
- **Servizio non trovato**: verificare il namespace e il nome del servizio con l'utente
- **Pod senza label 'app'**: usare `get_pod_status` senza il parametro `service` per listare tutti i pod

## Tool disponibili

| Tool | Sorgente | Uso |
|------|----------|-----|
| `get_pod_status` | OpenShift | Stato pod (crash, restart, OOM) |
| `get_pod_logs` | OpenShift | Log recenti di un pod |
| `get_deployment_info` | OpenShift | Info deployment (image, repliche) |
| `get_build_info` | Azure DevOps | Dettagli build CI/CD |
| `get_pipeline_runs` | Azure DevOps | Esecuzioni pipeline recenti |
| `get_recent_commits` | Azure DevOps | Ultimi commit su un repo |
| `get_repositories` | Azure DevOps | Lista dei repository Git nel progetto |
| `get_incident_context` | Tutti | Contesto aggregato (tool composito) |
