"""
Assemble une vidéo à partir des clips que l'utilisateur possède DÉJÀ sur sa
machine — aucune vidéo n'est téléchargée depuis Internet (contrairement à
des outils comme MoneyPrinterTurbo qui piochent des vidéos stock sur
Pexels). Seule la voix off est générée, localement, avec la voix système.

Étapes, toutes locales :
  1. Voix off : voix système macOS (`say`) ou Windows (SAPI), à partir du
     texte fourni.
  2. Sous-titres : découpage du texte en phrases, réparties sur la durée de
     la voix off au prorata du nombre de caractères (approximation simple,
     pas d'alignement forcé — donc le calage n'est pas seconde près).
  3. Montage : chaque clip fourni par l'utilisateur est mis à l'échelle,
     rogné/bouclé pour occuper une portion égale de la durée totale, puis
     concaténé, avec les sous-titres incrustés et la voix off en piste
     audio.

Dépendance requise :
    ffmpeg. En développement, celui installé sur ta machine (brew install
    ffmpeg) suffit. Pour l'app finale livrée aux utilisateurs, un binaire
    ffmpeg statique doit être embarqué dans le paquet Tauri (voir le
    dossier src-tauri/binaries/) — sinon la fonction plante chez toute
    personne qui n'a pas ffmpeg installé. Ce script sait utiliser le
    binaire embarqué automatiquement s'il est fourni (variable
    d'environnement STANISLAS_FFMPEG_DIR, positionnée côté JS), et retombe
    sur le PATH système sinon (donc rien ne casse en développement).

Usage :
    python3 montage_video_cli.py <texte_voix_off> <clip1> [clip2] [clip3...]

Sortie : des lignes de progression, puis ---RESULTAT--- suivi d'un message
de confirmation avec le chemin du fichier final.
"""
import sys
import os

# Si l'app a embarqué son propre binaire ffmpeg (cas de l'app finale
# distribuée aux utilisateurs), on le fait passer en priorité sur le PATH
# système — sans ça, rien ne fonctionne chez quelqu'un qui n'a pas
# installé ffmpeg lui-même.
_dossier_ffmpeg_embarque = os.environ.get("STANISLAS_FFMPEG_DIR")
if _dossier_ffmpeg_embarque:
    os.environ["PATH"] = _dossier_ffmpeg_embarque + os.pathsep + os.environ.get("PATH", "")
import re
import json
import subprocess
import tempfile
import shutil
import platform
from datetime import datetime, timedelta

TAILLE_SORTIE = (1280, 720)  # largeur, hauteur — format horizontal standard
VOIX_DISPONIBLES = {
    "stanislas": "Thomas",
    "homme": "Jacques",
    "femme": "Amélie",
    "homme_en": "Fred",
    "femme_en": "Samantha",
}
CHOIX_VOIX_PAR_DEFAUT = "stanislas"


def nom_voix_mac() -> str:
    choix = os.environ.get("STANISLAS_VOIX_CHOIX", CHOIX_VOIX_PAR_DEFAUT)
    return VOIX_DISPONIBLES.get(choix, VOIX_DISPONIBLES[CHOIX_VOIX_PAR_DEFAUT])


def genre_voix_windows() -> str:
    """Même logique que dans voix_stanislas.py : sur Windows, un nom de
    voix précis (Amélie, Jacques...) n'existe presque jamais par défaut.
    On demande juste un genre à SAPI, qui pioche parmi ce qui est déjà
    installé sur la machine."""
    choix = os.environ.get("STANISLAS_VOIX_CHOIX", CHOIX_VOIX_PAR_DEFAUT)
    return "Female" if choix in ("femme", "femme_en") else "Male"


def verifier_ffmpeg():
    for outil in ("ffmpeg", "ffprobe"):
        if shutil.which(outil) is None:
            print(f"[ERREUR] '{outil}' est introuvable. Installe-le (ex: brew install ffmpeg sur Mac) puis relance.")
            sys.exit(1)


def decouper_phrases(texte: str):
    phrases = re.split(r'(?<=[.!?])\s+', texte.strip())
    return [p.strip() for p in phrases if p.strip()]


def generer_voix_off(texte: str, dossier_temp: str) -> str:
    """Génère le fichier audio de la voix off, renvoie son chemin (.wav)."""
    chemin_wav = os.path.join(dossier_temp, "voix_off.wav")
    systeme = platform.system()

    print("Génération de la voix off...")
    if systeme == "Darwin":
        chemin_aiff = os.path.join(dossier_temp, "voix_off.aiff")
        subprocess.run(["say", "-v", nom_voix_mac(), "-o", chemin_aiff, texte], check=True)
        subprocess.run(
            ["ffmpeg", "-y", "-i", chemin_aiff, chemin_wav],
            check=True, capture_output=True,
        )
    elif systeme == "Windows":
        texte_echappe = texte.replace("'", "")
        genre = genre_voix_windows()
        commande_ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"try {{ $s.SelectVoiceByHints('{genre}') }} catch {{}}; "
            f"$s.SetOutputToWaveFile('{chemin_wav}'); "
            f"$s.Speak('{texte_echappe}'); "
            "$s.Dispose()"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", commande_ps], check=True)
    else:
        raise RuntimeError("Génération de voix off non prise en charge sur ce système (Linux).")

    return chemin_wav


