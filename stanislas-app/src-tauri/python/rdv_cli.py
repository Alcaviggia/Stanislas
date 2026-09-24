"""
Rédige un message proposant des créneaux de rendez-vous — 100% local, via
le modèle Ollama déjà utilisé ailleurs dans le projet. Ne lit pas un vrai
agenda (aucune connexion Calendrier dans cette version) — la personne
décrit ses disponibilités, Stanislas rédige le message.

Usage :
    python3 rdv_cli.py <demande_et_disponibilites>

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

    prompt = f"""Voici la demande de rendez-vous reçue, et/ou les
disponibilités de la personne qui doit répondre :
---
{notes}
---

Rédige un message clair et courtois proposant des créneaux pour ce
rendez-vous, à partir des informations données ci-dessus. Si aucun
créneau précis n'est mentionné, propose une formulation ouverte
demandant à l'autre personne ses disponibilités, plutôt que d'inventer
des dates.

Réponds uniquement avec le texte du message, prêt à être envoyé tel quel,
sans préambule ni commentaire."""
    return ask(prompt).strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucune information fournie.")
        sys.exit(1)

    notes = sys.argv[1]
    resultat = rediger(notes)

    print("---RESULTAT---")
    print(resultat)
