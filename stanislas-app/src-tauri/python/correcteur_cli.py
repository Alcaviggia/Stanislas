"""
Action : Correcteur
Corrige l'orthographe et la grammaire d'un texte SANS changer le style,
le ton ni le vocabulaire de la personne — contrairement à un correcteur
classique qui a tendance à "améliorer" et rendre le texte pompeux.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask


def construire_prompt(texte: str) -> str:
    return f"""Corrige UNIQUEMENT les fautes d'orthographe et de grammaire du
texte suivant. Ne change RIEN d'autre : garde exactement le même style, le
même ton, le même niveau de langage, les mêmes mots choisis par la personne
(même si une formulation plus "soignée" te viendrait à l'esprit — ce n'est
pas demandé). Ne reformule pas les phrases si elles sont grammaticalement
correctes, même si tu les tournerais différemment.

Porte une attention particulière aux confusions d'homophones (mots qui se
prononcent pareil mais s'écrivent différemment et n'ont pas le même sens) —
c'est le type d'erreur le plus souvent raté. Exemples : vain/vin/vingt/vint,
ou/où, a/à, et/est, ce/se, ces/ses/c'est, on/ont, son/sont, la/là/l'a,
quelle/qu'elle. Relis chaque mot du texte en te demandant s'il a vraiment
le sens voulu dans la phrase, pas seulement s'il est écrit sans faute en
tant que mot isolé.

Texte à corriger :
---
{texte}
---

Réponds uniquement avec le texte corrigé, rien d'autre autour."""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucun texte fourni.")
        sys.exit(1)

    texte = sys.argv[1].strip()
    if not texte:
        print("[ERREUR] Le texte est vide.")
        sys.exit(1)

    print("Correction en cours...", flush=True)
    resultat = ask(construire_prompt(texte))
    print("Correction terminée.", flush=True)
    print("---RESULTAT---", flush=True)
    print(resultat)
