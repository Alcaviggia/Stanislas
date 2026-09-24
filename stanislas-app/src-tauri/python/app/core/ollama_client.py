"""
Petite passerelle vers le modèle local (Ollama).
Toutes les actions passent par ici — un seul endroit à changer
si un jour on veut router vers un autre modèle local ou cloud.
"""
import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3:8b"


def embed(texte: str, model: str = "nomic-embed-text") -> list:
    """Transforme un texte en vecteur numérique (empreinte de sens), via Ollama."""
    payload = json.dumps({"model": model, "prompt": texte}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("embedding", [])
    except Exception as e:
        print(f"[Erreur embedding : {e}]")
        return []


def ask(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Envoie un prompt au modèle local et renvoie le texte généré."""
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception as e:
        return (
            "[Stanislas n'a pas pu joindre le modèle local. "
            f"Vérifie qu'Ollama est bien lancé. Détail : {e}]"
        )
