"""
Action : Comprendre
Dépose un document/texte confus (courrier administratif, contrat, mail
compliqué), et choisis une question parmi 4 — pas de "prompt" à écrire,
juste un bouton à cliquer.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask
from app.memory.memory_store import contexte_pour_prompt

CONSIGNES = {
    "resumer": (
        "Résume ce document en 3-5 phrases claires, sans jargon. "
        "Va droit à l'essentiel, comme si tu l'expliquais à un ami pressé."
    ),
    "expliquer": (
        "Explique ce document comme si la personne qui le lit n'a aucune "
        "connaissance du sujet — décompose les termes compliqués, le contexte, "
        "pourquoi ce document existe."
    ),
    "que_dois_je_faire": (
        "Dis clairement et uniquement ce que la personne doit FAIRE suite à ce "
        "document : quelles actions, avant quelle date, quels documents à "
        "fournir. Sous forme de liste courte et actionnable. Si rien n'est "
        "demandé, dis-le clairement."
    ),
    "probleme": (
        "Cherche s'il y a un problème, un piège, une clause défavorable, une "
        "date critique, ou une information manquante/inquiétante dans ce "
        "document. Si tu n'es pas sûr à 100%, dis-le clairement avec "
        "'À vérifier :' plutôt que d'affirmer. Si rien de problématique, dis-le."
    ),
}

TITRES = {
    "resumer": "Résumé",
    "expliquer": "Explication",
    "que_dois_je_faire": "Ce qu'il faut faire",
    "probleme": "Points d'attention",
}


def construire_prompt(document: str, mode: str) -> str:
    contexte = contexte_pour_prompt()
    consigne = CONSIGNES.get(mode, CONSIGNES["resumer"])
    return f"""Tu es l'assistant d'un indépendant qui n'a pas le temps ni les
connaissances pour déchiffrer des documents compliqués (administratifs,
contrats, mails longs).
Contexte : {contexte}

Voici le document :
---
{document}
---

Consigne : {consigne}

RÈGLE IMPORTANTE : si une information n'est pas clairement présente dans le
document, ne l'invente jamais — dis "Je ne trouve pas cette information dans
le document" plutôt que de deviner.

Réponds uniquement avec le contenu demandé, sans préambule ni signature."""


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("[ERREUR] Usage : comprendre_cli.py <document> <mode>")
        sys.exit(1)

    document = sys.argv[1].strip()
    mode = sys.argv[2].strip()

    if not document:
        print("[ERREUR] Le document est vide.")
        sys.exit(1)

    titre = TITRES.get(mode, "Résultat")
    print(f"Analyse en cours ({titre})...", flush=True)

    resultat = ask(construire_prompt(document, mode))

    print("Analyse terminée.", flush=True)
    print("---RESULTAT---", flush=True)
    print(resultat)
