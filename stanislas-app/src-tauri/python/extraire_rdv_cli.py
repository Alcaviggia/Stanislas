"""
Action : Extraire un rendez-vous
Un SMS ou mail long et confus d'un client → uniquement les données utiles :
nom, date souhaitée, prestation demandée, numéro de téléphone.
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask

JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def construire_prompt(message: str) -> str:
    maintenant = datetime.now()
    date_du_jour = f"{JOURS_FR[maintenant.weekday()]} {maintenant.day:02d}/{maintenant.month:02d}/{maintenant.year}"

    return f"""Nous sommes aujourd'hui : {date_du_jour}.

Voici un message reçu d'un client (SMS ou email), potentiellement
long et confus :
---
{message}
---

Extrais UNIQUEMENT ces informations, sous cette forme exacte :
Nom : ...
Date souhaitée : ...
Prestation demandée : ...
Téléphone : ...

Pour "Date souhaitée" : si le message utilise une expression relative
("samedi prochain", "dans 3 jours", "la semaine prochaine"), calcule la
vraie date à partir d'aujourd'hui ({date_du_jour}) et donne le jour et la
date exacte (exemple : "samedi 06/09/2025"). Si une information n'est pas
présente dans le message, écris "non précisé" à la place — ne l'invente
jamais.

Réponds uniquement avec ces 4 lignes, rien d'autre autour."""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucun message fourni.")
        sys.exit(1)

    message = sys.argv[1].strip()
    if not message:
        print("[ERREUR] Le message est vide.")
        sys.exit(1)

    print("Extraction en cours...", flush=True)
    resultat = ask(construire_prompt(message))
    print("Extraction terminée.", flush=True)
    print("---RESULTAT---", flush=True)
    print(resultat)
