"""
Action : Brouillon → Devis
L'artisan tape ses notes en vrac ("fuite lavabo, joint à changer, 2h de
main d'oeuvre, tuyau cuivre 12mm"), Stanislas génère le paragraphe de
description propre et professionnel à copier-coller dans son logiciel
de facturation.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask
from app.memory.memory_store import contexte_pour_prompt


def construire_prompt(notes: str) -> str:
    contexte = contexte_pour_prompt()
    return f"""Tu es l'assistant d'un artisan/indépendant qui rédige un devis.
Contexte : {contexte}

Voici ses notes en vrac (pas structurées, abrégées) :
---
{notes}
---

Transforme ça en un paragraphe de description professionnel, clair, prêt à
coller directement dans un devis. Garde toutes les informations concrètes
mentionnées (quantités, durées, matériaux) — n'en invente aucune de plus.
Si un prix ou un total n'est pas donné dans les notes, ne l'invente pas.

Réponds uniquement avec le paragraphe final, rien d'autre autour."""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucune note fournie.")
        sys.exit(1)

    notes = sys.argv[1].strip()
    if not notes:
        print("[ERREUR] Les notes sont vides.")
        sys.exit(1)

    print("Rédaction du devis en cours...", flush=True)
    resultat = ask(construire_prompt(notes))
    print("Devis rédigé.", flush=True)
    print("---RESULTAT---", flush=True)
    print(resultat)
