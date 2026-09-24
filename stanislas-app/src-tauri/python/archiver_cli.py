"""
Enregistre une réponse générée dans son dossier, sous
~/Documents/Stanislas/<nom_dossier>/<horodatage>.txt
Python gère tout lui-même (création de dossier, écriture) — fiable,
sans dépendre des APIs Tauri fs, comme pour l'ouverture de fichiers.
"""
import sys
import os
from datetime import datetime

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("[ERREUR] Usage : archiver_cli.py <nom_dossier> <contenu> [extension]")
        sys.exit(1)

    nom_dossier = sys.argv[1]
    contenu = sys.argv[2]
    extension = sys.argv[3] if len(sys.argv) > 3 else "txt"

    chemin_dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", nom_dossier))
    os.makedirs(chemin_dossier, exist_ok=True)

    horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
    chemin_fichier = os.path.join(chemin_dossier, f"{horodatage}.{extension}")

    with open(chemin_fichier, "w", encoding="utf-8") as f:
        f.write(contenu)

    print("OK")
    print(chemin_fichier)
