"""
Démarre Ollama — utilise le binaire EMBARQUÉ dans l'app (comme ffmpeg),
pas une installation séparée sur la machine. La personne qui installe
Stanislas n'a jamais besoin d'installer Ollama elle-même ailleurs.

Le chemin du dossier Ollama embarqué est transmis via la variable
d'environnement STANISLAS_OLLAMA_DIR (même mécanisme que pour ffmpeg,
voir optionsEnvironnement() côté interface). Si elle est absente (mode
développement, avant packaging), on retombe sur un "ollama" déjà présent
sur la machine — pratique pour toi en train de développer, sans jamais
bloquer le fonctionnement.
"""
import sys
import os
import json
import time
import subprocess
import urllib.request

OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"


def chemin_ollama() -> str:
    dossier_embarque = os.environ.get("STANISLAS_OLLAMA_DIR")
    if dossier_embarque:
        nom = "ollama.exe" if os.name == "nt" else "ollama"
        chemin = os.path.join(dossier_embarque, nom)
        if os.path.exists(chemin):
            return chemin
    return "ollama"  # repli : celui déjà installé sur la machine (mode dev)


def ollama_deja_actif() -> bool:
    try:
        urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=2)
        return True
    except Exception:
        return False


def demarrer_serveur():
    """Lance 'ollama serve' en arrière-plan, sans bloquer — ne fait rien
    si un serveur Ollama répond déjà (évite les conflits avec une
    installation existante sur la machine du développeur)."""
    if ollama_deja_actif():
        print("SERVEUR_DEJA_ACTIF")
        return

    exe = chemin_ollama()
    try:
        # Détaché : continue de tourner même après la fin de ce script
        subprocess.Popen(
            [exe, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as e:
        print(f"SERVEUR_ECHEC:{e}")
        return

    # Attend que le serveur réponde vraiment, jusqu'à 15 secondes
    for _ in range(30):
        if ollama_deja_actif():
            print("SERVEUR_DEMARRE")
            return
        time.sleep(0.5)

    print("SERVEUR_ECHEC:pas de réponse après 15s")


def telecharger_modele(nom_modele: str) -> bool:
    """Télécharge un modèle via le binaire Ollama embarqué (ou celui du
    système en mode dev) — affiche la progression au fil de l'eau.

    Ollama met à jour sa barre de progression avec des retours chariot
    (\\r, qui réécrivent la même ligne dans un vrai terminal), pas des
    retours à la ligne classiques — une lecture ligne par ligne resterait
    donc silencieuse jusqu'à la toute fin. On lit ici caractère par
    caractère, et on émet une "ligne" à chaque \\r ou \\n rencontré."""
    exe = chemin_ollama()
    try:
        processus = subprocess.Popen(
            [exe, "pull", nom_modele],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        morceau = ""
        while True:
            caractere = processus.stdout.read(1)
            if caractere == "" and processus.poll() is not None:
                break
            if caractere in ("\r", "\n"):
                if morceau.strip():
                    print(morceau.strip(), flush=True)
                morceau = ""
            else:
                morceau += caractere
        if morceau.strip():
            print(morceau.strip(), flush=True)
        processus.wait()
        return processus.returncode == 0
    except Exception as e:
        print(f"[ERREUR téléchargement {nom_modele}] {e}", flush=True)
        return False


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "demarrer"

    if action == "demarrer":
        demarrer_serveur()
    elif action == "telecharger" and len(sys.argv) > 2:
        ok = telecharger_modele(sys.argv[2])
        print("TELECHARGEMENT_OK" if ok else "TELECHARGEMENT_ECHEC")
    else:
        print("[ERREUR] Usage : demarrer_ollama_cli.py demarrer|telecharger <modele>")
        sys.exit(1)
