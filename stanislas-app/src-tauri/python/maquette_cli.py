"""
Génère une vraie image PNG de la maquette (texte posé sur un cadre aux
dimensions du format choisi), et l'ouvre pour que l'utilisateur puisse
la voir, l'enregistrer ailleurs, l'imprimer ou la joindre à un email.

Ce n'est PAS encore une image générée par IA (Flux) — juste une mise en
page propre du texte, en attendant que le générateur d'image soit relié.

Nécessite Pillow (normalement déjà installé pour Atelier image) :
    pip3 install Pillow --break-system-packages
"""
import sys
import os
import platform
import subprocess
import textwrap
from datetime import datetime

DIMENSIONS = {
    "post": (1080, 1080),
    "story": (1080, 1920),
    "banniere": (1200, 300),
    "ads": (1080, 1080),
    "print": (1240, 1748),  # A4 environ, à 150 dpi
}


def trouver_police(taille: int):
    """Police embarquée dans l'app (Poppins Regular) — même mécanisme que
    ffmpeg/Ollama, indépendant de ce qui est installé sur la machine.
    Retombe sur une police système si jamais le dossier embarqué manque
    (mode développement avant packaging)."""
    from PIL import ImageFont

    dossier_polices = os.environ.get("STANISLAS_POLICES_DIR")
    if dossier_polices:
        chemin = os.path.join(dossier_polices, "Poppins-Regular.ttf")
        if os.path.exists(chemin):
            return ImageFont.truetype(chemin, taille)

    chemins_repli = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for chemin in chemins_repli:
        if os.path.exists(chemin):
            try:
                return ImageFont.truetype(chemin, taille)
            except Exception:
                continue
    return ImageFont.load_default(size=taille)


def trouver_police_grasse(taille: int):
    """Version en gras de la police, pour le style Impact."""
    from PIL import ImageFont
    dossier_polices = os.environ.get("STANISLAS_POLICES_DIR")
    if dossier_polices:
        chemin = os.path.join(dossier_polices, "Poppins-Bold.ttf")
        if os.path.exists(chemin):
            return ImageFont.truetype(chemin, taille)

    chemins_possibles = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for chemin in chemins_possibles:
        if os.path.exists(chemin):
            try:
                return ImageFont.truetype(chemin, taille)
            except Exception:
                continue
    return trouver_police(taille)


def trouver_police_elegante(taille: int, gras: bool = False):
    """Playfair Display — police serif élégante embarquée, pour le style
    "Élégant". Police variable : on choisit le bon réglage de graisse
    directement dedans plutôt que d'avoir besoin d'un fichier séparé."""
    from PIL import ImageFont

    dossier_polices = os.environ.get("STANISLAS_POLICES_DIR")
    if dossier_polices:
        chemin = os.path.join(dossier_polices, "PlayfairDisplay-Variable.ttf")
        if os.path.exists(chemin):
            police = ImageFont.truetype(chemin, taille)
            try:
                police.set_variation_by_name("Bold" if gras else "Regular")
            except Exception:
                pass
            return police

    return trouver_police_grasse(taille) if gras else trouver_police(taille)


def trouver_police_moderne(taille: int):
    """Space Grotesk — police géométrique et technique embarquée, pour le
    style "Moderne". Volontairement différente de Poppins (style Pro) et
    de Playfair Display (style Élégant), pour que les 3 styles aient
    chacun leur vraie identité visuelle plutôt que de se ressembler."""
    from PIL import ImageFont

    dossier_polices = os.environ.get("STANISLAS_POLICES_DIR")
    if dossier_polices:
        chemin = os.path.join(dossier_polices, "SpaceGrotesk-Variable.ttf")
        if os.path.exists(chemin):
            police = ImageFont.truetype(chemin, taille)
            try:
                police.set_variation_by_name("Bold")
            except Exception:
                pass
            return police

    return trouver_police_grasse(taille)


import re


