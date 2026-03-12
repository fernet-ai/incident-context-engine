"""
azure_devops_client.py - Client REST per le API Azure DevOps.

Usa la libreria 'requests' con autenticazione Basic Auth (PAT come password).
Permette di recuperare build, pipeline, commit e artifact da Azure DevOps.
"""

import requests
import json
import sys
from pathlib import Path
from base64 import b64encode

# Aggiunge la directory backend/ al path per importare config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from config import settings


# Versione API Azure DevOps da usare nelle richieste
API_VERSION = "7.1"


def _get_auth_header() -> dict:
    """
    Genera l'header di autenticazione Basic Auth per Azure DevOps.
    Il PAT viene usato come password con username vuoto.
    
    Returns:
        dict con l'header Authorization
    """
    # Azure DevOps usa Basic Auth con username vuoto e PAT come password
    credentials = b64encode(f":{settings.AZURE_DEVOPS_PAT}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }


def _make_request(url: str, params: dict = None) -> dict:
    """
    Effettua una richiesta GET alle API Azure DevOps.
    
    Args:
        url: URL completo dell'endpoint API
        params: parametri query opzionali
    
    Returns:
        dict con chiavi 'success', 'output' (dati JSON), 'error' (stringa)
    """
    if not settings.AZURE_DEVOPS_ORG_URL or not settings.AZURE_DEVOPS_PAT:
        return {
            "success": False,
            "output": "",
            "error": "AZURE_DEVOPS_ORG_URL o AZURE_DEVOPS_PAT non configurati nel .env"
        }

    try:
        # Aggiunge la versione API come parametro di default
        if params is None:
            params = {}
        params["api-version"] = API_VERSION

        response = requests.get(url, headers=_get_auth_header(), params=params, timeout=30)

        if response.status_code == 200:
            return {"success": True, "output": response.json(), "error": ""}
        elif response.status_code == 401:
            return {"success": False, "output": "", "error": "Autenticazione fallita: verifica il PAT in .env"}
        elif response.status_code == 404:
            return {"success": False, "output": "", "error": f"Risorsa non trovata: {url}"}
        else:
            return {"success": False, "output": "", "error": f"Errore HTTP {response.status_code}: {response.text[:500]}"}

    except requests.exceptions.ConnectionError:
        return {"success": False, "output": "", "error": f"Impossibile connettersi a {settings.AZURE_DEVOPS_ORG_URL}"}
    except requests.exceptions.Timeout:
        return {"success": False, "output": "", "error": "Timeout: la richiesta ha superato i 30 secondi"}
    except Exception as e:
        return {"success": False, "output": "", "error": f"Errore imprevisto: {str(e)}"}


def get_builds(project: str = "", definition_name: str = "", top: int = 5) -> dict:
    """
    Recupera le ultime N build da Azure DevOps.
    
    API: GET {org}/{project}/_apis/build/builds
    
    Args:
        project: nome del progetto (usa il default da .env se vuoto)
        definition_name: filtro opzionale per nome della definition
        top: numero massimo di build da recuperare (default 5)
    
    Returns:
        dict con lista delle build (id, status, result, source branch, commit)
    """
    proj = project or settings.AZURE_DEVOPS_PROJECT
    url = f"{settings.AZURE_DEVOPS_ORG_URL}/{proj}/_apis/build/builds"

    params = {"$top": top}
    if definition_name:
        params["definitionName"] = definition_name  # Filtra per nome pipeline (opzionale, non sempre supportato)

    result = _make_request(url, params)

    if not result["success"]:
        return result

    # Estrae le informazioni principali da ogni build
    builds = []
    for build in result["output"].get("value", []):
        build_info = {
            "id": build.get("id"),
            "build_number": build.get("buildNumber"),
            "status": build.get("status"),
            "result": build.get("result"),
            "source_branch": build.get("sourceBranch"),
            "source_version": build.get("sourceVersion", "")[:8],  # Primi 8 char del commit
            "start_time": build.get("startTime"),
            "finish_time": build.get("finishTime"),
            "definition_name": build.get("definition", {}).get("name"),
            "requested_by": build.get("requestedBy", {}).get("displayName")
        }
        builds.append(build_info)

    return {"success": True, "output": builds, "error": ""}


def get_build_details(project: str = "", build_id: int = 0) -> dict:
    """
    Recupera i dettagli di una build specifica.
    
    API: GET {org}/{project}/_apis/build/builds/{buildId}
    
    Args:
        project: nome del progetto
        build_id: ID numerico della build
    
    Returns:
        dict con dettagli completi della build
    """
    proj = project or settings.AZURE_DEVOPS_PROJECT
    url = f"{settings.AZURE_DEVOPS_ORG_URL}/{proj}/_apis/build/builds/{build_id}"

    result = _make_request(url)

    if not result["success"]:
        return result

    # Estrae i dettagli significativi dalla build
    build = result["output"]
    details = {
        "id": build.get("id"),
        "build_number": build.get("buildNumber"),
        "status": build.get("status"),
        "result": build.get("result"),
        "source_branch": build.get("sourceBranch"),
        "source_version": build.get("sourceVersion"),
        "start_time": build.get("startTime"),
        "finish_time": build.get("finishTime"),
        "definition_name": build.get("definition", {}).get("name"),
        "requested_by": build.get("requestedBy", {}).get("displayName"),
        "repository": build.get("repository", {}).get("name"),
        "logs_url": build.get("logs", {}).get("url"),
        "reason": build.get("reason"),
        "priority": build.get("priority")
    }

    return {"success": True, "output": details, "error": ""}


def get_pipeline_runs(project: str = "", pipeline_name: str = "", top: int = 5) -> dict:
    """
    Recupera le ultime esecuzioni di pipeline.
    Usa l'API builds filtrata per definition name come proxy per le pipeline runs.
    
    Args:
        project: nome del progetto
        pipeline_name: nome della pipeline da filtrare
        top: numero massimo di risultati (default 5)
    
    Returns:
        dict con lista delle esecuzioni pipeline
    """
    # Le pipeline runs in Azure DevOps sono essenzialmente build filtrate per definition
    return get_builds(project=project, definition_name=pipeline_name, top=top)


def get_commits(project: str = "", repository: str = "", top: int = 10) -> dict:
    """
    Recupera gli ultimi N commit da un repository Git in Azure DevOps.
    
    API: GET {org}/{project}/_apis/git/repositories/{repo}/commits
    
    Args:
        project: nome del progetto
        repository: nome del repository Git
        top: numero massimo di commit da recuperare (default 10)
    
    Returns:
        dict con lista dei commit (id, autore, messaggio, data)
    """
    proj = project or settings.AZURE_DEVOPS_PROJECT
    url = f"{settings.AZURE_DEVOPS_ORG_URL}/{proj}/_apis/git/repositories/{repository}/commits"

    params = {"$top": top}
    result = _make_request(url, params)

    if not result["success"]:
        return result

    # Estrae le informazioni chiave da ogni commit
    commits = []
    for commit in result["output"].get("value", []):
        commit_info = {
            "commit_id": commit.get("commitId", "")[:8],  # Primi 8 char dello SHA
            "commit_id_full": commit.get("commitId"),
            "author": commit.get("author", {}).get("name"),
            "author_email": commit.get("author", {}).get("email"),
            "date": commit.get("author", {}).get("date"),
            "message": commit.get("comment", "").strip(),
            "url": commit.get("remoteUrl")
        }
        commits.append(commit_info)

    return {"success": True, "output": commits, "error": ""}


def get_commit_details(project: str = "", repository: str = "", commit_id: str = "") -> dict:
    """
    Recupera i dettagli di un singolo commit.
    
    API: GET {org}/{project}/_apis/git/repositories/{repo}/commits/{commitId}
    
    Args:
        project: nome del progetto
        repository: nome del repository
        commit_id: SHA del commit (completo o abbreviato)
    
    Returns:
        dict con dettagli del commit (autore, messaggio, file modificati)
    """
    proj = project or settings.AZURE_DEVOPS_PROJECT
    url = f"{settings.AZURE_DEVOPS_ORG_URL}/{proj}/_apis/git/repositories/{repository}/commits/{commit_id}"

    result = _make_request(url)

    if not result["success"]:
        return result

    commit = result["output"]
    details = {
        "commit_id": commit.get("commitId"),
        "author": commit.get("author", {}).get("name"),
        "author_email": commit.get("author", {}).get("email"),
        "date": commit.get("author", {}).get("date"),
        "committer": commit.get("committer", {}).get("name"),
        "message": commit.get("comment", "").strip(),
        "changes_count": commit.get("changeCounts", {}),
        "url": commit.get("remoteUrl")
    }

    return {"success": True, "output": details, "error": ""}


# === Entry point per test standalone ===
if __name__ == "__main__":
    print("=== Test Azure DevOps Client ===")
    
    print(f"\nOrganizzazione: {settings.AZURE_DEVOPS_ORG_URL}")
    print(f"Progetto: {settings.AZURE_DEVOPS_PROJECT}")
    
    # Test get builds
    print("\n1. Recupero ultime build...")
    builds_result = get_builds()
    print(f"   Risultato: {json.dumps(builds_result, indent=2, default=str)}")
