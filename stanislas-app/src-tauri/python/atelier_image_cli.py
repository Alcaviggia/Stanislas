"""
Action : Atelier image
Génère une image directement à partir d'une description libre — pas de
texte posé par-dessus, pas de format promo, juste une vraie image.
Réutilise le même moteur (Flux) et le même enrichissement de prompt que
Promo, pour ne pas dupliquer la logique de génération.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from promo_image_ia import generer_fond


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucune description fournie.")
        sys.exit(1)

    description = sys.argv[1].strip()
    if not description:
        print("[ERREUR] La description est vide.")
        sys.exit(1)

    dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Atelier image"))
    os.makedirs(dossier, exist_ok=True)

    from datetime import datetime
    horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
    chemin_sortie = os.path.join(dossier, f"image_{horodatage}.png")

    generer_fond(description, "post", chemin_sortie)

    import base64
    with open(chemin_sortie, "rb") as f:
        contenu_base64 = base64.b64encode(f.read()).decode("ascii")

    print("---IMAGE_BASE64---", flush=True)
    print(contenu_base64)
