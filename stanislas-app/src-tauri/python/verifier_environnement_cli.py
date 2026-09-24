"""
Vérifie l'état de l'environnement IA local (Ollama + modèles requis),
pour l'écran de premier lancement.

Ne vérifie PAS si Python est installé — si ce script tourne, c'est que
Python fonctionne déjà. La vérification de Python doit se faire côté
JavaScript/Tauri, avant même d'essayer d'appeler ce script.
"""
import sys
import json
import urllib.request

OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"


def lister_modeles_installes():
    """Retourne la liste des modèles déjà installés, ou None si Ollama
    n'est pas joignable du tout (pas lancé, ou pas installé)."""
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=5) as reponse:
            data = json.loads(reponse.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return None


if __name__ == "__main__":
    # Les deux modèles de texte sont toujours requis, peu importe la
    # langue de l'interface — la langue affichée et le modèle IA utilisé
    # sont deux choses différentes, l'un ne doit jamais dépendre de l'autre
    modeles_requis = ["ministral-3:8b", "qwen3:8b", "nomic-embed-text"]

    installes = lister_modeles_installes()

    if installes is None:
        print("OLLAMA_INTROUVABLE")
        sys.exit(0)

    print("OLLAMA_OK")
    for modele in modeles_requis:
        # Les noms installés incluent parfois ":latest", on compare la base
        trouve = any(m == modele or m.startswith(modele + ":") or m == modele + ":latest" for m in installes)
        if trouve:
            print(f"MODELE_OK:{modele}")
        else:
            print(f"MODELE_MANQUANT:{modele}")
