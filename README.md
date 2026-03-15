

# Incident Context Engine (ICE)

## 1. Introduzione

Nelle moderne architetture cloud-native basate su **Kubernetes/OpenShift**, **CI/CD** e **microservizi**, l’analisi degli incidenti applicativi richiede spesso la consultazione manuale di molteplici sistemi:

- log applicativi
    
- stato dei pod Kubernetes
    
- deployment e container image
    
- pipeline CI/CD
    
- commit Git
    
- build artifacts
    

Queste informazioni sono distribuite tra diversi strumenti come:

- OpenShift / Kubernetes
    
- Azure DevOps
    
- Git repositories
    
- CI/CD pipelines
    

Il risultato è che il troubleshooting richiede spesso **navigazione manuale tra sistemi diversi**, aumentando il tempo necessario per identificare la causa di un problema.

---

# 2. Visione del progetto

L'**Incident Context Engine (ICE)** è un sistema progettato per **fornire contesto runtime e DevOps a un Large Language Model (LLM)** tramite un **MCP Server**.

In pratica:

**ICE espone API interrogabili da GitHub Copilot che permettono all'LLM di recuperare automaticamente informazioni da:**

- OpenShift / Kubernetes
    
- Azure DevOps
    
- CI/CD pipelines
    
- repository Git
    

Questo permette a Copilot di **analizzare incidenti reali con contesto live del sistema**.

---

# 3. Obiettivo

L’obiettivo del progetto è permettere a **GitHub Copilot o altri LLM** di rispondere a domande operative come:

- “Perché questo servizio sta crashando?”
    
- “Quale commit ha introdotto questo errore?”
    
- “Quale pipeline ha deployato questa versione?”
    
- “Chi ha fatto l’ultima modifica al servizio?”
    

senza che l’utente debba manualmente interrogare:

- `oc`
    
- Azure DevOps
    
- Git
    
- pipeline CI/CD
    

Il modello LLM può invece interrogare direttamente il **MCP server ICE**, che fornisce il contesto necessario.

---

# 4. Ruolo dell’MCP Server

Il **Model Context Protocol (MCP)** consente agli LLM di interrogare sistemi esterni tramite tool strutturati.

Nel progetto ICE, il **MCP server funge da ponte tra Copilot e l’infrastruttura DevOps**.

Architettura:

```
Developer
    ↓
GitHub Copilot (LLM)
    ↓
MCP Client (IntelliJ / VSCode)
    ↓
Incident Context Engine (MCP Server)
    ↓
-------------------------------------
OpenShift CLI (oc)
Azure DevOps APIs
Kubernetes APIs
Git APIs
```

Il server MCP espone endpoint che permettono all’LLM di interrogare il sistema runtime.

---

# 5. Tipologia di informazioni fornite all'LLM

Il server ICE aggrega dati provenienti da diversi sistemi.

### Runtime (OpenShift / Kubernetes)

- pod status
    
- restart count
    
- container crash
    
- OOMKilled
    
- readiness probe failure
    
- pod logs
    
- resource usage (CPU / memory)
    

### Deployment Context

- deployment name
    
- container image
    
- image tag
    
- numero di repliche
    

### CI/CD Context (Azure DevOps)

- build pipeline
    
- build status
    
- artifact generati
    
- commit associato alla build
    

### Git Context

- commit ID
    
- autore
    
- messaggio
    
- timestamp
    

---

# 6. Esempio di interrogazione LLM

Uno sviluppatore può chiedere a Copilot:

> "Perché il servizio `backend` sta crashando in produzione?"

Copilot può automaticamente interrogare il server MCP:

```
getOpenShiftIncidentContext(service="backend")
```

Il server ICE esegue:

```
oc get pods
oc logs
oc describe pod
```

E interroga Azure DevOps per correlare:

- build
    
- pipeline
    
- commit
    

---

# 7. Output restituito al LLM

Il server MCP restituisce un JSON strutturato:

```json
{
  "service": "backend",
  "error": "NullPointerException",
  "pod": "backend-5f98d",
  "deployment": "backend",
  "image": "backend:20250306.1",
  "build": 8452,
  "pipeline": "backend-ci",
  "commit": "abc123",
  "author": "Mario Rossi",
  "message": "fix login bug"
}
```

Copilot può quindi interpretare il contesto e spiegare all’utente:

> "Il crash è probabilmente causato dal commit `abc123` introdotto nella build 8452."

---

# 8. Vantaggio principale

Il valore del sistema non è solo raccogliere dati, ma **renderli immediatamente utilizzabili da un LLM**.

Questo abilita un nuovo paradigma:

### AI-assisted incident investigation

Dove un LLM può:

