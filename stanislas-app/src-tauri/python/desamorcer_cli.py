"""
Action : Désamorcer (avis Google, réclamation client agressive)
L'utilisateur colle l'avis/message reçu, et sa réaction à chaud (souvent
énervée) — Stanislas transforme ça en réponse professionnelle qui protège
la réputation, sans changer le fond de ce que veut dire la personne.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask
from app.memory.memory_store import contexte_pour_prompt


def construire_prompt(avis_recu: str, reaction_a_chaud: str) -> str:
    contexte = contexte_pour_prompt()
    bloc_reaction = f"""
Voici des éléments à prendre en compte dans la réponse (faits, contexte,
ta version des événements) — reprends le fond de ce qui est dit ici,
mais jamais le ton s'il est vif :
---
{reaction_a_chaud}
---
""" if reaction_a_chaud else ""

    return f"""Tu es l'assistant d'un indépendant qui doit répondre à un avis
ou une réclamation client, sans se laisser emporter par l'émotion.
Contexte : {contexte}

Voici l'avis/message reçu (souvent négatif ou injuste) :
---
{avis_recu}
---
{bloc_reaction}
Rédige une réponse professionnelle qui :
- défend fermement les faits, {"en te basant sur les éléments donnés ci-dessus" if reaction_a_chaud else "sans rien inventer que l'avis ne mentionne pas déjà"} — si la
  responsabilité du client dans la situation est claire, la réponse doit
  le dire clairement, sans s'excuser ni proposer de geste commercial pour
  un problème que le client a lui-même causé
- reste courtoise dans le TON, même quand elle est ferme sur le FOND
- ne cède jamais automatiquement — un ton posé ne veut pas dire donner
  raison au client par défaut
- reste courte (3-5 phrases maximum)

Réponds uniquement avec le texte de la réponse, sans préambule ni signature."""


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("[ERREUR] Usage : desamorcer_cli.py <avis_recu> <reaction_a_chaud>")
        sys.exit(1)

    avis_recu = sys.argv[1].strip()
    reaction = sys.argv[2].strip() if len(sys.argv) > 2 else ""

    if not avis_recu:
        print("[ERREUR] L'avis reçu est manquant.")
        sys.exit(1)

    print("Rédaction d'une réponse posée...", flush=True)
    resultat = ask(construire_prompt(avis_recu, reaction))
    print("Réponse prête.", flush=True)
    print("---RESULTAT---", flush=True)
    print(resultat)
