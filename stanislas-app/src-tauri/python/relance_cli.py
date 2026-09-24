"""
Rédige une lettre de relance pour une facture impayée — 100% local, via
le modèle Ollama déjà utilisé ailleurs dans le projet (même schéma que
devis_cli.py, traduire_cli.py...).

Usage :
    python3 relance_cli.py <notes>

Sortie : un marqueur ---RESULTAT--- suivi de la lettre rédigée.
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

    prompt = f"""Voici les informations sur une facture impayée (client, montant,
retard, éventuellement le contenu d'une facture importée) :
---
{notes}
---

Rédige une lettre de relance professionnelle mais courtoise, pour un premier
rappel (pas encore une mise en demeure). Elle doit :
- rappeler poliment la facture concernée (numéro/référence si mentionné, montant, date d'échéance) ;
- indiquer le retard constaté ;
- demander un règlement rapide ;
- rester cordiale, sans menace ni ton agressif.

Réponds uniquement avec le texte de la lettre, prête à être envoyée ou
imprimée telle quelle, sans préambule ni commentaire."""
    return ask(prompt).strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucune information fournie.")
        sys.exit(1)

    notes = sys.argv[1]
    resultat = rediger(notes)

    print("---RESULTAT---")
    print(resultat)
