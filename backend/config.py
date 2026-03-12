"""
config.py - Caricamento configurazione da variabili d'ambiente.

Legge il file .env dalla root del progetto e fornisce una classe Settings
con tutte le variabili necessarie per OpenShift e Azure DevOps.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# Carica il file .env dalla root del progetto (una directory sopra backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


class Settings:
    """
    Contenitore per tutte le impostazioni dell'applicazione.
    I valori vengono letti dalle variabili d'ambiente (caricate da .env).
    """

    # --- OpenShift ---
    # URL del server API del cluster (es. https://api.cluster.example.com:6443)
    OPENSHIFT_API_URL: str = os.getenv("OPENSHIFT_API_URL", "")
    # Token bearer per autenticazione (ottenibile con: oc whoami -t)
    OPENSHIFT_TOKEN: str = os.getenv("OPENSHIFT_TOKEN", "")
    # Namespace di default per le query
    OPENSHIFT_NAMESPACE: str = os.getenv("OPENSHIFT_NAMESPACE", "default")

    # --- Azure DevOps ---
    # URL dell'organizzazione (es. https://dev.azure.com/myorg)
    AZURE_DEVOPS_ORG_URL: str = os.getenv("AZURE_DEVOPS_ORG_URL", "")
    # Personal Access Token con permessi su Build, Code, Release
    AZURE_DEVOPS_PAT: str = os.getenv("AZURE_DEVOPS_PAT", "")
    # Nome del progetto di default
    AZURE_DEVOPS_PROJECT: str = os.getenv("AZURE_DEVOPS_PROJECT", "")

    @classmethod
    def validate(cls) -> list[str]:
        """
        Verifica che le variabili critiche siano configurate.
        Restituisce una lista di warning per i campi mancanti.
        """
        warnings = []
        if not cls.OPENSHIFT_API_URL:
            warnings.append("OPENSHIFT_API_URL non configurato - i tool OpenShift non funzioneranno")
        if not cls.OPENSHIFT_TOKEN:
            warnings.append("OPENSHIFT_TOKEN non configurato - i tool OpenShift non funzioneranno")
        if not cls.AZURE_DEVOPS_ORG_URL:
            warnings.append("AZURE_DEVOPS_ORG_URL non configurato - i tool Azure DevOps non funzioneranno")
        if not cls.AZURE_DEVOPS_PAT:
            warnings.append("AZURE_DEVOPS_PAT non configurato - i tool Azure DevOps non funzioneranno")
        return warnings


# Istanza globale delle impostazioni
settings = Settings()
