"""
Extrait le texte d'un fichier déposé par l'utilisateur (PDF, Word, texte,
markdown) — 100% local, aucun envoi du fichier nulle part.

Usage :
    python3 lire_fichier_cli.py <chemin_du_fichier>

Sortie : un marqueur ---CONTENU--- suivi du texte extrait.

Dépendances requises (une seule fois) :
    pip3 install pypdf python-docx --break-system-packages
"""
import sys
import os


def lire_pdf(chemin: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("[ERREUR] La bibliothèque 'pypdf' n'est pas installée.")
        print("Lance : pip3 install pypdf --break-system-packages")
        sys.exit(1)

    lecteur = PdfReader(chemin)
    morceaux = []
    for page in lecteur.pages:
        texte_page = page.extract_text()
        if texte_page:
            morceaux.append(texte_page)

    if not morceaux:
        return "(Aucun texte n'a pu être extrait de ce PDF — il s'agit peut-être d'un PDF scanné/image, sans texte réel dedans.)"

    return "\n\n".join(morceaux)


def lire_docx(chemin: str) -> str:
    try:
        import docx
    except ImportError:
        print("[ERREUR] La bibliothèque 'python-docx' n'est pas installée.")
        print("Lance : pip3 install python-docx --break-system-packages")
        sys.exit(1)

    document = docx.Document(chemin)
    paragraphes = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphes)


def lire_csv(chemin: str) -> str:
    import csv

    for encodage in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(chemin, "r", encoding=encodage, newline="") as f:
                lecteur = csv.reader(f)
                lignes = list(lecteur)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        return "(Impossible de lire ce fichier CSV — encodage non reconnu.)"

    # Reformate en texte lisible plutôt qu'en CSV brut (virgules/points-virgules
    # collés) — plus facile à interpréter correctement pour le modèle local
    return "\n".join(" | ".join(cellule for cellule in ligne) for ligne in lignes)


def lire_texte_brut(chemin: str) -> str:
    # Essaie plusieurs encodages courants, au cas où le fichier ne soit
    # pas en UTF-8 (ex: vieux fichiers Windows en latin-1)
    for encodage in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(chemin, "r", encoding=encodage) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # Dernier recours : lecture en ignorant les caractères problématiques
    with open(chemin, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucun fichier fourni.")
        sys.exit(1)

    chemin = sys.argv[1]

    if not os.path.exists(chemin):
        print(f"[ERREUR] Fichier introuvable : {chemin}")
        sys.exit(1)

    extension = os.path.splitext(chemin)[1].lower()

    try:
        if extension == ".pdf":
            contenu = lire_pdf(chemin)
        elif extension == ".docx":
            contenu = lire_docx(chemin)
        elif extension == ".csv":
            contenu = lire_csv(chemin)
        elif extension in (".txt", ".md"):
            contenu = lire_texte_brut(chemin)
        else:
            print(f"[ERREUR] Format non pris en charge : {extension}")
            sys.exit(1)
    except Exception as e:
        print(f"[ERREUR lecture] {e}")
        sys.exit(1)

    print("---CONTENU---")
    print(contenu)
