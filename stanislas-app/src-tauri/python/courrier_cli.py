"""
Version "silencieuse" de Courrier, pour être appelée par l'app Tauri.
Contrairement à courrier.py (qui pose des questions dans le Terminal),
celui-ci lit le mail depuis un fichier fixe, écrit UNIQUEMENT le résultat
sur la sortie standard (rien d'autre), et s'arrête — pas d'interaction.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.ollama_client import ask
from app.memory.memory_store import contexte_pour_prompt

CHEMIN_ENTREE = os.path.join(os.path.dirname(__file__), "courrier_cli_entree.txt")


def construire_prompt(mail_recu: str) -> str:
    contexte = contexte_pour_prompt()
    return f"""Tu es l'assistant de rédaction d'un indépendant.
Voici ce que Stanislas sait déjà de son style et de son entreprise :
{contexte}

Voici le mail reçu :
---
{mail_recu}
---

Rédige une réponse à ce mail, ÉCRITE DANS LA MÊME LANGUE que le mail reçu
(anglais si le mail est en anglais, français si le mail est en français, etc.).

RÈGLES STRICTES :
- Commence directement par une formule de salutation dans la langue du mail
  (par exemple "Hi [Name]," ou "Bonjour," selon le cas) — jamais par une
  phrase qui parle de la langue elle-même.
- N'écris JAMAIS de commentaire du type "C'est en anglais", "This is in French"
  ou toute mention de la langue détectée. Ce n'est pas un texte à afficher,
  seulement une instruction pour toi.
- Ne signe pas à la place de l'utilisateur, termine par [Prénom].

Réponds uniquement avec le texte de la réponse, rien d'autre autour."""


if __name__ == "__main__":
    # Priorité à l'argument passé directement (utilisé par l'app Tauri) ;
    # sinon, on retombe sur le fichier (utile pour tester à la main).
    if len(sys.argv) > 1:
        mail_recu = sys.argv[1].strip()
    elif os.path.exists(CHEMIN_ENTREE):
        with open(CHEMIN_ENTREE, "r", encoding="utf-8") as f:
            mail_recu = f.read().strip()
    else:
        print("[ERREUR] Aucun texte à traiter trouvé.")
        sys.exit(1)

    if not mail_recu:
        print("[ERREUR] Le texte à traiter est vide.")
        sys.exit(1)

    print("Lecture du mail reçu...", flush=True)
    print(f"({len(mail_recu)} caractères à traiter)", flush=True)
    print("Connexion au modèle local (Llama 3.2)...", flush=True)
    print("Rédaction de la réponse en cours...", flush=True)

    resultat = ask(construire_prompt(mail_recu))

    print("Réponse générée.", flush=True)
    print("---RESULTAT---", flush=True)
    print(resultat)
