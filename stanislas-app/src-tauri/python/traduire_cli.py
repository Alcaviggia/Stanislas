"""
Traduit un texte vers la langue choisie — 100% local, via le modèle
Ollama déjà utilisé ailleurs dans le projet (même schéma que
promo_cli.py, verifier_cli.py...).

Usage :
    python3 traduire_cli.py <texte> <langue_cible>

Sortie : un marqueur ---RESULTAT--- suivi du texte traduit.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# Adapte cet import si l'emplacement réel diffère dans ton projet — ce
# script suit le même schéma que les autres CLI (ex: promo_cli.py) qui
# utilisent app.core.ollama_client.ask() pour parler au modèle local.
try:
    from app.core.ollama_client import ask
except ImportError:
    ask = None


def traduire(texte: str, langue_cible: str) -> str:
    if ask is None:
        return "(Traduction indisponible : module de langage local introuvable.)"

    prompt = f"""Traduis le texte suivant en {langue_cible}. Si le texte est déjà
en {langue_cible}, dis-le simplement plutôt que de le recopier.

Texte à traduire :
---
{texte}
---

Réponds uniquement avec la traduction, sans préambule, sans commentaire,
sans recopier le texte original."""
    return ask(prompt).strip()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("[ERREUR] Usage : traduire_cli.py <texte> <langue_cible>")
        sys.exit(1)

    texte_source = sys.argv[1]
    langue_cible = sys.argv[2]

    resultat = traduire(texte_source, langue_cible)

    print("---RESULTAT---")
    print(resultat)