- investigare incidenti
    
- correlare dati runtime e CI/CD
    
- suggerire cause probabili
    
- indicare commit responsabili
    

---

# 9. Benefici

### Riduzione del MTTR

Diagnosi incidenti molto più veloce.

### Contesto runtime per Copilot

Copilot non lavora più solo sul codice, ma anche sul **runtime reale del sistema**.

### Automazione troubleshooting

L’LLM può eseguire automaticamente le interrogazioni tecniche.

### Migliore collaborazione tra team

SRE, DevOps e sviluppatori condividono lo stesso contesto.

---

# 10. Evoluzioni future

Il progetto può essere esteso con:

- integrazione Dynatrace
    
- analisi automatica delle regressioni
    
- correlazione incidenti multi-servizio
    
- alert intelligenti
    

---

# 11. Setup e Configurazione

Per utilizzare ICE come MCP Server, segui questi passaggi:

### 1. Configurazione delle Credenziali
Copia il file `.env` ed inserisci i tuoi token e URL:

```env
# OpenShift
OPENSHIFT_API_URL=https://api.cluster.example.com:6443
OPENSHIFT_TOKEN=tuo-token-qui        # Ottienilo con: oc whoami -t
OPENSHIFT_NAMESPACE=tuo-namespace

# Azure DevOps
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/tua-org
AZURE_DEVOPS_PAT=tuo-pat-qui         # Personal Access Token con permessi Build/Code
AZURE_DEVOPS_PROJECT=tuo-progetto
```

### 2. Installazione Dipendenze
Assicurati di avere Python 3.10+ installato, quindi esegui:

```bash
pip install -r backend/requirements.txt
```

### 3. Integrazione con GitHub Copilot
Per integrare ICE in VS Code con GitHub Copilot, crea (o modifica) il file di configurazione MCP di VS Code:

- **Windows**: `%APPDATA%\Code\User\globalStorage\github.copilot-chat\mcp.json`
- **macOS/Linux**: `~/Library/Application Support/Code/User/globalStorage/github.copilot-chat\mcp.json`

Aggiungi la configurazione per ICE:

```json
{
  "mcpServers": {
    "incident-context-engine": {
      "command": "python",
      "args": ["c:/percorso/assoluto/a/incident-context-engine/backend/main.py"],
      "env": {
        "PYTHONPATH": "c:/percorso/assoluto/a/incident-context-engine/backend;c:/percorso/assoluto/a/incident-context-engine/execution"
      }
    }
  }
}
```

### 4. Avvio del Server
Il server viene avviato automaticamente da Copilot tramite il comando configurato sopra. Per testarlo manualmente:

```bash
python backend/main.py
```

---

# 12. Tool Disponibili

Attualmente ICE espone i seguenti tool all'LLM:

| Categoria | Tool | Descrizione |
|-----------|------|-------------|
| **OpenShift** | `get_pod_status` | Stato dei pod (crash, restart, oom) |
| **OpenShift** | `get_pod_logs` | Recupera gli ultimi N log di un pod |
| **OpenShift** | `get_deployment_info` | Info su immagine e repliche |
| **Azure DevOps** | `get_build_info` | Dettagli di build specifiche o recenti |
| **Azure DevOps** | `get_pipeline_runs` | Ultime esecuzioni di una pipeline |
| **Azure DevOps** | `get_recent_commits` | Ultimi commit su un repository Git |
| **Composito** | `get_incident_context` | **Aggregatore**: combina runtime e CI/CD in un unico report |

---

# 13. Testing con MCP Inspector

Se non hai mai usato un server MCP o vuoi testare i tool senza usare Copilot, il metodo più semplice è usare l'**MCP Inspector**.

### A cosa serve?
L'Inspector apre un'interfaccia web interattiva che ti permette di:
- Vedere l'elenco dei tool registrati dal server.
- Inserire manualmente i parametri di input (es. il nome di un servizio).
- Eseguire il tool e vedere l'output JSON reale restituito dai client (OpenShift/Azure DevOps).
- Verificare se le tue credenziali nel `.env` sono corrette.

### Come usarlo
Dalla cartella root del progetto, esegui:

```bash
npx @modelcontextprotocol/inspector python backend/main.py
```

1. Il comando avvierà l'ispettore e ti fornirà un link (es. `http://localhost:6274/...`).
2. Apri il link nel browser.
3. Seleziona un tool dalla lista (es. `get_pod_status`).
4. Inserisci un parametro (es: `service: "backend"`) e clicca su **"Run Tool"**.
5. Vedrai la risposta del sistema in tempo reale.

È il modo migliore per assicurarsi che tutto sia configurato correttamente prima di passare all'integrazione finale in VS Code.
