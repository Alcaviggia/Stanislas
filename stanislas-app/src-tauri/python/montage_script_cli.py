"""
Rédige un texte de voix off pour une vidéo, à partir d'un simple sujet tapé
par l'utilisateur — 100% local, via le modèle Ollama déjà utilisé ailleurs
dans le projet (même schéma que promo_cli.py, transcription_cli.py...).

Usage :
    python3 montage_script_cli.py <sujet>

Sortie : un marqueur ---RESULTAT--- suivi du texte rédigé.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.core.ollama_client import ask
except ImportError:
    ask = None


def rediger(sujet: str) -> str:
    if ask is None:
        return f"(Rédaction indisponible : module de langage local introuvable.)\n\nSujet : {sujet}"

    prompt = f"""Rédige le texte d'une voix off pour une courte vidéo sur ce sujet :
"{sujet}"

Consignes :
- 4 à 8 phrases courtes, faciles à lire à voix haute.
- Ton chaleureux et clair, pas de jargon.
- Pas de titre, pas de mise en forme, juste le texte à dire tel quel.

Réponds uniquement avec le texte de la voix off."""
    return ask(prompt).strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucun sujet fourni.")
        sys.exit(1)

    sujet = sys.argv[1]
    texte = rediger(sujet)

    print("---RESULTAT---")
    print(texte)
