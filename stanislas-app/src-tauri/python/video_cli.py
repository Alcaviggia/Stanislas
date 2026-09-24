"""
Génère une vraie vidéo MP4 (pas un GIF limité à 256 couleurs, qui donnait
un rendu délavé sur les photos) — les éléments (fond, badge, titre,
bouton) apparaissent progressivement, dans l'esprit d'une présentation
Mac classique.

Utilise ffmpeg pour l'encodage — le même binaire déjà embarqué pour
Montage vidéo (voir STANISLAS_FFMPEG_DIR, positionnée côté JS). Toujours
pas de la vraie génération vidéo IA — ça reste un gros chantier séparé,
qui demande du matériel que la config minimale visée ne peut pas offrir.
"""
import sys
import os
import shutil
import subprocess
import tempfile
import textwrap

sys.path.insert(0, os.path.dirname(__file__))

from maquette_cli import (
    DIMENSIONS, trouver_police, trouver_police_grasse,
    extraire_couleur_accent, detecter_pourcentage,
)

# Si l'app a embarqué son propre binaire ffmpeg, on le rend prioritaire
# dans le PATH — même mécanisme que montage_video_cli.py, pour ne jamais
# dépendre d'une installation séparée de ffmpeg sur la machine
_dossier_ffmpeg_embarque = os.environ.get("STANISLAS_FFMPEG_DIR")
if _dossier_ffmpeg_embarque:
    os.environ["PATH"] = _dossier_ffmpeg_embarque + os.pathsep + os.environ.get("PATH", "")


def construire_fond(chemin_image_fond, largeur, hauteur):
    from PIL import Image
    if chemin_image_fond and os.path.exists(chemin_image_fond):
        fond = Image.open(chemin_image_fond).convert("RGB")
        ratio_cible = largeur / hauteur
        ratio_fond = fond.width / fond.height
        if ratio_fond > ratio_cible:
            nh, nl = hauteur, int(hauteur * ratio_fond)
        else:
            nl, nh = largeur, int(largeur / ratio_fond)
        fond = fond.resize((nl, nh))
        gauche, haut = (nl - largeur) // 2, (nh - hauteur) // 2
        return fond.crop((gauche, haut, gauche + largeur, haut + hauteur))
    return Image.new("RGB", (largeur, hauteur), "#3a5a40")


