"""
Compare deux textes (devis, contrats, offres, versions d'un texte) et
met en évidence ce qui change entre les deux — 100% local, via Ollama.

Différent de Vérifier (qui cherche des anomalies dans UN SEUL texte) :
Comparer répond à "qu'est-ce qui est différent entre A et B ?", pas
"y a-t-il un problème dans ce texte ?".

Usage :
    python3 comparer_cli.py <texte_a> <texte_b>

Sortie : un marqueur ---RESULTAT--- suivi de la comparaison.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.core.ollama_client import ask
except ImportError:
    ask = None


def comparer(texte_a: str, texte_b: str) -> str:
    if ask is None:
        return "(Comparaison indisponible : module de langage local introuvable.)"

    prompt = f"""Voici deux textes ou documents (A et B) à comparer — ça
peut être deux devis, deux contrats, deux offres, ou deux versions
d'un même texte :

--- TEXTE A ---
{texte_a}
--- TEXTE B ---
{texte_b}
---

Compare-les et présente clairement :

1. **Ce qui est identique** : les points communs importants (en une
   ou deux lignes, pas besoin de détailler ce qui ne change pas).

2. **Ce qui est différent** : sous forme de tableau si possible
   (Point | A | B), toutes les différences concrètes repérées
   (montants, conditions, formulations, dates, etc.).

3. **Avantages / inconvénients de chaque côté** : si le contexte s'y
   prête (ex : deux devis, deux offres), dis clairement ce qui rend A
   ou B préférable sur chaque point, sans recommandation générale
   forcée si ce n'est pas pertinent.

Reste factuel, base-toi uniquement sur ce qui est écrit dans les deux
textes — ne suppose rien qui ne soit pas écrit. Réponds directement
avec la comparaison, sans préambule."""

    return ask(prompt).strip()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("[ERREUR] Usage : comparer_cli.py <texte_a> <texte_b>")
        sys.exit(1)

    texte_a = sys.argv[1]
    texte_b = sys.argv[2]

    print("---RESULTAT---")
    print(comparer(texte_a, texte_b))
