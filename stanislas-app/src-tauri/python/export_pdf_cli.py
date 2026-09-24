"""
Transforme un texte (résultat d'une fonction Stanislas — Devis, Courrier,
Offre d'emploi...) en un vrai document PDF propre, prêt à imprimer —
100% local, aucun envoi nulle part.

Usage :
    python3 export_pdf_cli.py <texte> <titre>

<titre> sert à la fois de titre affiché en haut du PDF et de nom de
sous-dossier d'archivage (ex: "Devis" -> Archives/Devis/).

Sortie : un marqueur ---RESULTAT--- suivi du chemin du fichier PDF créé.

Dépendance requise (une seule fois) :
    python3 -m pip install reportlab --break-system-packages
"""
import sys
import os
import platform
from datetime import datetime


def dossier_donnees_app() -> str:
    """Même emplacement que les autres fonctions qui sauvegardent des
    fichiers (Montage vidéo...) — jamais dans le dossier de l'app
    lui-même, toujours dans Documents, visible et facile à retrouver."""
    systeme = platform.system()
    if systeme == "Windows":
        return os.path.join(os.path.expanduser("~"), "Documents", "Stanislas")
    return os.path.expanduser("~/Documents/Stanislas")


def creer_pdf(texte: str, titre: str, chemin_sortie: str) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.enums import TA_LEFT

    doc = SimpleDocTemplate(
        chemin_sortie,
        pagesize=A4,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle(
        "TitreStanislas", parent=styles["Title"], alignment=TA_LEFT, spaceAfter=4,
    )
    style_date = ParagraphStyle(
        "DateStanislas", parent=styles["Normal"], textColor="#666666", spaceAfter=20,
    )
    style_corps = ParagraphStyle(
        "CorpsStanislas", parent=styles["Normal"], fontSize=11, leading=16, spaceAfter=12,
    )

    elements = [
        Paragraph(titre, style_titre),
        Paragraph(datetime.now().strftime("%d/%m/%Y"), style_date),
        Spacer(1, 6),
    ]

    # Un paragraphe PDF par paragraphe séparé par une ligne vide dans le
    # texte d'origine, pour garder une mise en page lisible
    for bloc in texte.split("\n\n"):
        bloc = bloc.strip()
        if not bloc:
            continue
        # échappe les caractères spéciaux XML/HTML que reportlab interprète
        bloc_echappe = (
            bloc.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        ).replace("\n", "<br/>")
        elements.append(Paragraph(bloc_echappe, style_corps))

    doc.build(elements)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("[ERREUR] Usage : export_pdf_cli.py <texte> <titre>")
        sys.exit(1)

    texte = sys.argv[1]
    titre = sys.argv[2]

    try:
        dossier_sortie = os.path.join(dossier_donnees_app(), "Archives", titre)
        os.makedirs(dossier_sortie, exist_ok=True)

        nom_fichier = f"{titre}_{datetime.now().strftime('%Y-%m-%d_%Hh%M')}.pdf"
        chemin_final = os.path.join(dossier_sortie, nom_fichier)

        creer_pdf(texte, titre, chemin_final)
    except ModuleNotFoundError:
        print("[ERREUR] La bibliothèque 'reportlab' n'est pas installée.")
        print("Lance : python3 -m pip install reportlab --break-system-packages")
        sys.exit(1)
    except Exception as e:
        print(f"[ERREUR] {e}")
        sys.exit(1)

    print("---RESULTAT---")
    print(chemin_final)
