"""
Enregistre la langue choisie dans les Préférences (français/anglais) dans
un petit fichier local — c'est le pont entre le choix fait côté interface
(JavaScript, localStorage) et le choix du modèle IA côté Python, qui ne
peut pas lire le localStorage du navigateur directement.
"""
import sys
import os
import json

CHEMIN_LANGUE = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", ".langue.json"))


def definir_langue(langue: str):
    os.makedirs(os.path.dirname(CHEMIN_LANGUE), exist_ok=True)
    with open(CHEMIN_LANGUE, "w", encoding="utf-8") as f:
        json.dump({"langue": langue}, f)


if __name__ == "__main__":
    langue = sys.argv[1] if len(sys.argv) > 1 else "fr"
    definir_langue(langue)
    print("OK")
