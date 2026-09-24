"""
Rédige un message de relance pour un prospect sans nouvelles — 100% local,
via le modèle Ollama déjà utilisé ailleurs dans le projet (même schéma que
relance_cli.py, devis_cli.py...).

Usage :
    python3 prospects_cli.py <notes>

Sortie : un marqueur ---RESULTAT--- suivi du message rédigé.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.core.ollama_client import ask
except ImportError:
    ask = None


def rediger(notes: str) -> str:
    if ask is None:
        return "(Rédaction indisponible : module de langage local introuvable.)"

    prompt = f"""Voici les informations disponibles sur un prospect qui n'a pas
donné de nouvelles depuis quelques jours — cela peut être une simple note,
ou plusieurs échanges/documents importés (emails, comptes-rendus...),
chacun repéré par "--- Document : nom_du_fichier ---" :
---
{notes}
---

Fais d'abord, pour toi-même, une synthèse mentale de ce qui a été échangé
avec ce prospect (ce qu'il cherche, ses objections ou hésitations
éventuelles, où en était la discussion) — mais NE l'écris PAS dans ta
réponse, elle doit rester uniquement en préparation.

Rédige ensuite un message de relance amical et professionnel pour
reprendre contact. Il doit :
- faire référence naturellement et précisément à ce qui a été discuté (sans rien inventer si l'information manque) ;
- rester léger, sans pression ni ton commercial insistant ;
- proposer un prochain pas concret, cohérent avec où en était la discussion ;
- rester court (quelques phrases).

Réponds uniquement avec le texte du message, prêt à être envoyé tel quel,
sans préambule, sans résumé visible, sans commentaire."""
    return ask(prompt).strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucune information fournie.")
        sys.exit(1)

    notes = sys.argv[1]
    resultat = rediger(notes)

    print("---RESULTAT---")
    print(resultat)
