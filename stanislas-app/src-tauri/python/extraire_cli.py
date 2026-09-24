"""
Action : Extraire
Dépose un document (devis reçu, facture, carte de visite, email) →
les informations utiles sont extraites automatiquement, prêtes à copier
dans un tableur ou un logiciel de facturation.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask

CHAMPS_PAR_TYPE = {
    "devis": "client, entreprise, montant, TVA, date, délai, numéro de devis",
    "carte_visite": "nom, entreprise, téléphone, email, site web",
    "email": "personne, date, téléphone, adresse, demande, échéance",
    "facture": "client, entreprise, montant, TVA, date d'émission, date d'échéance, numéro de facture",
}

NOMS_TYPE = {
    "devis": "un devis",
    "carte_visite": "une carte de visite",
    "email": "un email",
    "facture": "une facture",
}


def construire_prompt(document: str, type_doc: str) -> str:
    champs = CHAMPS_PAR_TYPE.get(type_doc, CHAMPS_PAR_TYPE["email"])
    nom_type = NOMS_TYPE.get(type_doc, "ce document")
    return f"""Voici {nom_type} :
---
{document}
---

Extrais les champs suivants, un par ligne, sous la forme "Nom du champ : valeur" :
{champs}

Si une information n'est pas présente dans le document, écris "non précisé"
à la place — ne l'invente jamais.

Réponds uniquement avec la liste des champs, rien d'autre autour."""


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("[ERREUR] Usage : extraire_cli.py <document> <type>")
        sys.exit(1)

    document = sys.argv[1].strip()
    type_doc = sys.argv[2].strip()

    if not document:
        print("[ERREUR] Le document est vide.")
        sys.exit(1)

    print("Extraction en cours...", flush=True)
    resultat = ask(construire_prompt(document, type_doc))
    print("Extraction terminée.", flush=True)
    print("---RESULTAT---", flush=True)
    print(resultat)
