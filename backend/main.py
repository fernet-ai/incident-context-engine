"""
main.py - Entry point del server MCP per l'Incident Context Engine (ICE).

Questo server espone tool interrogabili da GitHub Copilot (o altri LLM)
per recuperare contesto runtime (OpenShift) e CI/CD (Azure DevOps)
durante l'analisi di incidenti applicativi.

Usa FastMCP (incluso nell'SDK MCP ufficiale) per registrare i tool
e gestire il protocollo di comunicazione con il client MCP.
"""

import sys
import json
from pathlib import Path

# Aggiunge le directory necessarie al path per importare i moduli
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "backend"))
sys.path.insert(0, str(_project_root / "execution"))

from mcp.server.fastmcp import FastMCP
from config import settings
import openshift_client as oc
import azure_devops_client as azdo


# ============================================================
# Inizializzazione del server MCP
# ============================================================
mcp = FastMCP(
    name="incident-context-engine",
    instructions="""
    Sei l'Incident Context Engine (ICE), un sistema che fornisce contesto
    runtime e DevOps a un LLM per analizzare incidenti applicativi.
    
    Puoi interrogare OpenShift/Kubernetes per informazioni sui pod,
    deployment e log, e Azure DevOps per build, pipeline e commit.
    
    Usa i tool disponibili per raccogliere contesto e correlare
    le informazioni tra runtime e CI/CD.
    """
)


# ============================================================
# Tool OpenShift / Kubernetes
# ============================================================

@mcp.tool()
def get_pod_status(service: str = "", namespace: str = "") -> str:
    """
    Recupera lo stato dei pod per un servizio su OpenShift/Kubernetes.
    Mostra: nome, stato, numero di restart, se è ready, se è stato OOMKilled.
    
    Args:
        service: nome del servizio (usato come label selector 'app=<service>').
                 Se vuoto, recupera tutti i pod nel namespace.
        namespace: namespace OpenShift. Se vuoto, usa il default da .env.
    
    Returns:
        JSON con la lista dei pod e il loro stato.
    """
    # Prima effettua il login al cluster
    login_result = oc.login()
    if not login_result["success"]:
        return json.dumps({"error": f"Login OpenShift fallito: {login_result['error']}"})

    # Costruisce il label selector se è stato specificato un servizio
    label_selector = f"app={service}" if service else ""

    # Recupera i pod
    result = oc.get_pods(namespace=namespace, label_selector=label_selector)

    if not result["success"]:
        return json.dumps({"error": result["error"]})

    return json.dumps({"pods": result["output"]}, indent=2, default=str)


@mcp.tool()
def get_pod_logs(pod_name: str, namespace: str = "", tail_lines: int = 100, container: str = "") -> str:
    """
    Recupera gli ultimi log di un pod specifico su OpenShift.
    Utile per identificare errori, eccezioni e crash.
    
    Args:
        pod_name: nome esatto del pod (es. 'backend-5f98d-xyz').
        namespace: namespace OpenShift. Se vuoto, usa il default da .env.
        tail_lines: numero di righe di log da recuperare (default 100).
        container: nome del container specifico (per pod multi-container).
    
    Returns:
        Le ultime righe di log del pod.
    """
    # Login al cluster
    login_result = oc.login()
    if not login_result["success"]:
        return json.dumps({"error": f"Login OpenShift fallito: {login_result['error']}"})

    # Recupera i log
    result = oc.get_pod_logs(
        namespace=namespace,
        pod_name=pod_name,
        tail_lines=tail_lines,
        container=container
    )

    if not result["success"]:
        return json.dumps({"error": result["error"]})

    return result["output"]


@mcp.tool()
def get_deployment_info(deployment_name: str, namespace: str = "") -> str:
    """
    Recupera le informazioni di un deployment su OpenShift.
    Mostra: nome, repliche disponibili, immagine container, strategia di deploy.
    
    Args:
        deployment_name: nome del deployment (es. 'backend').
        namespace: namespace OpenShift. Se vuoto, usa il default da .env.
    
    Returns:
        JSON con le informazioni del deployment.
    """
    # Login al cluster
    login_result = oc.login()
    if not login_result["success"]:
        return json.dumps({"error": f"Login OpenShift fallito: {login_result['error']}"})

    # Recupera info deployment
    result = oc.get_deployment(namespace=namespace, deployment_name=deployment_name)

    if not result["success"]:
        return json.dumps({"error": result["error"]})

    return json.dumps({"deployment": result["output"]}, indent=2, default=str)


# ============================================================
# Tool Azure DevOps
# ============================================================

@mcp.tool()
def get_build_info(build_id: int = 0, project: str = "") -> str:
    """
    Recupera informazioni su una build specifica da Azure DevOps.
    Se build_id è 0, recupera le ultime 5 build.
    
    Args:
        build_id: ID numerico della build. Se 0, recupera le ultime build.
        project: nome del progetto Azure DevOps. Se vuoto, usa il default da .env.
    
    Returns:
        JSON con dettagli della build (status, result, commit, pipeline, autore).
    """
    if build_id > 0:
        # Recupera i dettagli di una build specifica
        result = azdo.get_build_details(project=project, build_id=build_id)
    else:
        # Recupera le ultime build
        result = azdo.get_builds(project=project, top=5)

    if not result["success"]:
        return json.dumps({"error": result["error"]})

    return json.dumps({"builds": result["output"]}, indent=2, default=str)


