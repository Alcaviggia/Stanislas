"""
Deux usages :
- Sans argument : compte les fichiers présents dans chaque sous-dossier
  de Documents/Stanislas/, pour afficher un vrai nombre sur les icônes
  de la fenêtre Dossiers.
- --lister <nom_dossier> : liste individuellement les fichiers d'UN
  dossier précis (nom, taille, date), pour permettre de les voir et
  les supprimer un par un directement dans Stanislas.
"""
import os
import sys
import json
from datetime import datetime

DOSSIERS = ["Courrier", "Bloc-notes", "Documents", "Calculer", "Comparer", "Promo", "Budget", "Comprendre", "Désamorcer", "Correcteur", "Devis", "Offre emploi", "Extraire RDV", "Extraire", "Vérifier", "Atelier image", "Transcription", "Montage", "Traduire"]


def lister_fichiers(nom_dossier: str):
    base = os.path.expanduser(os.path.join("~", "Documents", "Stanislas"))
    chemin = os.path.join(base, nom_dossier)
    # Garde-fou : le dossier doit être un sous-dossier direct de
    # Documents/Stanislas, jamais un chemin qui en sortirait
    if os.path.dirname(os.path.abspath(chemin)) != os.path.abspath(base):
        print(json.dumps({"erreur": "chemin invalide"}))
        return

    fichiers = []
    if os.path.isdir(chemin):
        for nom in sorted(os.listdir(chemin), reverse=True):
            if nom.startswith("."):
                continue
            chemin_complet = os.path.join(chemin, nom)
            if os.path.isfile(chemin_complet):
                stats = os.stat(chemin_complet)
                fichiers.append({
                    "nom": nom,
                    "taille": stats.st_size,
                    "date": datetime.fromtimestamp(stats.st_mtime).strftime("%d/%m/%Y %Hh%M"),
                })
    print(json.dumps(fichiers))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--lister":
        nom_dossier = sys.argv[2] if len(sys.argv) > 2 else ""
        lister_fichiers(nom_dossier)
        sys.exit(0)

    base = os.path.expanduser(os.path.join("~", "Documents", "Stanislas"))
    resultats = {}
    for nom in DOSSIERS:
        chemin = os.path.join(base, nom)
        if os.path.isdir(chemin):
            fichiers = [f for f in os.listdir(chemin) if not f.startswith(".")]
            resultats[nom] = len(fichiers)
        else:
            resultats[nom] = 0
    print(json.dumps(resultats))