def detecter_pourcentage(texte: str):
    """Cherche un pourcentage ou un chiffre marquant dans le texte, pour le
    mettre en avant dans un badge — comme le fait une vraie pub."""
    m = re.search(r"(\d{1,3})\s?%", texte)
    if m:
        return m.group(1) + "%"
    m = re.search(r"(\d{1,4})\s?(€|\$|EUR)", texte)
    if m:
        return m.group(1) + m.group(2)
    return None


def creer_image_pro(texte: str, format_cle: str, chemin_sortie: str, chemin_image_fond: str = None):
    """Un vrai gabarit publicitaire : badge de réduction, gros titre avec
    ombre, bouton d'appel à l'action — plutôt qu'un simple bloc de texte."""
    from PIL import Image, ImageDraw

    largeur, hauteur = DIMENSIONS.get(format_cle, DIMENSIONS["post"])

    if chemin_image_fond and os.path.exists(chemin_image_fond):
        fond = Image.open(chemin_image_fond).convert("RGB")
        ratio_cible = largeur / hauteur
        ratio_fond = fond.width / fond.height
        if ratio_fond > ratio_cible:
            nh = hauteur
            nl = int(hauteur * ratio_fond)
        else:
            nl = largeur
            nh = int(largeur / ratio_fond)
        fond = fond.resize((nl, nh))
        gauche = (nl - largeur) // 2
        haut = (nh - hauteur) // 2
        image = fond.crop((gauche, haut, gauche + largeur, haut + hauteur))
    else:
        image = Image.new("RGB", (largeur, hauteur), "#3a5a40")

    image = image.convert("RGBA")

    # Léger voile sombre en bas pour que le titre reste toujours lisible,
    # quelle que soit la photo derrière
    voile = Image.new("RGBA", image.size, (0, 0, 0, 0))
    dessin_voile = ImageDraw.Draw(voile)
    dessin_voile.rectangle([0, int(hauteur * 0.55), largeur, hauteur], fill=(0, 0, 0, 130))
    image = Image.alpha_composite(image, voile)
    dessin = ImageDraw.Draw(image)

    marge = int(largeur * 0.06)
    r_accent, g_accent, b_accent = extraire_couleur_accent(image.convert("RGB"), 0, int(largeur * 0.2))
    couleur_accent = (min(r_accent + 60, 255), min(g_accent + 30, 255), min(b_accent + 10, 255))

    # Badge de réduction en haut, façon "pastille" — si un pourcentage est détecté
    pourcentage = detecter_pourcentage(texte)
    if pourcentage:
        rayon = int(largeur * 0.11)
        cx, cy = largeur - marge - rayon, marge + rayon
        dessin.ellipse([cx - rayon, cy - rayon, cx + rayon, cy + rayon], fill=(0xE8, 0x3D, 0x3D, 255))
        police_badge = trouver_police_grasse(int(rayon * 0.55))
        bbox_b = dessin.textbbox((0, 0), pourcentage, font=police_badge)
        lb = bbox_b[2] - bbox_b[0]
        hb = bbox_b[3] - bbox_b[1]
        dessin.text((cx - lb / 2, cy - hb / 2 - bbox_b[1]), pourcentage, font=police_badge, fill="white")

    if format_cle == "banniere":
        # Format très bas : titre centré verticalement, pas de bouton séparé
        # (le chevauchement titre/bouton vient d'ici sur les formats hauts)
        police_titre = trouver_police_grasse(max(20, int(hauteur * 0.22)))
        largeur_car_titre = int((largeur - 2 * marge) / (hauteur * 0.22 * 0.55))
        lignes_titre = textwrap.wrap(texte, width=max(largeur_car_titre, 10))[:2]
        texte_titre = "\n".join(lignes_titre)

        bbox_t = dessin.multiline_textbbox((0, 0), texte_titre, font=police_titre, spacing=6)
        hauteur_texte = bbox_t[3] - bbox_t[1]
        y_titre = (hauteur - hauteur_texte) / 2

        dessin.multiline_text((marge + 2, y_titre + 2), texte_titre, font=police_titre, fill=(0, 0, 0, 160), spacing=6, align="center")
        dessin.multiline_text((marge, y_titre), texte_titre, font=police_titre, fill="white", spacing=6, align="center")
    else:
        # Titre principal, gros et gras, avec une légère ombre pour le détacher du fond
        police_titre = trouver_police_grasse(max(28, int(largeur * 0.055)))
        largeur_car_titre = int((largeur - 2 * marge) / (largeur * 0.055 * 0.55))
        lignes_titre = textwrap.wrap(texte, width=max(largeur_car_titre, 8))[:3]
        texte_titre = "\n".join(lignes_titre)

        y_titre = int(hauteur * 0.62)
        dessin.multiline_text((marge + 2, y_titre + 2), texte_titre, font=police_titre, fill=(0, 0, 0, 160), spacing=10)
        dessin.multiline_text((marge, y_titre), texte_titre, font=police_titre, fill="white", spacing=10)

        # Bouton d'appel à l'action, en bas — seulement sur les formats assez hauts
        hauteur_bouton = int(hauteur * 0.07)
        y_bouton = hauteur - marge - hauteur_bouton
        dessin.rounded_rectangle(
            [marge, y_bouton, marge + int(largeur * 0.4), y_bouton + hauteur_bouton],
            radius=hauteur_bouton // 2, fill=couleur_accent
        )
        police_bouton = trouver_police_grasse(int(hauteur_bouton * 0.4))
        texte_bouton = "En profiter »"
        bbox_btn = dessin.textbbox((0, 0), texte_bouton, font=police_bouton)
        lbtn = bbox_btn[2] - bbox_btn[0]
        dessin.text(
            (marge + (int(largeur * 0.4) - lbtn) / 2, y_bouton + (hauteur_bouton - (bbox_btn[3] - bbox_btn[1])) / 2 - bbox_btn[1]),
            texte_bouton, font=police_bouton, fill="white"
        )

    image.convert("RGB").save(chemin_sortie)