@mcp.tool()
def get_pipeline_runs(pipeline_name: str = "", project: str = "", top: int = 5) -> str:
    """
    Recupera le ultime esecuzioni di una pipeline CI/CD da Azure DevOps.
    
    Args:
        pipeline_name: nome della pipeline da filtrare. Se vuoto, mostra tutte.
        project: nome del progetto Azure DevOps. Se vuoto, usa il default da .env.
        top: numero massimo di risultati (default 5).
    
    Returns:
        JSON con le ultime esecuzioni della pipeline.
    """
    result = azdo.get_pipeline_runs(project=project, pipeline_name=pipeline_name, top=top)

    if not result["success"]:
        return json.dumps({"error": result["error"]})

    return json.dumps({"pipeline_runs": result["output"]}, indent=2, default=str)


@mcp.tool()
def get_recent_commits(repository: str, project: str = "", top: int = 10) -> str:
    """
    Recupera gli ultimi commit da un repository Git in Azure DevOps.
    
    Args:
        repository: nome del repository Git.
        project: nome del progetto Azure DevOps. Se vuoto, usa il default da .env.
        top: numero di commit da recuperare (default 10).
    
    Returns:
        JSON con lista dei commit (id, autore, messaggio, data).
    """
    result = azdo.get_commits(project=project, repository=repository, top=top)

    if not result["success"]:
        return json.dumps({"error": result["error"]})

    return json.dumps({"commits": result["output"]}, indent=2, default=str)


@mcp.tool()
def get_repositories(project: str = "") -> str:
    """
    Recupera la lista dei repository Git disponibili in un progetto Azure DevOps.
    Utile per scoprire i nomi esatti dei repository prima di cercare commit.

    Args:
        project: nome del progetto Azure DevOps. Se vuoto, usa il default da .env.

    Returns:
        JSON con la lista dei repository (nome, default branch, URL, dimensione).
    """
    result = azdo.get_repositories(project=project)

    if not result["success"]:
        return json.dumps({"error": result["error"]})

    return json.dumps({"repositories": result["output"]}, indent=2, default=str)

# ============================================================
# Tool Composito (aggregazione multi-sorgente)
# ============================================================

@mcp.tool()
def get_incident_context(service: str, repository: str = "", namespace: str = "", project: str = "") -> str:
    """
    Tool composito: aggrega contesto runtime (OpenShift) e CI/CD (Azure DevOps)
    per un servizio specifico. Questo è il tool principale per l'investigazione
    di incidenti.
    
    Raccoglie:
    - Stato dei pod del servizio (crash, restart, OOMKilled)
    - Info deployment (immagine, repliche)
    - Ultime build della pipeline CI/CD
    - Ultimi commit sul repository
    
    Args:
        service: nome del servizio da investigare (es. 'backend').
        repository: nome del repository Git associato (se vuoto, usa il nome del servizio).
        namespace: namespace OpenShift. Se vuoto, usa il default da .env.
        project: progetto Azure DevOps. Se vuoto, usa il default da .env.
    
    Returns:
        JSON aggregato con tutto il contesto dell'incidente.
    """
    # Il repository di default ha lo stesso nome del servizio
    repo = repository or service
    context = {"service": service}

    # --- 1. Contesto Runtime (OpenShift) ---
    login_result = oc.login()
    if login_result["success"]:
        # Stato dei pod
        pods_result = oc.get_pods(namespace=namespace, label_selector=f"app={service}")
        if pods_result["success"]:
            context["pods"] = pods_result["output"]

            # Se ci sono pod, recupera i log del primo pod con problemi (o del primo in lista)
            if pods_result["output"]:
                # Cerca un pod con restart > 0 o OOMKilled, altrimenti prende il primo
                problem_pod = next(
                    (p for p in pods_result["output"] if p.get("restart_count", 0) > 0 or p.get("oom_killed")),
                    pods_result["output"][0]
                )
                logs_result = oc.get_pod_logs(namespace=namespace, pod_name=problem_pod["name"], tail_lines=50)
                if logs_result["success"]:
                    context["recent_logs"] = logs_result["output"]

        # Info deployment
        deploy_result = oc.get_deployment(namespace=namespace, deployment_name=service)
        if deploy_result["success"]:
            context["deployment"] = deploy_result["output"]
    else:
        context["openshift_error"] = login_result["error"]

    # --- 2. Contesto CI/CD (Azure DevOps) ---
    # Ultime build
    builds_result = azdo.get_builds(project=project, top=3)
    if builds_result["success"]:
        context["recent_builds"] = builds_result["output"]

    # Ultimi commit
    commits_result = azdo.get_commits(project=project, repository=repo, top=5)
    if commits_result["success"]:
        context["recent_commits"] = commits_result["output"]

    return json.dumps(context, indent=2, default=str)


# ============================================================
# Avvio del server
# ============================================================
if __name__ == "__main__":
    # Mostra eventuali warning sulla configurazione
    warnings = settings.validate()
    if warnings:
        sys.stderr.write("⚠️  Warning configurazione:\n")
        for w in warnings:
            sys.stderr.write(f"   - {w}\n")
        sys.stderr.write("\n")

    # Avvia il server MCP (usa il transport stdio per default)
    sys.stderr.write("🚀 Avvio Incident Context Engine (MCP Server)...\n")
    mcp.run()
