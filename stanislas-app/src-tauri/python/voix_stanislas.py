"""
Fait parler Stanislas selon la situation — 100% local, aucun appel réseau :
voix système macOS (`say`) ou voix système Windows (SAPI via PowerShell).

Remplace l'ancien script qui ne disait qu'une seule phrase fixe ("HELLO I'm
STANISLAS") quelle que soit la situation. Ici, une petite banque de phrases
variées est tirée au sort selon l'évènement, pour ne pas répéter toujours la
même chose.

Usage :
    python3 voix_stanislas.py <evenement>

Évènements reconnus : bienvenue, fin_tache, erreur, alerte
(un évènement inconnu retombe sur les phrases de "fin_tache")
"""
import sys
import os
import random
import subprocess
import platform

PHRASES = {
    "bienvenue": [
        "Bonjour, je suis Stanislas.",
        "Stanislas est prêt.",
        "Bonjour ! Stanislas à votre service.",
        "Stanislas est en ligne, tout tourne en local.",
    ],
    "fin_tache": [
        "C'est prêt.",
        "Voilà, c'est fait.",
        "Tâche terminée.",
        "J'ai terminé.",
        "C'est bon, le résultat est disponible.",
        "Et voilà, c'est réglé.",
    ],
    "erreur": [
        "Il y a eu un problème.",
        "Ça n'a pas fonctionné, désolé.",
        "Une erreur s'est produite.",
        "Je n'ai pas réussi à terminer cette tâche.",
        "Quelque chose s'est mal passé, regarde la fenêtre Processus.",
    ],
    "alerte": [
        "Attention, un point nécessite ton attention.",
        "Il y a une notification à consulter.",
        "Une alerte t'attend.",
        "N'oublie pas de vérifier tes notifications.",
    ],
}

# Version anglaise des mêmes phrases, utilisée automatiquement quand une
# voix anglaise est choisie (sinon lire du texte français avec un accent
# anglais serait bizarre à l'oreille).
PHRASES_EN = {
    "bienvenue": [
        "Hello, I'm Stanislas.",
        "Stanislas is ready.",
        "Hi there! Stanislas at your service.",
        "Stanislas is online, everything runs locally.",
    ],
    "fin_tache": [
        "All done.",
        "There you go, it's finished.",
        "Task completed.",
        "I'm done.",
        "All good, your result is ready.",
        "And that's sorted.",
    ],
    "erreur": [
        "Something went wrong.",
        "That didn't work, sorry.",
        "An error occurred.",
        "I couldn't finish this task.",
        "Something went sideways, check the Process window.",
    ],
    "alerte": [
        "Heads up, something needs your attention.",
        "There's a notification to check.",
        "An alert is waiting for you.",
        "Don't forget to check your notifications.",
    ],
}

# Voix françaises et anglaises confirmées réellement présentes sur la
# machine de test (via `say -v '?'`) — les noms initialement choisis
# (Audrey, Nicolas, Alex) n'existaient PAS sur macOS 26, say retombait
# donc silencieusement sur la voix anglaise par défaut du système, quel
# que soit le choix fait dans l'app. Ces noms-ci ont été vérifiés présents.
VOIX_DISPONIBLES = {
    "stanislas": "Thomas",    # homme, France
    "homme": "Jacques",       # homme, France
    "femme": "Amélie",        # femme, Québec
    "homme_en": "Fred",       # homme, anglais (US)
    "femme_en": "Samantha",   # femme, anglais (US)
}

# Choix dont la voix est anglaise : on bascule alors sur PHRASES_EN
CHOIX_ANGLAIS = {"homme_en", "femme_en"}

# Peut être surchargé par la variable d'environnement STANISLAS_VOIX_CHOIX
# (positionnée côté JS selon le choix fait dans les Préférences), sinon
# valeur par défaut ci-dessous.
CHOIX_PAR_DEFAUT = "stanislas"


def choix_voix_actuel() -> str:
    return os.environ.get("STANISLAS_VOIX_CHOIX", CHOIX_PAR_DEFAUT)


def nom_voix_mac() -> str:
    choix = choix_voix_actuel()
    return VOIX_DISPONIBLES.get(choix, VOIX_DISPONIBLES[CHOIX_PAR_DEFAUT])


def banque_phrases() -> dict:
    return PHRASES_EN if choix_voix_actuel() in CHOIX_ANGLAIS else PHRASES


def genre_voix_windows() -> str:
    """Sur Windows, chercher un nom exact ('Thomas', 'Amélie'...) ne marche
    presque jamais : les voix françaises n'y sont, sauf exception, pas
    installées par défaut. Au lieu de ça, on demande juste un GENRE
    (homme/femme) à SAPI, qui choisit lui-même parmi les voix déjà
    présentes sur le PC — ça fonctionne avec n'importe quelle machine
    Windows, sans rien à télécharger."""
    choix = choix_voix_actuel()
    return "Female" if choix in ("femme", "femme_en") else "Male"


def parler(texte: str) -> None:
    systeme = platform.system()
    try:
        if systeme == "Darwin":
            subprocess.run(["say", "-v", nom_voix_mac(), texte], check=False)
        elif systeme == "Windows":
            texte_echappe = texte.replace("'", "")
            genre = genre_voix_windows()
            commande_ps = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"try {{ $s.SelectVoiceByHints('{genre}') }} catch {{}}; "
                f"$s.Speak('{texte_echappe}')"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", commande_ps], check=False)
        else:
            # Linux : pas de voix système simple et universelle, on affiche
            # au moins le texte pour ne pas échouer silencieusement.
            print(texte)
    except Exception as e:
        print(f"[voix indisponible] {e}")


if __name__ == "__main__":
    evenement = sys.argv[1] if len(sys.argv) > 1 else "bienvenue"
    phrases = banque_phrases()
    liste = phrases.get(evenement, phrases["fin_tache"])
    parler(random.choice(liste))

