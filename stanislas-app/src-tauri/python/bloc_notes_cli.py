"""
Version "silencieuse" de Bloc-notes, pour être appelée par l'app Tauri.
Reçoit le texte à traiter en premier argument, et la consigne (optionnelle)
en second argument. Écrit uniquement le résultat sur la sortie standard.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask
from app.memory.memory_store import contexte_pour_prompt


def construire_prompt(texte: str, consigne: str = "") -> str:
    contexte = contexte_pour_prompt()
    instruction = consigne if consigne else "Résume ce texte en quelques phrases claires."
    return f"""Tu es l'assistant de rédaction d'un indépendant.
Style habituel : {contexte}

Voici le texte à traiter :
---
{texte}
---

Consigne : {instruction}
Réponds uniquement avec le résultat, sans commentaire autour."""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucun texte à traiter.")
        sys.exit(1)

    texte = sys.argv[1].strip()
    consigne = sys.argv[2].strip() if len(sys.argv) > 2 else ""

    if not texte:
        print("[ERREUR] Le texte à traiter est vide.")
        sys.exit(1)

    resultat = ask(construire_prompt(texte, consigne))
    print(resultat)
