"""
Version "silencieuse" de Promo, pour être appelée par l'app Tauri.
Reçoit la description de ce qu'il faut annoncer en premier argument.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask
from app.memory.memory_store import contexte_pour_prompt


CONSIGNES_FORMAT = {
    "post": "Un post pour Instagram/Facebook : accroche courte (1-2 phrases), ton chaleureux, 3 à 5 hashtags pertinents à la fin.",
    "story": "Une Story/Reel : très court (1 phrase percutante maximum), direct, pensé pour être lu en 2 secondes, pas de hashtags.",
    "banniere": "Une bannière web : une seule phrase très courte et accrocheuse (10 mots maximum), pas de hashtags, pas de ponctuation superflue.",
    "ads": "Une publicité payante (Ads) : direct, orienté action, avec un appel à l'action clair à la fin (ex: 'Réservez maintenant', 'Contactez-nous'), sans hashtags.",
    "print": "Un support imprimé (flyer/affiche) : texte sobre et clair, sans hashtags, sans emoji, adapté à une lecture papier.",
}


def construire_prompt(description: str, format_cle: str = "post") -> str:
    contexte = contexte_pour_prompt()
    consigne_format = CONSIGNES_FORMAT.get(format_cle, CONSIGNES_FORMAT["post"])
    return f"""Tu es l'assistant de communication d'un indépendant.
Style : {contexte}

Voici ce qu'il faut annoncer :
---
{description}
---

Format demandé : {consigne_format}

Réponds uniquement avec le texte final, rien d'autre autour."""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucune description fournie.")
        sys.exit(1)

    description = sys.argv[1].strip()
    format_cle = sys.argv[2].strip() if len(sys.argv) > 2 else "post"

    if not description:
        print("[ERREUR] La description est vide.")
        sys.exit(1)

    print("Rédaction du post en cours...", flush=True)
    resultat = ask(construire_prompt(description, format_cle))
    print("Post généré.", flush=True)
    print("---RESULTAT---", flush=True)
    print(resultat)
