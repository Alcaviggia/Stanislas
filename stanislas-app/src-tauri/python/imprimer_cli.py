"""
Écrit le texte reçu dans un fichier temporaire et l'ouvre avec l'app par
défaut du système (TextEdit sur Mac) — Python gère tout lui-même,
sans dépendre des APIs Tauri fs/path, pour rester fiable.

Gère aussi la Corbeille de Stanislas : un dossier caché
(Documents/Stanislas/.Corbeille) où les fichiers supprimés sont
D'ABORD déplacés (récupérables), avant une suppression définitive via
une action "vider la corbeille" séparée — comme une vraie corbeille
Mac, pas une suppression immédiate.
"""
import sys
import os
import tempfile
import subprocess
import platform
import shutil

NOM_CORBEILLE = ".Corbeille"


def _racine():
    return os.path.expanduser(os.path.join("~", "Documents", "Stanislas"))


def _dossier_corbeille():
    chemin = os.path.join(_racine(), NOM_CORBEILLE)
    os.makedirs(chemin, exist_ok=True)
    return chemin


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--ouvrir-dossier":
        sous_dossier = sys.argv[2] if len(sys.argv) > 2 else ""
        chemin = os.path.join(_racine(), sous_dossier)
        os.makedirs(chemin, exist_ok=True)
        systeme = platform.system()
        try:
            if systeme == "Darwin":
                subprocess.run(["open", chemin], check=True)
            elif systeme == "Windows":
                os.startfile(chemin)
            else:
                subprocess.run(["xdg-open", chemin], check=True)
            print("OK")
        except Exception as e:
            print(f"[ERREUR] {e}")
            sys.exit(1)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--reglages-imprimante":
        systeme = platform.system()
        try:
            if systeme == "Darwin":
                subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.printfax"], check=True)
            elif systeme == "Windows":
                os.startfile("ms-settings:printers")
            else:
                subprocess.run(["xdg-open", "system-config-printer"], check=True)
            print("OK")
        except Exception as e:
            print(f"[ERREUR] {e}")
            sys.exit(1)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--deplacer-vers-corbeille":
        # Déplace UN fichier précis vers la Corbeille de Stanislas —
        # pas une suppression définitive, il reste récupérable tant que
        # la corbeille n'a pas été vidée explicitement.
        sous_dossier = sys.argv[2] if len(sys.argv) > 2 else ""
        nom_fichier = sys.argv[3] if len(sys.argv) > 3 else ""
        racine = _racine()
        dossier = os.path.join(racine, sous_dossier)
        chemin_fichier = os.path.join(dossier, nom_fichier)
        try:
            if not sous_dossier or os.path.dirname(os.path.abspath(dossier)) != os.path.abspath(racine):
                print("[ERREUR] Nom de dossier invalide, opération annulée par sécurité.")
                sys.exit(1)
            if not nom_fichier or os.sep in nom_fichier or "/" in nom_fichier or os.path.dirname(os.path.abspath(chemin_fichier)) != os.path.abspath(dossier):
                print("[ERREUR] Nom de fichier invalide, opération annulée par sécurité.")
                sys.exit(1)
            if os.path.isfile(chemin_fichier):
                corbeille = _dossier_corbeille()
                # Préfixe avec le dossier d'origine pour éviter les
                # collisions de noms, et pour pouvoir un jour restaurer
                # au bon endroit si besoin
                nom_dans_corbeille = f"{sous_dossier}__{nom_fichier}"
                destination = os.path.join(corbeille, nom_dans_corbeille)
                # Si un fichier du même nom existe déjà en corbeille, on
                # ajoute un suffixe plutôt que d'écraser silencieusement
                compteur = 1
                base, ext = os.path.splitext(destination)
                while os.path.exists(destination):
                    destination = f"{base}_{compteur}{ext}"
                    compteur += 1
                shutil.move(chemin_fichier, destination)
            print("OK")
        except Exception as e:
            print(f"[ERREUR] {e}")
            sys.exit(1)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--etat-corbeille":
        # Renvoie le nombre d'éléments actuellement dans la Corbeille —
        # pour savoir si l'icône doit s'afficher pleine ou vide.
        corbeille = os.path.join(_racine(), NOM_CORBEILLE)
        n = 0
        if os.path.isdir(corbeille):
            n = len([f for f in os.listdir(corbeille) if not f.startswith(".")])
        print(n)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--vider-corbeille":
        # Supprime DÉFINITIVEMENT le contenu de la Corbeille de
        # Stanislas (Documents/Stanislas/.Corbeille) — pas tout
        # Documents/Stanislas, juste ce qui a été mis à la corbeille.
        # La confirmation est déjà demandée côté interface.
        corbeille = os.path.join(_racine(), NOM_CORBEILLE)
        try:
            racine_attendue = os.path.abspath(_racine())
            if os.path.abspath(corbeille) != os.path.join(racine_attendue, NOM_CORBEILLE):
                print("[ERREUR] Chemin inattendu, opération annulée par sécurité.")
                sys.exit(1)
            if os.path.isdir(corbeille):
                for nom in os.listdir(corbeille):
                    chemin_element = os.path.join(corbeille, nom)
                    if os.path.isdir(chemin_element):
                        shutil.rmtree(chemin_element)
                    else:
                        os.remove(chemin_element)
            print("OK")
        except Exception as e:
            print(f"[ERREUR] {e}")
            sys.exit(1)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--vider-dossier":
        # Supprime uniquement le contenu d'UN dossier précis (ex :
        # "Courrier"), pas toutes les archives — sélection par dossier,
        # plus sûr qu'un "tout ou rien". Suppression définitive directe
        # (pas via la Corbeille) — action volontairement plus rare et
        # plus lourde qu'une suppression fichier par fichier.
        sous_dossier = sys.argv[2] if len(sys.argv) > 2 else ""
        racine = _racine()
        dossier = os.path.join(racine, sous_dossier)
        try:
            if not sous_dossier or os.path.dirname(os.path.abspath(dossier)) != os.path.abspath(racine):
                print("[ERREUR] Nom de dossier invalide, opération annulée par sécurité.")
                sys.exit(1)
            if os.path.isdir(dossier):
                for nom in os.listdir(dossier):
                    chemin_element = os.path.join(dossier, nom)
                    if os.path.isdir(chemin_element):
                        shutil.rmtree(chemin_element)
                    else:
                        os.remove(chemin_element)
            print("OK")
        except Exception as e:
            print(f"[ERREUR] {e}")
            sys.exit(1)
        sys.exit(0)

    if len(sys.argv) < 2:
        print("[ERREUR] Aucun texte à imprimer.")
        sys.exit(1)

    texte = sys.argv[1]

    fichier_temp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="stanislas_", delete=False, encoding="utf-8"
    )
    fichier_temp.write(texte)
    fichier_temp.close()

    systeme = platform.system()
    try:
        if systeme == "Darwin":
            subprocess.run(["open", fichier_temp.name], check=True)
        elif systeme == "Windows":
            os.startfile(fichier_temp.name)
        else:
            subprocess.run(["xdg-open", fichier_temp.name], check=True)
        print("OK")
    except Exception as e:
        print(f"[ERREUR] Impossible d'ouvrir le fichier : {e}")
        sys.exit(1)
