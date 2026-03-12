"""
openshift_client.py - Client wrapper per il CLI 'oc' (OpenShift).

Esegue comandi 'oc' tramite subprocess e parsa l'output JSON.
Il login avviene automaticamente con token e URL dal file .env.
"""

import subprocess
import json
import sys
from pathlib import Path

# Aggiunge la directory backend/ al path per importare config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from config import settings


def _run_oc_command(args: list[str], timeout: int = 30) -> dict:
    """
    Esegue un comando 'oc' e restituisce il risultato.
    
    Args:
        args: lista di argomenti da passare a 'oc' (es. ["get", "pods", "-o", "json"])
        timeout: timeout in secondi per l'esecuzione del comando
    
    Returns:
        dict con chiavi 'success', 'output' (str), 'error' (str)
    """
    try:
        # Esegue il comando oc con gli argomenti forniti
        result = subprocess.run(
            ["oc"] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            return {"success": True, "output": result.stdout.strip(), "error": ""}
        else:
            return {"success": False, "output": "", "error": result.stderr.strip()}

    except FileNotFoundError:
        # oc non è installato o non è nel PATH
        return {"success": False, "output": "", "error": "Comando 'oc' non trovato. Assicurati che sia installato e nel PATH."}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"Timeout: il comando ha superato i {timeout} secondi."}
    except Exception as e:
        return {"success": False, "output": "", "error": f"Errore imprevisto: {str(e)}"}


def login() -> dict:
    """
    Effettua il login al cluster OpenShift usando token e URL dal .env.
    
    Esegue: oc login --token=<TOKEN> --server=<URL> --insecure-skip-tls-verify=true
    
    Returns:
        dict con esito del login
    """
    if not settings.OPENSHIFT_TOKEN or not settings.OPENSHIFT_API_URL:
        return {"success": False, "output": "", "error": "OPENSHIFT_TOKEN o OPENSHIFT_API_URL non configurati nel .env"}

    return _run_oc_command([
        "login",
        f"--token={settings.OPENSHIFT_TOKEN}",
        f"--server={settings.OPENSHIFT_API_URL}",
        "--insecure-skip-tls-verify=true"  # Ignora verifica TLS (comune in ambienti interni)
    ])


def get_pods(namespace: str = "", label_selector: str = "") -> dict:
    """
    Recupera la lista dei pod e il loro stato.
    
    Esegue: oc get pods -n <namespace> [-l <label>] -o json
    
    Args:
        namespace: namespace OpenShift (usa il default da .env se vuoto)
        label_selector: filtro label opzionale (es. "app=backend")
    
    Returns:
        dict con lista dei pod e il loro stato (nome, stato, restart, ready)
    """
    ns = namespace or settings.OPENSHIFT_NAMESPACE
    args = ["get", "pods", "-n", ns, "-o", "json"]

    # Aggiunge il filtro label se specificato
    if label_selector:
        args.extend(["-l", label_selector])

    result = _run_oc_command(args)

    if not result["success"]:
        return result

    try:
        # Parsa l'output JSON e estrae le informazioni principali di ogni pod
        data = json.loads(result["output"])
        pods = []
        for item in data.get("items", []):
            pod_info = {
                "name": item["metadata"]["name"],
                "namespace": item["metadata"]["namespace"],
                "status": item["status"].get("phase", "Unknown"),
                "restart_count": sum(
                    cs.get("restartCount", 0) 
                    for cs in item["status"].get("containerStatuses", [])
                ),
                "ready": all(
                    cs.get("ready", False) 
                    for cs in item["status"].get("containerStatuses", [])
                ),
                # Controlla se qualche container è stato OOMKilled
                "oom_killed": any(
                    cs.get("lastState", {}).get("terminated", {}).get("reason") == "OOMKilled"
                    for cs in item["status"].get("containerStatuses", [])
                ),
                "containers": [
                    {
                        "name": cs["name"],
                        "ready": cs.get("ready", False),
                        "restart_count": cs.get("restartCount", 0),
                        "state": list(cs.get("state", {}).keys())[0] if cs.get("state") else "unknown"
                    }
                    for cs in item["status"].get("containerStatuses", [])
                ]
            }
            pods.append(pod_info)

        return {"success": True, "output": pods, "error": ""}

    except json.JSONDecodeError:
        return {"success": False, "output": "", "error": "Errore nel parsing JSON dell'output di 'oc get pods'"}


