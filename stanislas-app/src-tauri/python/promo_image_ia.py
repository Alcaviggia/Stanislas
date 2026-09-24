"""
Génère le fond visuel d'une image de promo par IA (Flux Schnell) —
contrairement à maquette_cli.py qui pose le texte par-dessus une photo
avec Python, ici l'IA génère uniquement le fond, sans texte.

Note : Qwen-Image-2512 a été testé (meilleur rendu de texte que Flux en
théorie), mais abandonné — son téléchargement (58 Go) est bridé par
Hugging Face sans compte, comme Flux Dev précédemment. Retour à Flux
Schnell, qui fonctionne de façon fiable et rapide.

Licence Apache 2.0 (miroir libre) — libre d'usage commercial, sans compte requis.

Réutilise la même détection de machine qu'Atelier image.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.detect_machine import profil_image_video
from app.core.ollama_client import ask
from app.memory.memory_store import contexte_pour_prompt

DIMENSIONS = {
    "post": (1024, 1024),
    "story": (768, 1344),
    "banniere": (1344, 384),
    "ads": (1024, 1024),
    "print": (1024, 1344),
}

MODELE_QUALITE = "unsloth/FLUX.1-schnell"

ZONE_TEXTE_PAR_FORMAT = {
    "post": "the bottom fifth of the image",
    "story": "the bottom fifth of the image",
    "banniere": "the sides of the image, keeping the center clear",
    "ads": "the bottom fifth of the image",
    "print": "the top fifth of the image",
}


def enrichir_description_pour_image(description: str, format_cle: str) -> str:
    """Utilise le modèle de texte (Llama) pour transformer une description
    courte en un vrai prompt visuel détaillé — les modèles d'image donnent
    de bien meilleurs résultats avec un prompt riche qu'avec quelques mots."""
    contexte = contexte_pour_prompt()
    zone_texte = ZONE_TEXTE_PAR_FORMAT.get(format_cle, "the bottom of the image")

    prompt_enrichissement = f"""Tu es un expert en prompts pour générateurs d'images IA (comme Flux).
Contexte de l'entreprise : {contexte}

Voici une description brute donnée par un indépendant pour illustrer une promotion :
"{description}"

Transforme cette description en un prompt visuel riche et précis, EN ANGLAIS,
pour un générateur d'image. Décris : le sujet principal, l'éclairage, l'angle
de prise de vue, l'ambiance, les couleurs. Sois concret et évocateur.

RÈGLE IMPORTANTE : le visuel doit garder {zone_texte} relativement simple et
dégagé (peu d'éléments importants là), car un texte sera posé par-dessus
après coup.

Réponds uniquement avec le prompt en anglais, une seule phrase ou deux,
rien d'autre autour."""

    return ask(prompt_enrichissement).strip()


def construire_prompt_fond(description_enrichie: str) -> str:
    """Assemble le prompt final pour Flux à partir de la description déjà enrichie."""
    return (
        f"{description_enrichie} "
        f"Professional commercial photography, clean composition, natural lighting. "
        f"No text, no words, no writing, no letters, no typography."
    )


def generer_fond(description: str, format_cle: str, chemin_sortie: str):
    import torch
    from diffusers import FluxPipeline

    pv = profil_image_video()
    if not pv["image_locale"]:
        print(f"[ERREUR] Machine trop limitée pour la génération d'image IA locale ({pv['raison']}).")
        sys.exit(1)

    largeur, hauteur = DIMENSIONS.get(format_cle, DIMENSIONS["post"])
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    print("Enrichissement de la description avec Llama...", flush=True)
    description_enrichie = enrichir_description_pour_image(description, format_cle)
    print(f"Prompt visuel : {description_enrichie}", flush=True)

    print(f"Chargement du modèle Flux Schnell (device: {device})...", flush=True)
    pipe = FluxPipeline.from_pretrained(MODELE_QUALITE, torch_dtype=torch.bfloat16).to(device)

    prompt = construire_prompt_fond(description_enrichie)
    print("Génération du fond visuel en cours...", flush=True)

    image = pipe(
        prompt=prompt, num_inference_steps=4, guidance_scale=0.0,
        height=hauteur, width=largeur,
    ).images[0]

    image.save(chemin_sortie)
    print("Fond visuel généré.", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--finaliser":
        style_choisi = sys.argv[2] if len(sys.argv) > 2 else "classique"
        dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Promo"))
        chemin_temp = os.path.join(dossier, f".apercu_ia_temp_{style_choisi}.png")
        if not os.path.exists(chemin_temp):
            print("[ERREUR] Aucun aperçu IA à sauvegarder.")
            sys.exit(1)

        from datetime import datetime
        import shutil
        import platform
        import subprocess

        horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
        chemin_final = os.path.join(dossier, f"promo_ia_{style_choisi}_{horodatage}.png")
        shutil.copy(chemin_temp, chemin_final)

        systeme = platform.system()
        try:
            if systeme == "Darwin":
                subprocess.run(["open", chemin_final], check=True)
            elif systeme == "Windows":
                os.startfile(chemin_final)
            else:
                subprocess.run(["xdg-open", chemin_final], check=True)
        except Exception as e:
            print(f"[ERREUR ouverture] {e}")

        print(f"Enregistré : {chemin_final}")
        print("OK")
        sys.exit(0)

    if len(sys.argv) < 3:
        print("[ERREUR] Usage : promo_image_ia.py <description> <texte_promo> [format]")
        sys.exit(1)

    description = sys.argv[1]
    texte_promo = sys.argv[2]
    format_cle = sys.argv[3] if len(sys.argv) > 3 else "post"

    dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Promo"))
    os.makedirs(dossier, exist_ok=True)
    chemin_fond = os.path.join(dossier, ".fond_ia_temp.png")

    # Étape 1 : Flux génère UNIQUEMENT le fond, sans texte
    generer_fond(description, format_cle, chemin_fond)

    # Étape 2 : on réutilise notre système de texte déjà testé (3 styles),
    # posé par-dessus ce fond généré par IA plutôt qu'une photo de l'utilisateur
    from maquette_cli import creer_image, STYLES_DISPONIBLES
    import base64

    for style in STYLES_DISPONIBLES:
        chemin_temp = os.path.join(dossier, f".apercu_ia_temp_{style}.png")
        creer_image(texte_promo, format_cle, chemin_temp, chemin_fond, style)
        with open(chemin_temp, "rb") as f:
            contenu_base64 = base64.b64encode(f.read()).decode("ascii")
        print(f"---IMAGE_{style.upper()}---")
        print(contenu_base64)