def extraire_couleur_accent(image, y_zone: int, hauteur_zone: int):
    """Pioche une couleur d'accent dans la zone où le texte sera posé,
    pour que le bandeau ait une couleur assortie à l'image plutôt qu'un
    noir générique — un petit réflexe de designer, sans réécrire tout
    le moteur de rendu."""
    zone = image.crop((0, y_zone, image.width, y_zone + hauteur_zone)).convert("RGB")
    zone_reduite = zone.resize((1, 1))
    r, g, b = zone_reduite.getpixel((0, 0))
    # On assombrit la couleur piochée pour garder un bon contraste avec le texte blanc
    facteur = 0.45
    return (int(r * facteur), int(g * facteur), int(b * facteur))


def creer_image(texte: str, format_cle: str, chemin_sortie: str, chemin_image_fond: str = None, style: str = "classique"):
    if style == "pro":
        return creer_image_pro(texte, format_cle, chemin_sortie, chemin_image_fond)

    from PIL import Image, ImageDraw

    largeur, hauteur = DIMENSIONS.get(format_cle, DIMENSIONS["post"])

    if chemin_image_fond and os.path.exists(chemin_image_fond):
        # Une vraie image a été choisie : on la recadre pour remplir le cadre
        # (mode "cover" — remplit tout l'espace, quitte à rogner les bords)
        fond = Image.open(chemin_image_fond).convert("RGB")
        ratio_cible = largeur / hauteur
        ratio_fond = fond.width / fond.height
        if ratio_fond > ratio_cible:
            nouvelle_hauteur = hauteur
            nouvelle_largeur = int(hauteur * ratio_fond)
        else:
            nouvelle_largeur = largeur
            nouvelle_hauteur = int(largeur / ratio_fond)
        fond = fond.resize((nouvelle_largeur, nouvelle_hauteur))
        gauche = (nouvelle_largeur - largeur) // 2
        haut = (nouvelle_hauteur - hauteur) // 2
        image = fond.crop((gauche, haut, gauche + largeur, haut + hauteur))
    else:
        # Pas d'image choisie : on garde le motif rayé "emplacement à venir"
        image = Image.new("RGB", (largeur, hauteur), "#e8e8e0")
        dessin_fond = ImageDraw.Draw(image)
        pas = 24
        for x in range(-hauteur, largeur, pas):
            dessin_fond.line([(x, 0), (x + hauteur, hauteur)], fill="#f4f4ee", width=8)

    image = image.convert("RGBA")

    marge = int(largeur * 0.06)
    taille_police = max(20, largeur // 30)
    if style == "elegant":
        police = trouver_police_elegante(taille_police, gras=True)
    elif style == "moderne":
        police = trouver_police_moderne(taille_police)
    else:
        police = trouver_police(taille_police)

    largeur_car = int((largeur - 2 * marge) / (taille_police * 0.6))
    lignes = textwrap.wrap(texte, width=max(largeur_car, 10))
    texte_multiligne = "\n".join(lignes)

    dessin_mesure = ImageDraw.Draw(image)
    bbox = dessin_mesure.multiline_textbbox((0, 0), texte_multiligne, font=police, spacing=10)
    hauteur_texte = bbox[3] - bbox[1]
    hauteur_boite = hauteur_texte + marge

    if format_cle == "print":
        y_boite = marge
    else:
        y_boite = hauteur - hauteur_boite - marge

    if style == "moderne":
        # Bandeau semi-transparent teinté avec une couleur piochée dans l'image,
        # plutôt qu'un noir générique — donne un rendu plus assorti et soigné
        r, g, b = extraire_couleur_accent(image, int(y_boite - marge / 2), int(hauteur_boite + marge))
        calque = Image.new("RGBA", image.size, (0, 0, 0, 0))
        dessin_calque = ImageDraw.Draw(calque)
        dessin_calque.rectangle(
            [0, y_boite - marge / 2, largeur, y_boite + hauteur_boite + marge / 2],
            fill=(r, g, b, 190)
        )
        image = Image.alpha_composite(image, calque)
        dessin = ImageDraw.Draw(image)
        dessin.multiline_text(
            (marge * 1.5, y_boite + marge / 2), texte_multiligne,
            font=police, fill="white", spacing=10
        )
    else:
        # Élégant : dégradé sombre doux en bas (pas de boîte dure), titre
        # serif blanc, fine ligne dorée au-dessus — esprit couverture de
        # magazine plutôt que bloc publicitaire
        calque = Image.new("RGBA", image.size, (0, 0, 0, 0))
        dessin_calque = ImageDraw.Draw(calque)
        haut_degrade = max(0, int(y_boite - marge * 1.5))
        for y in range(haut_degrade, hauteur):
            progression = (y - haut_degrade) / max(1, hauteur - haut_degrade)
            alpha = int(175 * progression)
            dessin_calque.line([(0, y), (largeur, y)], fill=(10, 10, 10, alpha))
        image = Image.alpha_composite(image, calque)
        dessin = ImageDraw.Draw(image)

        ligne_y = y_boite - marge * 0.6
        dessin.line([(marge * 1.5, ligne_y), (marge * 1.5 + largeur * 0.14, ligne_y)], fill=(214, 178, 122, 255), width=3)
        dessin.multiline_text(
            (marge * 1.5, y_boite + marge / 2), texte_multiligne,
            font=police, fill="white", spacing=14
        )

    image.convert("RGB").save(chemin_sortie)



def ajouter_diapo_style(prs, largeur_diapo, hauteur_diapo, texte: str, format_cle: str, chemin_image_fond: str, style: str):
    """Ajoute UNE diapo (pour un style donné) dans une présentation déjà
    créée — permet de mettre plusieurs styles dans le même fichier."""
    from pptx.util import Emu, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    diapo = prs.slides.add_slide(prs.slide_layouts[6])

    if chemin_image_fond and os.path.exists(chemin_image_fond):
        diapo.shapes.add_picture(chemin_image_fond, 0, 0, width=largeur_diapo, height=hauteur_diapo)
    else:
        forme = diapo.shapes.add_shape(1, 0, 0, largeur_diapo, hauteur_diapo)
        forme.fill.solid()
        forme.fill.fore_color.rgb = RGBColor(0xE8, 0xE8, 0xE0)
        forme.line.fill.background()

    hauteur_bloc = Emu(int(hauteur_diapo * 0.22))
    if format_cle == "print":
        y_bloc = Emu(int(hauteur_diapo * 0.04))
    else:
        y_bloc = hauteur_diapo - hauteur_bloc - Emu(int(hauteur_diapo * 0.04))

    if style == "pro":
        pourcentage = detecter_pourcentage(texte)
        if pourcentage:
            rayon = Emu(int(largeur_diapo * 0.09))
            cx = largeur_diapo - Emu(int(largeur_diapo * 0.05)) - rayon
            cy = Emu(int(largeur_diapo * 0.05)) + rayon
            badge = diapo.shapes.add_shape(9, cx - rayon, cy - rayon, rayon * 2, rayon * 2)
            badge.fill.solid()
            badge.fill.fore_color.rgb = RGBColor(0xE8, 0x3D, 0x3D)
            badge.line.fill.background()
            cadre_badge = badge.text_frame
            cadre_badge.paragraphs[0].text = pourcentage
            cadre_badge.paragraphs[0].font.size = Pt(28)
            cadre_badge.paragraphs[0].font.bold = True
            cadre_badge.paragraphs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            cadre_badge.paragraphs[0].alignment = PP_ALIGN.CENTER

        voile = diapo.shapes.add_shape(1, 0, Emu(int(hauteur_diapo * 0.55)), largeur_diapo, hauteur_diapo - Emu(int(hauteur_diapo * 0.55)))
        voile.fill.solid()
        voile.fill.fore_color.rgb = RGBColor(0x00, 0x00, 0x00)
        voile.fill.transparency = 0.5
        voile.line.fill.background()
        couleur_texte = RGBColor(0xFF, 0xFF, 0xFF)

        hauteur_bouton = Emu(int(hauteur_diapo * 0.08))
        y_bouton = hauteur_diapo - Emu(int(largeur_diapo * 0.05)) - hauteur_bouton
        bouton = diapo.shapes.add_shape(5, Emu(int(largeur_diapo * 0.05)), y_bouton,
                                         Emu(int(largeur_diapo * 0.35)), hauteur_bouton)
        bouton.fill.solid()
        bouton.fill.fore_color.rgb = RGBColor(0xE0, 0x7A, 0x3D)
        bouton.line.fill.background()
        cadre_bouton = bouton.text_frame
        cadre_bouton.paragraphs[0].text = "En profiter »"
        cadre_bouton.paragraphs[0].font.size = Pt(14)
        cadre_bouton.paragraphs[0].font.bold = True
        cadre_bouton.paragraphs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        cadre_bouton.paragraphs[0].alignment = PP_ALIGN.CENTER

    elif style == "moderne":
        fond_bloc = diapo.shapes.add_shape(1, 0, y_bloc, largeur_diapo, hauteur_bloc)
        fond_bloc.fill.solid()
        fond_bloc.fill.fore_color.rgb = RGBColor(0x00, 0x00, 0x00)
        fond_bloc.fill.transparency = 0.35
        fond_bloc.line.fill.background()
        couleur_texte = RGBColor(0xFF, 0xFF, 0xFF)
    else:
        # Élégant : bloc sombre discret avec une fine ligne dorée au-dessus,
        # police serif — esprit couverture de magazine
        ligne_accent = diapo.shapes.add_shape(1, Emu(int(largeur_diapo * 0.05)), y_bloc - Emu(int(hauteur_diapo * 0.015)),
                                               Emu(int(largeur_diapo * 0.12)), Emu(int(hauteur_diapo * 0.005)))
        ligne_accent.fill.solid()
        ligne_accent.fill.fore_color.rgb = RGBColor(0xD6, 0xB2, 0x7A)
        ligne_accent.line.fill.background()

        fond_bloc = diapo.shapes.add_shape(1, 0, y_bloc, largeur_diapo, hauteur_bloc)
        fond_bloc.fill.solid()
        fond_bloc.fill.fore_color.rgb = RGBColor(0x0A, 0x0A, 0x0A)
        fond_bloc.fill.transparency = 0.25
        fond_bloc.line.fill.background()
        couleur_texte = RGBColor(0xFF, 0xFF, 0xFF)

    zone_texte = diapo.shapes.add_textbox(
        Emu(int(largeur_diapo * 0.07)), y_bloc,
        Emu(int(largeur_diapo * 0.86)), hauteur_bloc
    )
    cadre = zone_texte.text_frame
    cadre.word_wrap = True
    p = cadre.paragraphs[0]
    p.text = texte
    p.font.size = Pt(20 if format_cle != "banniere" else 16)
    p.font.color.rgb = couleur_texte
    p.font.bold = (style == "pro")
    if style == "elegant":
        p.font.name = "Playfair Display"
    elif style == "moderne":
        p.font.name = "Space Grotesk"
    else:
        p.font.name = "Poppins"
    p.alignment = PP_ALIGN.LEFT

    # Étiquette discrète en haut à gauche de chaque diapo, pour s'y
    # retrouver facilement quand plusieurs styles sont dans le même fichier
    etiquette = diapo.shapes.add_textbox(Emu(int(largeur_diapo * 0.02)), Emu(int(hauteur_diapo * 0.01)),
                                          Emu(int(largeur_diapo * 0.3)), Emu(int(hauteur_diapo * 0.05)))
    etiquette.text_frame.paragraphs[0].text = style.capitalize()
    etiquette.text_frame.paragraphs[0].font.size = Pt(10)
    etiquette.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x88, 0x88, 0x88)


