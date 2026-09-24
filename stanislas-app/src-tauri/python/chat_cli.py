"""
Action : Chat
La seule action qui sort du principe "un bouton = une tâche" — un vrai
dialogue libre avec le modèle local, pour brainstormer ou poser des
questions ouvertes. L'historique de la conversation est géré côté
interface (JS) et transmis en entier à chaque message, puisque chaque
appel à ce script est indépendant (pas de mémoire entre deux appels).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask
from app.memory.memory_store import contexte_pour_prompt


def construire_prompt(historique_formatte: str) -> str:
    contexte = contexte_pour_prompt()
    return f"""Tu es Stanislas, l'assistant local d'un indépendant.
Contexte : {contexte}

Voici la conversation en cours (le dernier message est celui auquel tu dois répondre) :
---
{historique_formatte}
---

Réponds uniquement en tant que Stanislas, de façon naturelle et utile,
sans répéter tout l'historique — juste ta prochaine réponse."""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucun historique de conversation fourni.")
        sys.exit(1)

    historique_formatte = sys.argv[1]

    resultat = ask(construire_prompt(historique_formatte))
    print("---RESULTAT---", flush=True)
    print(resultat)
