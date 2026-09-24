"""
Transcrit un enregistrement audio (réunion, note vocale...) puis en génère un
résumé avec les points clés — 100% local :
  1) Transcription : bibliothèque "openai-whisper" (modèle tourne en local,
     téléchargé une fois depuis le CDN OpenAI — PAS Hugging Face, donc pas
     soumis à la limitation de débit sans compte qui a fait abandonner
     Flux Dev / Qwen-Image).
  2) Résumé : modèle Ollama local déjà utilisé par les autres fonctions
     (Llama 3.2 / Qwen3), via app.core.ollama_client.ask — même schéma que
     les autres scripts CLI du projet.

Installation requise (une seule fois) :
    pip3 install openai-whisper --break-system-packages
    (nécessite aussi ffmpeg installé sur la machine : `brew install ffmpeg`
    sur Mac, ou l'équivalent Windows)

Usage :
    python3 transcription_cli.py <chemin_vers_fichier_audio>

Sortie attendue par l'app (mêmes conventions que les autres CLI du projet) :
    des lignes de progression sur stdout, puis un marqueur ---RESULTAT---
    suivi du texte final (résumé + transcription complète).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# Whisper a besoin de ffmpeg en coulisses pour décoder l'audio — on rend
# prioritaire le ffmpeg embarqué de l'app (même mécanisme que video_cli.py
# et montage_video_cli.py), pour ne jamais dépendre d'une installation
# séparée de ffmpeg sur la machine.
_dossier_ffmpeg_embarque = os.environ.get("STANISLAS_FFMPEG_DIR")
if _dossier_ffmpeg_embarque:
    os.environ["PATH"] = _dossier_ffmpeg_embarque + os.pathsep + os.environ.get("PATH", "")

# Adapte cet import si l'emplacement réel diffère dans ton projet — ce
# script suit le même schéma que les autres CLI (ex: promo_cli.py) qui
# utilisent app.core.ollama_client.ask() pour parler au modèle local.
try:
    from app.core.ollama_client import ask
except ImportError:
    ask = None  # Permet au script de tourner en mode "transcription seule"
    # si le module maison n'est pas trouvé, plutôt que de planter net.


TAILLE_MODELE_WHISPER = "small"
# Modèles disponibles, du plus léger/rapide au plus précis/lent :
# "tiny", "base", "small", "medium", "large"
# "small" est un bon compromis par défaut pour un Mac M1 avec 16 Go+ de RAM.


def transcrire(chemin_audio: str) -> str:
    import whisper  # import ici pour ne pas alourdir le démarrage du script

    print(f"Chargement du modèle Whisper ({TAILLE_MODELE_WHISPER})...")
    modele = whisper.load_model(TAILLE_MODELE_WHISPER)

    print("Transcription en cours (peut prendre plusieurs minutes selon la durée)...")
    resultat = modele.transcribe(chemin_audio, language="fr", verbose=False)

    return resultat["text"].strip()


def resumer(transcription: str) -> str:
    if ask is None:
        return "(Résumé indisponible : module de langage local introuvable — voici uniquement la transcription brute ci-dessous.)"

    prompt = f"""Voici la transcription brute d'une réunion :
---
{transcription}
---

Rédige :
1. Un résumé en 3 à 5 phrases de ce qui a été dit.
2. Les points clés / décisions prises, sous forme de liste à puces.
3. S'il y a des actions à faire, une liste "À faire" avec qui/quoi si mentionné.

Réponds uniquement avec ce contenu structuré, sans préambule."""
    return ask(prompt)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucun fichier audio fourni.")
        sys.exit(1)

    chemin_audio = sys.argv[1]

    if not os.path.exists(chemin_audio):
        print(f"[ERREUR] Fichier introuvable : {chemin_audio}")
        sys.exit(1)

    try:
        transcription = transcrire(chemin_audio)
    except ModuleNotFoundError:
        print("[ERREUR] La bibliothèque 'openai-whisper' n'est pas installée.")
        print("Lance : pip3 install openai-whisper --break-system-packages")
        sys.exit(1)
    except Exception as e:
        print(f"[ERREUR transcription] {e}")
        sys.exit(1)

    print("Génération du résumé...")
    try:
        resume = resumer(transcription)
    except Exception as e:
        resume = f"(Résumé indisponible : {e})"

    resultat_final = f"{resume}\n\n---\nTranscription complète :\n{transcription}"

    print("---RESULTAT---")
    print(resultat_final)