def duree_fichier(chemin: str) -> float:
    resultat = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", chemin],
        check=True, capture_output=True, text=True,
    )
    return float(json.loads(resultat.stdout)["format"]["duration"])


def formater_timestamp_ass(secondes: float) -> str:
    td = timedelta(seconds=max(0, secondes))
    total_cs = int(td.total_seconds() * 100)  # centièmes de seconde
    h, reste = divmod(total_cs, 360_000)
    m, reste = divmod(reste, 6_000)
    s, cs = divmod(reste, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generer_ass(phrases, duree_totale: float, dossier_temp: str) -> str:
    """Génère un fichier de sous-titres .ass avec le style (police, taille,
    couleurs) directement défini DANS le fichier, plutôt que passé en
    paramètre 'force_style' dans la commande ffmpeg. C'est plus robuste :
    une valeur de style avec des virgules imbriquées dans des guillemets à
    l'intérieur d'un filtergraph ffmpeg est notoirement fragile et casse
    différemment selon la version d'ffmpeg installée (vécu en pratique).
    Un fichier .ass autoporteur élimine complètement ce risque."""
    chemin_ass = os.path.join(dossier_temp, "sous_titres.ass")
    total_caracteres = sum(len(p) for p in phrases) or 1

    entete = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,42,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,0,2,20,20,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    with open(chemin_ass, "w", encoding="utf-8") as f:
        f.write(entete)
        t = 0.0
        for phrase in phrases:
            part = len(phrase) / total_caracteres
            duree_phrase = duree_totale * part
            debut, fin = t, t + duree_phrase
            texte_ass = phrase.replace("\n", " ")
            f.write(f"Dialogue: 0,{formater_timestamp_ass(debut)},{formater_timestamp_ass(fin)},Default,,0,0,0,,{texte_ass}\n")
            t = fin

    return chemin_ass


EXTENSIONS_IMAGE = (".jpg", ".jpeg", ".png", ".heic", ".webp", ".bmp", ".tiff", ".gif")


def est_image(chemin: str) -> bool:
    return os.path.splitext(chemin)[1].lower() in EXTENSIONS_IMAGE


def assembler(texte: str, clips: list, dossier_sortie: str) -> str:
    verifier_ffmpeg()

    for clip in clips:
        if not os.path.exists(clip):
            print(f"[ERREUR] Fichier introuvable : {clip}")
            sys.exit(1)

    with tempfile.TemporaryDirectory() as dossier_temp:
        chemin_voix = generer_voix_off(texte, dossier_temp)
        duree_totale = duree_fichier(chemin_voix)
        print(f"Durée de la voix off : {duree_totale:.1f}s")

        phrases = decouper_phrases(texte) or [texte]
        chemin_ass = generer_ass(phrases, duree_totale, dossier_temp)

        duree_par_clip = duree_totale / len(clips)
        largeur, hauteur = TAILLE_SORTIE

        print("Préparation des clips (mise à l'échelle, zoom pour les photos)...")
        entrees = []
        filtres = []
        for i, clip in enumerate(clips):
            fps = 25
            nb_images = max(1, round(duree_par_clip * fps))

            if est_image(clip):
                # Photo fixe : une entrée en boucle sur une image ne
                # bouge jamais toute seule — on ajoute un vrai effet de
                # zoom lent (façon "Ken Burns"), sinon la photo reste
                # complètement figée pendant toute sa durée à l'écran.
                # Alterne zoom avant / zoom arrière d'un clip à l'autre,
                # pour ne pas avoir le même mouvement partout.
                entrees += ["-loop", "1", "-t", f"{duree_par_clip:.3f}", "-i", clip]
                zoom_avant = (i % 2 == 0)
                if zoom_avant:
                    expr_zoom = f"min(zoom+0.0015,1.4)"
                else:
                    expr_zoom = f"if(eq(on,1),1.4,max(zoom-0.0015,1.0))"
                # On part d'une image sur-échantillonnée (8000px de large)
                # pour que le zoom reste net, pas pixelisé
                filtres.append(
                    f"[{i}:v]scale=8000:-2,"
                    f"zoompan=z='{expr_zoom}':d={nb_images}:s={largeur}x{hauteur}:fps={fps},"
                    f"setsar=1[v{i}]"
                )
            else:
                # Vrai clip vidéo : a déjà son propre mouvement, pas
                # besoin d'effet ajouté — juste mise à l'échelle
                entrees += ["-stream_loop", "-1", "-t", f"{duree_par_clip:.3f}", "-i", clip]
                filtres.append(
                    f"[{i}:v]scale={largeur}:{hauteur}:force_original_aspect_ratio=decrease,"
                    f"pad={largeur}:{hauteur}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}[v{i}]"
                )

        concat_inputs = "".join(f"[v{i}]" for i in range(len(clips)))
        filtre_concat = f"{concat_inputs}concat=n={len(clips)}:v=1:a=0[vconcat]"
        # On référence le fichier de sous-titres par son seul nom (pas son
        # chemin complet) et on exécute ffmpeg avec ce dossier temporaire
        # comme répertoire de travail (cwd) juste en dessous. Sinon, le
        # chemin complet macOS (/var/folders/.../T/...) fait planter
        # l'analyseur de filtres d'ffmpeg 8.x avec "No option name" / "Error
        # parsing filterchain" — un chemin long injecté tel quel dans la
        # syntaxe des filtres est fragile et dépend trop de la version
        # d'ffmpeg installée ; un nom de fichier tout simple ne pose jamais
        # ce problème, quelle que soit la plateforme.
        # Le style (police, taille, couleurs) est déjà défini DANS le
        # fichier .ass lui-même (voir generer_ass) — donc plus besoin de
        # passer un 'force_style' fragile ici, juste le nom du fichier.
        nom_ass = os.path.basename(chemin_ass)
        # 'filename=' explicite plutôt que le raccourci positionnel : plus
        # sûr, ne dépend pas de la façon dont chaque version d'ffmpeg gère
        # (ou pas) la syntaxe raccourcie du filtre subtitles.
        filtre_sous_titres = f"[vconcat]subtitles=filename={nom_ass}[vout]"
        filter_complex = ";".join(filtres) + ";" + filtre_concat + ";" + filtre_sous_titres

        index_audio = len(clips)  # la voix off est ajoutée comme dernière entrée
        entrees += ["-i", chemin_voix]

        os.makedirs(dossier_sortie, exist_ok=True)
        nom_fichier = f"montage_{datetime.now().strftime('%Y-%m-%d_%Hh%M')}.mp4"
        chemin_final = os.path.join(dossier_sortie, nom_fichier)

        commande = [
            "ffmpeg", "-y",
            *entrees,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", f"{index_audio}:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            chemin_final,
        ]

        print("Montage final en cours (ffmpeg)...")
        # cwd=dossier_temp : c'est ce qui permet au nom de fichier "nu" du
        # filtre subtitles ci-dessus d'être retrouvé sans ambiguïté. Les
        # autres chemins (clips, voix, sortie) restent absolus donc ne
        # sont pas affectés par ce changement de répertoire de travail.
        resultat = subprocess.run(commande, capture_output=True, text=True, cwd=dossier_temp)
        if resultat.returncode != 0:
            print("[ERREUR ffmpeg]")
            print(resultat.stderr[-2000:])  # dernières lignes utiles pour diagnostiquer
            sys.exit(1)

        return chemin_final


def dossier_donnees_app() -> str:
    """Renvoie le dossier où Stanislas doit écrire ses fichiers générés —
    JAMAIS à l'intérieur du dossier de l'app elle-même. Deux raisons :
    1) en développement, Tauri surveille src-tauri/ pour détecter des
       changements de code, et confond les fichiers générés (vidéos...)
       avec du code à recompiler, provoquant des redémarrages en boucle ;
    2) une fois l'app compilée et signée pour de vrai, son dossier devient
       en lecture seule — impossible d'y écrire quoi que ce soit.
    On utilise "Documents" plutôt que le dossier système habituel des
    applications (~/Library/Application Support/...) : ce dernier est
    délibérément caché par macOS, un utilisateur non-technique n'ira
    jamais y chercher ses vidéos. "Documents" est un endroit que tout le
    monde connaît et sait retrouver dans le Finder."""
    systeme = platform.system()
    if systeme == "Darwin":
        base = os.path.expanduser("~/Documents/Stanislas")
    elif systeme == "Windows":
        base = os.path.join(os.path.expanduser("~"), "Documents", "Stanislas")
    else:
        base = os.path.expanduser("~/Documents/Stanislas")
    return base


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("[ERREUR] Usage : montage_video_cli.py <texte> <clip1> [clip2...]")
        sys.exit(1)

    texte_voix_off = sys.argv[1]
    clips = sys.argv[2:]

    dossier_sortie = os.path.join(dossier_donnees_app(), "Archives", "Montage")

    chemin_final = assembler(texte_voix_off, clips, dossier_sortie)

    print("---RESULTAT---")
    print(f"Vidéo assemblée avec succès : {chemin_final}\n({len(clips)} clip(s) utilisé(s), aucun téléchargement.)")
