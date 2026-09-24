"""
Calculatrice en langage naturel — 100% local. L'IA (Ollama) interprète
la demande et la transforme en expression mathématique claire, mais
c'est toujours PYTHON qui effectue le calcul réel : un modèle de
langage peut se tromper en arithmétique, un vrai calcul ne se trompe
jamais.

Gère : calculs simples ou complexes, pourcentages, TVA, proportions,
comparaisons de montants, durées. Pas les conversions de devises
(taux de change variable, pas de connexion internet dans l'app).

Usage :
    python3 calculer_cli.py <demande en langage naturel>

Sortie : un marqueur ---RESULTAT--- suivi de l'explication et du résultat.
"""
import sys
import os
import ast
import operator

sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.core.ollama_client import ask
except ImportError:
    ask = None


# Évaluateur sûr — n'autorise que les opérations mathématiques de base,
# jamais d'exécution de code arbitraire (contrairement à eval() brut)
OPERATEURS_AUTORISES = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def _evaluer_noeud(noeud):
    if isinstance(noeud, ast.Constant):
        if isinstance(noeud.value, (int, float)):
            return noeud.value
        raise ValueError("valeur non numérique")
    if isinstance(noeud, ast.BinOp):
        op = OPERATEURS_AUTORISES.get(type(noeud.op))
        if op is None:
            raise ValueError("opération non autorisée")
        return op(_evaluer_noeud(noeud.left), _evaluer_noeud(noeud.right))
    if isinstance(noeud, ast.UnaryOp):
        op = OPERATEURS_AUTORISES.get(type(noeud.op))
        if op is None:
            raise ValueError("opération non autorisée")
        return op(_evaluer_noeud(noeud.operand))
    raise ValueError("expression non autorisée")


def calculer_expression(expression: str):
    """Évalue une expression mathématique en toute sécurité — renvoie
    None si l'expression n'est pas une expression mathématique valide,
    plutôt que de planter ou d'exécuter n'importe quoi."""
    try:
        arbre = ast.parse(expression, mode="eval")
        return _evaluer_noeud(arbre.body)
    except Exception:
        return None


def repondre(demande: str) -> str:
    if ask is None:
        return "(Calcul indisponible : module de langage local introuvable.)"

    prompt = f"""Voici une demande de calcul, en langage naturel : "{demande}"

Transforme-la en une expression mathématique Python valide (uniquement
des nombres et les opérateurs + - * / ** % et parenthèses — rien
d'autre, pas de fonctions, pas de variables).

Réponds UNIQUEMENT avec cette expression, sur une seule ligne, sans
aucun texte autour, sans le mot "Résultat", juste l'expression brute.

Exemples :
- "20% de 150" → 150 * 0.20
- "150 plus 20%" → 150 * 1.20
- "TVA à 20% sur 80 euros HT" → 80 * 1.20
- "différence en % entre 120 et 150" → (150 - 120) / 120 * 100
- "3 heures 45 plus 1 heure 30 en minutes" → 3*60 + 45 + 1*60 + 30"""

    expression = ask(prompt).strip()
    # Nettoyage : garde uniquement la première ligne, retire un
    # éventuel habillage de code ```...```
    expression = expression.split("\n")[0].strip().strip("`").strip()

    resultat = calculer_expression(expression)

    if resultat is None:
        # L'IA n'a pas produit une expression mathématique valide —
        # on le dit clairement plutôt que d'inventer un résultat
        return (
            f"Je n'ai pas réussi à transformer ta demande en calcul précis.\n\n"
            f"Essaie de la reformuler plus simplement (ex : \"20% de 150\", "
            f"\"TVA 20% sur 80€\", \"différence entre 120 et 150 en %\")."
        )

    # Présente un résultat propre, avec l'expression utilisée pour la transparence
    if isinstance(resultat, float) and resultat == int(resultat):
        resultat_affiche = str(int(resultat))
    elif isinstance(resultat, float):
        resultat_affiche = f"{resultat:.4f}".rstrip("0").rstrip(".")
    else:
        resultat_affiche = str(resultat)

    return f"**Résultat : {resultat_affiche}**\n\n(Calcul effectué : {expression})"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucune demande fournie.")
        sys.exit(1)

    demande = sys.argv[1]
    print("---RESULTAT---")
    print(repondre(demande))
