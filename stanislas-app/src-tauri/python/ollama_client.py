"""
Petite passerelle vers le modèle local (Ollama).
Toutes les actions passent par ici — un seul endroit à changer
si un jour on veut router vers un autre modèle local ou cloud.
"""
import json
import os
import subprocess
import urllib.request

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"


def _chemin_ollama() -> str:
    """Chemin vers le vrai binaire Ollama embarqué (même mécanisme que
    demarrer_ollama_cli.py) — repli sur "ollama" du système en mode dev."""
    dossier_embarque = os.environ.get("STANISLAS_OLLAMA_DIR")
    if dossier_embarque:
        nom = "ollama.exe" if os.name == "nt" else "ollama"
        chemin = os.path.join(dossier_embarque, nom)
        if os.path.exists(chemin):
            return chemin
    return "ollama"


def modele_par_defaut() -> str:
    """Modèle de texte par défaut — indépendant de la langue de
    l'interface (l'affichage et le modèle IA sont deux choses
    différentes). Ministral par défaut ; l'autre modèle (Qwen3) reste
    disponible et peut être appelé explicitement si besoin."""
    return "ministral-3:8b"


def embed(texte: str, model: str = "nomic-embed-text") -> list:
    """Transforme un texte en vecteur numérique (empreinte de sens), via Ollama."""
    payload = json.dumps({"model": model, "prompt": texte}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/embeddings",
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


MODELE_SECOURS = "qwen3:8b"


def _appel_ollama(prompt: str, model: str) -> str:
    """Appelle directement "ollama run" (le vrai programme), pas l'API
    réseau — changement de méthode du 18/09 : tous les tests manuels de
    l'utilisateur via "ollama run" en Terminal ont toujours réussi
    (plusieurs dizaines de tests), alors que les appels réseau
    (urllib/HTTP vers l'API) échouaient de façon intermittente malgré
    de nombreux essais de réglages différents. On utilise donc la même
    méthode que celle qui s'est montrée fiable chez l'utilisateur."""
    resultat = subprocess.run(
        [_chemin_ollama(), "run", model, prompt],
        capture_output=True, text=True, timeout=600,
    )
    if resultat.returncode != 0:
        raise RuntimeError(resultat.stderr.strip() or "échec de la commande ollama run")
    return resultat.stdout.strip()


def ask(prompt: str, model: str = None) -> str:
    """Envoie un prompt au modèle local et renvoie le texte généré.
    Si le modèle demandé ne répond pas, retente automatiquement avec
    l'autre modèle de texte disponible avant d'abandonner — les deux
    modèles se complètent ainsi vraiment, plutôt que le second restant
    inutilisé."""
    modele_principal = model or modele_par_defaut()

    try:
        return _appel_ollama(prompt, modele_principal)
    except Exception as premiere_erreur:
        if modele_principal == MODELE_SECOURS:
            modele_repli = modele_par_defaut()
        else:
            modele_repli = MODELE_SECOURS
        try:
            return _appel_ollama(prompt, modele_repli)
        except Exception as e:
            return (
                "[Stanislas n'a pas pu joindre le modèle local. "
                f"Vérifie qu'Ollama est bien lancé. Détail : {e}]"
            )
