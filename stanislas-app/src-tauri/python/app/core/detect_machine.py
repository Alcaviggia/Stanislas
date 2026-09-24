"""
Détecte la RAM disponible sur la machine (Mac, Windows, Linux) et propose
un profil adapté. Aucune dépendance externe — uniquement des commandes
système natives, pour rester dans l'esprit "zéro installation surprise".
"""
import subprocess
import platform
import re

PROFILS = {
    "leger": {
        "nom": "Léger",
        "seuil_go": 0,
        "modele": "llama3.2:3b",
        "description": "8 Go ou moins de RAM détectés",
    },
    "confort": {
        "nom": "Confort",
        "seuil_go": 12,
        "modele": "qwen3:8b",
        "description": "Environ 16 Go de RAM détectés",
    },
    "performance": {
        "nom": "Performance",
        "seuil_go": 28,
        "modele": "qwen3.6:27b",
        "description": "32 Go de RAM ou plus détectés",
    },
}


def ram_totale_go() -> float:
    """Renvoie la RAM totale en Go, ou 0 si la détection échoue."""
    systeme = platform.system()

    try:
        if systeme == "Darwin":  # macOS
            sortie = subprocess.run(
                ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5
            )
            octets = int(sortie.stdout.strip())
            return octets / (1024 ** 3)

        elif systeme == "Windows":
            sortie = subprocess.run(
                ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                capture_output=True, text=True, timeout=5
            )
            chiffres = re.findall(r"\d+", sortie.stdout)
            if chiffres:
                octets = int(chiffres[0])
                return octets / (1024 ** 3)

        elif systeme == "Linux":
            with open("/proc/meminfo") as f:
                ligne = f.readline()
                ko = int(re.findall(r"\d+", ligne)[0])
                return ko / (1024 ** 2)

    except Exception as e:
        print(f"[Détection RAM impossible : {e}]")

    return 0.0


def profil_recommande() -> dict:
    ram = ram_totale_go()

    if ram >= PROFILS["performance"]["seuil_go"]:
        choix = "performance"
    elif ram >= PROFILS["confort"]["seuil_go"]:
        choix = "confort"
    else:
        choix = "leger"

    resultat = dict(PROFILS[choix])
    resultat["ram_detectee_go"] = round(ram, 1)
    resultat["cle"] = choix
    return resultat


def detecter_gpu() -> dict:
    """
    Détecte la capacité graphique pour l'image/vidéo locale.
    Sur Mac : la RAM unifiée sert d'indicateur (le GPU la partage).
    Sur PC : cherche une carte NVIDIA dédiée (seule filière bien détectable
    simplement) ; à défaut, on suppose un GPU intégré, insuffisant.
    """
    systeme = platform.system()

    if systeme == "Darwin":
        ram = ram_totale_go()
        puce = "inconnue"
        try:
            sortie = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=5
            )
            puce = sortie.stdout.strip() or puce
        except Exception:
            pass
        return {"type": "unifie", "puce": puce, "ram_go": ram, "vram_go": None}

    # PC : on tente de détecter une carte NVIDIA via nvidia-smi
    try:
        sortie = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if sortie.returncode == 0 and sortie.stdout.strip():
            ligne = sortie.stdout.strip().splitlines()[0]
            chiffres = re.findall(r"\d+", ligne)
            vram_mo = int(chiffres[0]) if chiffres else 0
            return {"type": "dediee", "puce": ligne, "ram_go": None, "vram_go": vram_mo / 1024}
    except Exception:
        pass

    return {"type": "integre", "puce": "GPU intégré (non identifié précisément)", "ram_go": None, "vram_go": None}


def profil_image_video() -> dict:
    """Recommandation honnête : image locale seulement si le matériel suit,
    vidéo locale quasiment jamais recommandée en 2026 (qualité encore faible)."""
    gpu = detecter_gpu()

    if gpu["type"] == "unifie":
        ram = gpu["ram_go"] or 0
        if ram >= 32:
            return {"image_locale": True, "qualite": "correcte", "video_locale": False,
                     "raison": f"Mac avec {round(ram)} Go de mémoire unifiée ({gpu['puce']})"}
        elif ram >= 16:
            return {"image_locale": True, "qualite": "basique", "video_locale": False,
                     "raison": f"Mac avec {round(ram)} Go de mémoire unifiée ({gpu['puce']})"}
        else:
            return {"image_locale": False, "qualite": None, "video_locale": False,
                     "raison": f"Mémoire unifiée trop limitée ({round(ram)} Go) pour l'image locale"}

    if gpu["type"] == "dediee":
        vram = gpu["vram_go"] or 0
        if vram >= 12:
            return {"image_locale": True, "qualite": "correcte", "video_locale": False,
                     "raison": f"GPU dédié détecté avec {round(vram)} Go de VRAM"}
        elif vram >= 6:
            return {"image_locale": True, "qualite": "basique", "video_locale": False,
                     "raison": f"GPU dédié détecté avec {round(vram)} Go de VRAM"}
        else:
            return {"image_locale": False, "qualite": None, "video_locale": False,
                     "raison": f"VRAM dédiée insuffisante ({round(vram)} Go)"}

    return {"image_locale": False, "qualite": None, "video_locale": False,
             "raison": "Aucun GPU dédié détecté (probablement graphique intégré)"}


if __name__ == "__main__":
    profil = profil_recommande()
    print(f"RAM détectée : {profil['ram_detectee_go']} Go")
    print(f"Profil recommandé : {profil['nom']} ({profil['description']})")
    print(f"Modèle à utiliser : {profil['modele']}")

    print()
    pv = profil_image_video()
    print(f"Image locale possible : {'oui' if pv['image_locale'] else 'non'}")
    if pv['image_locale']:
        print(f"Qualité attendue : {pv['qualite']}")
    print(f"Raison : {pv['raison']}")
    print(f"Vidéo locale : non recommandée en 2026 quel que soit le matériel — passer par le cloud")
