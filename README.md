

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