def creer_animation(texte: str, format_cle: str, chemin_image_fond: str, chemin_sortie: str):
    from PIL import Image, ImageDraw

    largeur, hauteur = DIMENSIONS.get(format_cle, DIMENSIONS["post"])
    fond_base = construire_fond(chemin_image_fond, largeur, hauteur).convert("RGBA")
    marge = int(largeur * 0.06)

    pourcentage = detecter_pourcentage(texte)
    if format_cle == "banniere":
        police_titre = trouver_police_grasse(max(20, int(hauteur * 0.22)))
        largeur_car = int((largeur - 2 * marge) / (hauteur * 0.22 * 0.55))
        lignes_titre = textwrap.wrap(texte, width=max(largeur_car, 10))[:2]
        texte_titre = "\n".join(lignes_titre)
        y_titre = int(hauteur * 0.3)
    else:
        police_titre = trouver_police_grasse(max(28, int(largeur * 0.055)))
        largeur_car = int((largeur - 2 * marge) / (largeur * 0.055 * 0.55))
        lignes_titre = textwrap.wrap(texte, width=max(largeur_car, 8))[:3]
        texte_titre = "\n".join(lignes_titre)
        y_titre = int(hauteur * 0.62)

    r_accent, g_accent, b_accent = extraire_couleur_accent(fond_base.convert("RGB"), 0, int(largeur * 0.2))
    couleur_bouton = (min(r_accent + 60, 255), min(g_accent + 30, 255), min(b_accent + 10, 255))

    def ease_out_cubic(t):
        """Accélère puis ralentit en douceur, plutôt qu'un mouvement linéaire
        et mécanique — la base de toute animation qui a l'air professionnelle."""
        return 1 - pow(1 - t, 3)

    frames = []
    NB_ETAPES = 28  # plus d'images qu'avant, pour un mouvement plus fluide

    for etape in range(NB_ETAPES):
        progression = etape / (NB_ETAPES - 1)
        progression_douce = ease_out_cubic(progression)

        # Zoom Ken Burns continu sur le fond, léger, tout au long de l'animation —
        # rend une photo statique vivante, technique classique du motion design
        facteur_zoom = 1.0 + 0.06 * progression_douce
        w_zoom, h_zoom = int(largeur * facteur_zoom), int(hauteur * facteur_zoom)
        fond_zoome = fond_base.resize((w_zoom, h_zoom))
        gauche_z = (w_zoom - largeur) // 2
        haut_z = (h_zoom - hauteur) // 2
        image = fond_zoome.crop((gauche_z, haut_z, gauche_z + largeur, haut_z + hauteur))
        dessin = ImageDraw.Draw(image)

        # Voile qui s'assombrit progressivement en bas
        opacite_voile = int(min(progression_douce * 2, 1) * 130)
        voile = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ImageDraw.Draw(voile).rectangle([0, int(hauteur * 0.55), largeur, hauteur], fill=(0, 0, 0, opacite_voile))
        image = Image.alpha_composite(image, voile)
        dessin = ImageDraw.Draw(image)

        # Badge qui grossit puis se stabilise (apparaît vers le milieu de l'animation)
        if pourcentage and progression > 0.25:
            avancement_badge = ease_out_cubic(min((progression - 0.25) / 0.35, 1))
            rayon = int(largeur * 0.11 * avancement_badge)
            if rayon > 2:
                cx, cy = largeur - marge - int(largeur * 0.11), marge + int(largeur * 0.11)
                dessin.ellipse([cx - rayon, cy - rayon, cx + rayon, cy + rayon], fill=(0xE8, 0x3D, 0x3D, 255))
                if avancement_badge > 0.6:
                    police_badge = trouver_police_grasse(int(largeur * 0.11 * 0.55))
                    bbox_b = dessin.textbbox((0, 0), pourcentage, font=police_badge)
                    lb, hb = bbox_b[2] - bbox_b[0], bbox_b[3] - bbox_b[1]
                    dessin.text((cx - lb / 2, cy - hb / 2 - bbox_b[1]), pourcentage, font=police_badge, fill="white")

        # Titre qui glisse depuis le bas (apparaît après le badge)
        if progression > 0.45:
            avancement_titre = ease_out_cubic(min((progression - 0.45) / 0.35, 1))
            decalage = int((1 - avancement_titre) * 40)
            dessin.multiline_text((marge + 2, y_titre + decalage + 2), texte_titre, font=police_titre, fill=(0, 0, 0, 160), spacing=10)
            dessin.multiline_text((marge, y_titre + decalage), texte_titre, font=police_titre, fill="white", spacing=10)

        # Bouton qui apparaît en dernier — sauf sur bannière, trop bas pour l'accueillir sans chevauchement
        if progression > 0.75 and format_cle != "banniere":
            hauteur_bouton = int(hauteur * 0.07)
            y_bouton = hauteur - marge - hauteur_bouton
            dessin.rounded_rectangle(
                [marge, y_bouton, marge + int(largeur * 0.4), y_bouton + hauteur_bouton],
                radius=hauteur_bouton // 2, fill=couleur_bouton
            )
            police_bouton = trouver_police_grasse(int(hauteur_bouton * 0.4))
            texte_bouton = "En profiter »"
            bbox_btn = dessin.textbbox((0, 0), texte_bouton, font=police_bouton)
            lbtn = bbox_btn[2] - bbox_btn[0]
            dessin.text(
                (marge + (int(largeur * 0.4) - lbtn) / 2, y_bouton + (hauteur_bouton - (bbox_btn[3] - bbox_btn[1])) / 2 - bbox_btn[1]),
                texte_bouton, font=police_bouton, fill="white"
            )

        frames.append(image.convert("RGB"))

    # La dernière image reste affichée 1.5s de plus avant de reboucler
    frames_finales = frames + [frames[-1]] * 8

    # Écrit chaque image dans un dossier temporaire, puis les encode en
    # un vrai MP4 via ffmpeg — un GIF est limité à 256 couleurs, ce qui
    # donne un rendu délavé et des bandes visibles sur une vraie photo ;
    # un MP4 n'a pas cette limite.
    dossier_temp = tempfile.mkdtemp(prefix="stanislas_video_")
    try:
        for i, frame in enumerate(frames_finales):
            frame.save(os.path.join(dossier_temp, f"frame_{i:04d}.png"))

        fps = 1000 / 65  # même cadence que l'ancien GIF (65ms par image)
        resultat = subprocess.run(
            [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", os.path.join(dossier_temp, "frame_%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # dimensions paires, requises par certains lecteurs
                chemin_sortie,
            ],
            capture_output=True, text=True,
        )
        if resultat.returncode != 0:
            raise RuntimeError(f"ffmpeg a échoué : {resultat.stderr[-500:]}")
    finally:
        shutil.rmtree(dossier_temp, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--generer-fond-ia":
        description = sys.argv[2]
        format_cle = sys.argv[3] if len(sys.argv) > 3 else "post"

        dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Vidéo"))
        os.makedirs(dossier, exist_ok=True)
        chemin_fond = os.path.join(dossier, ".fond_ia_temp.png")

        from promo_image_ia import generer_fond
        generer_fond(description, format_cle, chemin_fond)

        import base64
        with open(chemin_fond, "rb") as f:
            contenu_base64 = base64.b64encode(f.read()).decode("ascii")
        print("---FOND_BASE64---", flush=True)
        print(contenu_base64)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--finaliser":
        dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Vidéo"))
        chemin_temp = os.path.join(dossier, ".apercu_video_temp.mp4")
        if not os.path.exists(chemin_temp):
            print("[ERREUR] Aucun aperçu vidéo à sauvegarder.")
            sys.exit(1)

        from datetime import datetime
        import shutil
        import platform
        import subprocess

        horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
        chemin_final = os.path.join(dossier, f"animation_{horodatage}.mp4")
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

    if len(sys.argv) < 2:
        print("[ERREUR] Aucun texte fourni.")
        sys.exit(1)

    texte = sys.argv[1]
    format_cle = sys.argv[2] if len(sys.argv) > 2 else "post"
    chemin_image_fond = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None

    if chemin_image_fond == "IA":
        dossier_video = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Vidéo"))
        chemin_image_fond = os.path.join(dossier_video, ".fond_ia_temp.png")
        if not os.path.exists(chemin_image_fond):
            print("[ERREUR] Le fond généré par IA est introuvable — génère-le d'abord.")
            sys.exit(1)

    dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Vidéo"))
    os.makedirs(dossier, exist_ok=True)
    chemin_temp = os.path.join(dossier, ".apercu_video_temp.mp4")

    print("Construction de l'animation...", flush=True)
    creer_animation(texte, format_cle, chemin_image_fond, chemin_temp)
    print("Animation créée.", flush=True)

    import base64
    with open(chemin_temp, "rb") as f:
        contenu_base64 = base64.b64encode(f.read()).decode("ascii")

    print("---VIDEO_BASE64---", flush=True)
    print(contenu_base64)
