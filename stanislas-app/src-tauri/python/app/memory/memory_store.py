"""
Mémoire minimale de Stanislas : un fichier JSON local par utilisateur.
Deux sections : le style (ton) et les faits métier (tarifs, horaires, etc.).
Volontairement simple pour la v1 — pas de base de données.
"""
import json
import os

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "memory.json")

DEFAULTS = {
    "style": {
        "tutoiement": False,
        "longueur": "courte",  # courte | moyenne | detaillee
    },
    "faits": {
        # exemples : "tarif_horaire": "45€", "horaires": "9h-18h du lundi au vendredi"
    },
}


def load() -> dict:
    if not os.path.exists(MEMORY_PATH):
        save(DEFAULTS)
        return DEFAULTS
    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data: dict) -> None:
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_fait(cle: str, valeur: str) -> None:
    data = load()
    data["faits"][cle] = valeur
    save(data)


def contexte_pour_prompt() -> str:
    """Résume la mémoire en quelques lignes à injecter dans les prompts."""
    data = load()
    style = data["style"]
    faits = data["faits"]
    lignes = []
    lignes.append("Tutoiement" if style["tutoiement"] else "Vouvoiement")
    lignes.append(f"Longueur de réponse préférée : {style['longueur']}")
    if faits:
        lignes.append("Faits connus sur l'entreprise :")
        for cle, valeur in faits.items():
            lignes.append(f"- {cle} : {valeur}")
    return "\n".join(lignes)
