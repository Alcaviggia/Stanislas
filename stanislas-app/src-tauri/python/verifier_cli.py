"""
Action : Vérifier
Un "deuxième regard" sur un document — cherche les incohérences (dates,
montants contradictoires), fautes, informations manquantes ou ambiguës.
Ne prétend jamais être certain à 100% : dit "À vérifier" plutôt qu'affirmer.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask


def construire_prompt(document: str) -> str:
    return f"""Tu es un second regard attentif sur un document professionnel
(devis, contrat, courrier). Cherche :
- des incohérences (deux dates différentes pour la même chose, montants
  qui ne correspondent pas)
- des fautes qui changeraient le sens
- des informations manquantes ou ambiguës
- des formulations qui pourraient poser problème

Voici le document :
---
{document}
---

RÈGLE IMPORTANTE : si tu n'es pas sûr à 100% qu'il y a un vrai problème,
formule-le avec "À vérifier :" plutôt que d'affirmer catégoriquement.
Si tu ne trouves vraiment rien de problématique, dis-le clairement plutôt
que d'inventer un souci pour avoir quelque chose à dire.

Réponds sous forme de liste courte, un point par ligne."""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucun document fourni.")
        sys.exit(1)

    document = sys.argv[1].strip()
    if not document:
        print("[ERREUR] Le document est vide.")
        sys.exit(1)

    print("Vérification en cours...", flush=True)
    resultat = ask(construire_prompt(document))
    print("Vérification terminée.", flush=True)
    print("---RESULTAT---", flush=True)
    print(resultat)