def get_pod_logs(namespace: str = "", pod_name: str = "", tail_lines: int = 100, container: str = "") -> dict:
    """
    Recupera gli ultimi N log di un pod specifico.
    
    Esegue: oc logs <pod> -n <namespace> --tail=<N> [-c <container>]
    
    Args:
        namespace: namespace OpenShift
        pod_name: nome del pod
        tail_lines: numero di righe da recuperare (default 100)
        container: nome del container specifico (opzionale, utile per pod multi-container)
    
    Returns:
        dict con i log del pod come stringa
    """
    ns = namespace or settings.OPENSHIFT_NAMESPACE
    args = ["logs", pod_name, "-n", ns, f"--tail={tail_lines}"]

    # Se specificato, recupera i log di un container specifico
    if container:
        args.extend(["-c", container])

    return _run_oc_command(args, timeout=60)


def describe_pod(namespace: str = "", pod_name: str = "") -> dict:
    """
    Recupera la descrizione completa di un pod (eventi, condizioni, volumi, ecc.).
    
    Esegue: oc describe pod <pod> -n <namespace>
    
    Args:
        namespace: namespace OpenShift
        pod_name: nome del pod
    
    Returns:
        dict con l'output testuale di 'oc describe pod'
    """
    ns = namespace or settings.OPENSHIFT_NAMESPACE
    return _run_oc_command(["describe", "pod", pod_name, "-n", ns], timeout=30)


def get_deployment(namespace: str = "", deployment_name: str = "") -> dict:
    """
    Recupera le informazioni di un deployment (immagine, repliche, strategia).
    
    Esegue: oc get deployment <name> -n <namespace> -o json
    
    Args:
        namespace: namespace OpenShift
        deployment_name: nome del deployment
    
    Returns:
        dict con info deployment (nome, repliche, immagini containers, strategia)
    """
    ns = namespace or settings.OPENSHIFT_NAMESPACE
    args = ["get", "deployment", deployment_name, "-n", ns, "-o", "json"]

    result = _run_oc_command(args)

    if not result["success"]:
        # Prova con DeploymentConfig (specifico OpenShift) se il Deployment non esiste
        args = ["get", "dc", deployment_name, "-n", ns, "-o", "json"]
        result = _run_oc_command(args)
        if not result["success"]:
            return result

    try:
        # Estrae le informazioni principali dal JSON del deployment
        data = json.loads(result["output"])
        deployment_info = {
            "name": data["metadata"]["name"],
            "namespace": data["metadata"]["namespace"],
            "replicas": data["spec"].get("replicas", 0),
            "available_replicas": data.get("status", {}).get("availableReplicas", 0),
            "strategy": data["spec"].get("strategy", {}).get("type", "Unknown"),
            "containers": [
                {
                    "name": c["name"],
                    "image": c["image"]
                }
                for c in data["spec"]["template"]["spec"]["containers"]
            ]
        }
        return {"success": True, "output": deployment_info, "error": ""}

    except (json.JSONDecodeError, KeyError) as e:
        return {"success": False, "output": "", "error": f"Errore nel parsing del deployment: {str(e)}"}


def get_resource_usage(namespace: str = "", pod_name: str = "") -> dict:
    """
    Recupera l'utilizzo di CPU e memoria di un pod.
    
    Esegue: oc adm top pod <pod> -n <namespace> --no-headers
    
    Args:
        namespace: namespace OpenShift
        pod_name: nome del pod (se vuoto, mostra tutti i pod nel namespace)
    
    Returns:
        dict con utilizzo risorse (CPU, memoria) per ogni container
    """
    ns = namespace or settings.OPENSHIFT_NAMESPACE
    args = ["adm", "top", "pod", "-n", ns, "--no-headers"]

    # Se specificato un pod, filtra solo quello
    if pod_name:
        args.insert(3, pod_name)  # Inserisce il nome del pod dopo "pod"

    result = _run_oc_command(args)

    if not result["success"]:
        return result

    # Parsa l'output testuale (formato: NAME CPU(cores) MEMORY(bytes))
    usage_list = []
    for line in result["output"].split("\n"):
        parts = line.split()
        if len(parts) >= 3:
            usage_list.append({
                "pod": parts[0],
                "cpu": parts[1],
                "memory": parts[2]
            })

    return {"success": True, "output": usage_list, "error": ""}


# === Entry point per test standalone ===
if __name__ == "__main__":
    print("=== Test OpenShift Client ===")
    
    # Test login
    print("\n1. Login al cluster...")
    login_result = login()
    print(f"   Risultato: {login_result}")
    
    if login_result["success"]:
        # Test get pods
        print(f"\n2. Recupero pod nel namespace '{settings.OPENSHIFT_NAMESPACE}'...")
        pods_result = get_pods()
        print(f"   Risultato: {json.dumps(pods_result, indent=2)}")
