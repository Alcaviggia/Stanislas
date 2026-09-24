"""
Crée un raccourci (alias/lien symbolique) sur le vrai Bureau du Mac,
pointant vers le dossier Documents/Stanislas où tout est déjà rangé —
pour un accès en un clic, sans dupliquer aucun fichier.

Sûr à appeler à chaque lancement de l'app : ne fait rien si le raccourci
existe déjà.
"""
import os
import sys


def creer_raccourci():
    dossier_reel = os.path.expanduser(os.path.join("~", "Documents", "Stanislas"))
    dossier_bureau = os.path.expanduser(os.path.join("~", "Desktop"))
    raccourci = os.path.join(dossier_bureau, "Stanislas")

    os.makedirs(dossier_reel, exist_ok=True)
    os.makedirs(dossier_bureau, exist_ok=True)

    if os.path.islink(raccourci) or os.path.exists(raccourci):
        # Déjà présent (raccourci ou dossier) — rien à faire
        return

    try:
        os.symlink(dossier_reel, raccourci)
        print(f"Raccourci créé sur le Bureau : {raccourci}")
    except Exception as e:
        print(f"[ERREUR] Impossible de créer le raccourci : {e}")


if __name__ == "__main__":
    creer_raccourci()
