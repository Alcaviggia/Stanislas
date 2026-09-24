"""
Action : Offre d'emploi
Quelques critères simples (métier, salaire, horaires) → une annonce
attractive et claire, prête à publier.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask
from app.memory.memory_store import contexte_pour_prompt


def construire_prompt(metier: str, salaire: str, horaires: str, details: str) -> str:
    contexte = contexte_pour_prompt()
    details_txt = f"\nAutres précisions : {details}" if details else ""
    return f"""Tu es l'assistant d'un indépendant qui recrute.
Contexte de l'entreprise : {contexte}

Poste recherché : {metier}
Salaire/rémunération : {salaire}
Horaires : {horaires}{details_txt}

Rédige une offre d'emploi attractive et claire, prête à publier (site
d'emploi, réseaux sociaux, vitrine). Ton chaleureux mais professionnel,
va à l'essentiel — les personnes qui lisent ce genre d'annonce n'ont pas
le temps de lire un roman.

Réponds uniquement avec le texte de l'annonce, rien d'autre autour."""


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("[ERREUR] Usage : offre_emploi_cli.py <metier> <salaire> <horaires> [details]")
        sys.exit(1)

    metier = sys.argv[1].strip()
    salaire = sys.argv[2].strip()
    horaires = sys.argv[3].strip()
    details = sys.argv[4].strip() if len(sys.argv) > 4 else ""

    if not metier:
        print("[ERREUR] Le métier recherché est requis.")
        sys.exit(1)

    print("Rédaction de l'offre en cours...", flush=True)
    resultat = ask(construire_prompt(metier, salaire, horaires, details))
    print("Offre rédigée.", flush=True)
    print("---RESULTAT---", flush=True)
    print(resultat)