def exporter_pptx(texte: str, format_cle: str, chemin_image_fond: str, style: str, chemin_sortie: str):
    """Exporte un fichier PowerPoint éditable avec UN SEUL style — garde
    la même fonction qu'avant pour ne rien casser ailleurs."""
    from pptx import Presentation
    from pptx.util import Emu

    largeur_px, hauteur_px = DIMENSIONS.get(format_cle, DIMENSIONS["post"])
    ratio = largeur_px / hauteur_px
    largeur_diapo = Emu(9144000)
    hauteur_diapo = Emu(int(largeur_diapo / ratio))

    prs = Presentation()
    prs.slide_width = largeur_diapo
    prs.slide_height = hauteur_diapo

    ajouter_diapo_style(prs, largeur_diapo, hauteur_diapo, texte, format_cle, chemin_image_fond, style)

    prs.save(chemin_sortie)


def exporter_pptx_tous_styles(texte: str, format_cle: str, chemin_image_fond: str, chemin_sortie: str):
    """Exporte un SEUL fichier PowerPoint contenant les 3 styles (une
    diapo par style), pour comparer et choisir directement dans PowerPoint
    plutôt que de choisir avant l'export."""
    from pptx import Presentation
    from pptx.util import Emu

    largeur_px, hauteur_px = DIMENSIONS.get(format_cle, DIMENSIONS["post"])
    ratio = largeur_px / hauteur_px
    largeur_diapo = Emu(9144000)
    hauteur_diapo = Emu(int(largeur_diapo / ratio))

    prs = Presentation()
    prs.slide_width = largeur_diapo
    prs.slide_height = hauteur_diapo

    for style in STYLES_DISPONIBLES:
        ajouter_diapo_style(prs, largeur_diapo, hauteur_diapo, texte, format_cle, chemin_image_fond, style)

    prs.save(chemin_sortie)


STYLES_DISPONIBLES = ["pro", "moderne", "elegant"]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--export-pptx-tous":
        texte = sys.argv[2]
        format_cle = sys.argv[3] if len(sys.argv) > 3 else "post"
        chemin_image_fond = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None

        if chemin_image_fond == "IA":
            dossier_promo = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Promo"))
            chemin_image_fond = os.path.join(dossier_promo, ".fond_ia_temp.png")
            if not os.path.exists(chemin_image_fond):
                print("[ERREUR] Le fond généré par IA est introuvable — régénère l'image d'abord.")
                sys.exit(1)

        dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Promo"))
        os.makedirs(dossier, exist_ok=True)
        horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
        chemin_sortie = os.path.join(dossier, f"promo_3styles_{horodatage}.pptx")

        exporter_pptx_tous_styles(texte, format_cle, chemin_image_fond, chemin_sortie)

        systeme = platform.system()
        try:
            if systeme == "Darwin":
                subprocess.run(["open", chemin_sortie], check=True)
            elif systeme == "Windows":
                os.startfile(chemin_sortie)
            else:
                subprocess.run(["xdg-open", chemin_sortie], check=True)
        except Exception as e:
            print(f"[ERREUR ouverture] {e}")

        print(f"Fichier éditable créé (3 styles) : {chemin_sortie}")
        print("OK")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--export-pptx":
        texte = sys.argv[2]
        format_cle = sys.argv[3] if len(sys.argv) > 3 else "post"
        chemin_image_fond = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
        style = sys.argv[5] if len(sys.argv) > 5 else "classique"

        if chemin_image_fond == "IA":
            dossier_promo = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Promo"))
            chemin_image_fond = os.path.join(dossier_promo, ".fond_ia_temp.png")
            if not os.path.exists(chemin_image_fond):
                print("[ERREUR] Le fond généré par IA est introuvable — régénère l'image d'abord.")
                sys.exit(1)

        dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Promo"))
        os.makedirs(dossier, exist_ok=True)
        horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
        chemin_sortie = os.path.join(dossier, f"promo_editable_{horodatage}.pptx")

        exporter_pptx(texte, format_cle, chemin_image_fond, style, chemin_sortie)

        systeme = platform.system()
        try:
            if systeme == "Darwin":
                subprocess.run(["open", chemin_sortie], check=True)
            elif systeme == "Windows":
                os.startfile(chemin_sortie)
            else:
                subprocess.run(["xdg-open", chemin_sortie], check=True)
        except Exception as e:
            print(f"[ERREUR ouverture] {e}")

        print(f"Fichier éditable créé : {chemin_sortie}")
        print("OK")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--finaliser":
        # Deuxième étape : le style choisi est donné en 2ème argument
        style_choisi = sys.argv[2] if len(sys.argv) > 2 else "classique"
        dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Promo"))
        chemin_temp = os.path.join(dossier, f".apercu_temp_{style_choisi}.png")

        if not os.path.exists(chemin_temp):
            print("[ERREUR] Aucun aperçu à sauvegarder. Génère d'abord un aperçu.")
            sys.exit(1)

        horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
        chemin_final = os.path.join(dossier, f"promo_{style_choisi}_{horodatage}.png")

        import shutil
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

    try:
        from PIL import Image
    except ImportError:
        print("Bibliothèque manquante. Lance : pip3 install Pillow --break-system-packages")
        sys.exit(1)

    dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Promo"))
    os.makedirs(dossier, exist_ok=True)

    import base64

    # Génère les 3 styles d'un coup, chacun dans son propre fichier temporaire
    for style in STYLES_DISPONIBLES:
        chemin_temp = os.path.join(dossier, f".apercu_temp_{style}.png")
        creer_image(texte, format_cle, chemin_temp, chemin_image_fond, style)
        with open(chemin_temp, "rb") as f:
            contenu_base64 = base64.b64encode(f.read()).decode("ascii")
        print(f"---IMAGE_{style.upper()}---")
        print(contenu_base64)
