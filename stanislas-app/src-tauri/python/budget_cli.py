"""
Analyse des relevés bancaires ou de dépenses — 100% local, via Ollama.

Architecture différente de la première version : chaque groupe de
transactions donne directement ses chiffres sous forme structurée
(catégorie, montant, type), et c'est du calcul PYTHON classique — pas
un nouvel appel à l'IA — qui additionne les totaux entre les groupes.
L'IA n'intervient qu'une seule fois à la toute fin, pour rédiger un
texte lisible à partir de chiffres déjà calculés (un appel léger,
rapide, sans réanalyser les données brutes) — ça évite complètement
l'étape qui posait problème (redemander à l'IA de recombiner plusieurs
résumés), plutôt que d'essayer de la rendre fiable.

Usage :
    python3 budget_cli.py --decouper <contenu>
    python3 budget_cli.py --groupe <texte_du_groupe>
    python3 budget_cli.py --narratif <totaux_deja_calcules>
    python3 budget_cli.py --csv <totaux_deja_calcules>
"""
import sys
import os
import re
import csv
import io

sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.core.ollama_client import ask
except ImportError:
    ask = None

TAILLE_GROUPE_CARACTERES = 20000
SEPARATEUR_GROUPES = "\n---GROUPE_SUIVANT---\n"


def _decouper_par_taille_fixe(contenu: str) -> list:
    groupes = []
    debut = 0
    while debut < len(contenu):
        fin = min(debut + TAILLE_GROUPE_CARACTERES, len(contenu))
        if fin < len(contenu):
            coupure = contenu.rfind("\n", debut, fin)
            if coupure > debut:
                fin = coupure
        groupes.append(contenu[debut:fin])
        debut = fin
    return [g for g in groupes if g.strip()]


def _decouper_en_groupes(contenu: str) -> list:
    if len(contenu) <= TAILLE_GROUPE_CARACTERES:
        return [contenu]

    marqueurs = [m.start() for m in re.finditer(r"--- Document :", contenu)]

    if len(marqueurs) > 1:
        groupes_bruts = []
        debut_groupe = 0
        for position in marqueurs:
            if position - debut_groupe > TAILLE_GROUPE_CARACTERES and position > debut_groupe:
                groupes_bruts.append(contenu[debut_groupe:position])
                debut_groupe = position
        groupes_bruts.append(contenu[debut_groupe:])
        groupes_bruts = [g for g in groupes_bruts if g.strip()]
    else:
        groupes_bruts = [contenu]

    groupes_finaux = []
    for groupe in groupes_bruts:
        if len(groupe) > TAILLE_GROUPE_CARACTERES * 1.3:
            groupes_finaux.extend(_decouper_par_taille_fixe(groupe))
        else:
            groupes_finaux.append(groupe)
    return groupes_finaux


def _prompt_groupe(groupe: str) -> str:
    """Demande un résultat structuré (CSV) directement — plus facile à
    additionner ensuite avec du code, sans redemander à l'IA. Volontairement
    simple (3 colonnes, pas de classification Fixe/Variable ici) — une
    version antérieure demandait une 4e colonne à l'IA, ce qui a
    réintroduit des blocages sur certains groupes (réponse plus longue
    et plus complexe à produire) ; la classification Fixe/Variable se
    fait maintenant par du code, sur le nom de la catégorie."""
    return f"""Voici une partie des données financières d'un indépendant
(relevé bancaire, dépenses — un CSV importé se présente en lignes
séparées par " | ") :
---
{groupe}
---

Identifie chaque catégorie de dépense ou d'entrée d'argent présente,
et le montant total pour cette catégorie dans ce texte.

Réponds UNIQUEMENT avec un tableau CSV (séparateur virgule), exactement
ces 3 colonnes : Categorie,Montant,Type

- Type vaut "Entree" ou "Sortie".
- Montant est un nombre simple (ex: 250.00, jamais de virgule décimale
  ni de symbole €).

Une ligne par catégorie. Pas de texte avant ou après, pas d'en-tête,
juste les lignes de données."""


def totaux_vers_texte_detaille(totaux: dict) -> str:
    """Version texte (pas CSV) des mêmes calculs, pour que l'analyse
    écrite par l'IA s'appuie sur EXACTEMENT les mêmes chiffres que le
    tableau CSV — jamais deux versions incohérentes des mêmes données."""
    entrees = [(c, m) for (c, t, n), m in totaux.items() if t.lower() == "entree"]
    charges_fixes = [(c, m) for (c, t, n), m in totaux.items() if t.lower() == "sortie" and n.lower() == "fixe"]
    charges_variables = [(c, m) for (c, t, n), m in totaux.items() if t.lower() == "sortie" and n.lower() == "variable"]

    total_entrees = sum(m for _, m in entrees)
    total_charges_fixes = sum(m for _, m in charges_fixes)
    total_charges_variables = sum(m for _, m in charges_variables)
    total_charges = total_charges_fixes + total_charges_variables
    solde = total_entrees - total_charges

    lignes = [f"ENTREES (total {total_entrees:.2f}) :"]
    for cat, montant in sorted(entrees, key=lambda x: -x[1]):
        lignes.append(f"  - {cat} : {montant:.2f}")

    lignes.append(f"\nCHARGES FIXES (total {total_charges_fixes:.2f}) :")
    for cat, montant in sorted(charges_fixes, key=lambda x: -x[1]):
        lignes.append(f"  - {cat} : {montant:.2f}")

    lignes.append(f"\nCHARGES VARIABLES (total {total_charges_variables:.2f}) :")
    for cat, montant in sorted(charges_variables, key=lambda x: -x[1]):
        lignes.append(f"  - {cat} : {montant:.2f}")

    lignes.append(f"\nTotal charges : {total_charges:.2f}")
    lignes.append(f"Solde : {solde:.2f}")

    lignes.append("\nOBJECTIFS D'EPARGNE SUGGERES (-15% sur les charges variables) :")
    economie_totale = 0
    for cat, montant in sorted(charges_variables, key=lambda x: -x[1]):
        objectif = montant * 0.85
        economie = montant - objectif
        economie_totale += economie
        lignes.append(f"  - {cat} : de {montant:.2f} à {objectif:.2f} (économie {economie:.2f})")
    lignes.append(f"Économie mensuelle totale possible : {economie_totale:.2f}")

    return "\n".join(lignes)


def _prompt_narratif(totaux_texte: str) -> str:
    """Un seul appel léger, à la toute fin — rédige un texte à partir de
    chiffres DÉJÀ calculés (pas besoin de réanalyser des données brutes,
    donc un appel rapide et sûr, même après beaucoup de groupes)."""
    return f"""Voici les totaux déjà calculés à partir des relevés
financiers d'un indépendant, avec des objectifs d'épargne déjà
chiffrés (calculés avec précision, ne recalcule rien, utilise ces
chiffres tels quels) :
---
{totaux_texte}
---

Rédige une analyse financière claire à partir de CES chiffres exacts :

1. **Vue d'ensemble** : entrées, sorties, solde net.
2. **Répartition** : les postes du plus gros au plus petit, avec leur
   part du total des charges.
3. **Ce qui pèse le plus lourd** : les 2-3 postes principaux, et ce
   qui les compose.
4. **Où économiser, concrètement** : reprends les objectifs d'épargne
   déjà calculés ci-dessus (montant actuel → objectif, économie par
   poste, et le total mensuel possible) — ne recalcule rien, présente
   ces chiffres clairement.

N'invente aucun chiffre en dehors de ceux fournis ci-dessus. Réponds
directement avec l'analyse, sans préambule."""


MOTS_CLES_FIXE = (
    "loyer", "assurance", "abonnement", "credit", "crédit", "pret", "prêt",
    "salaire", "domiciliation", "telecom", "téléphone", "internet",
    "electricite", "électricité", "eau", "gaz", "mutuelle", "leasing",
)


def deviner_nature(categorie: str) -> str:
    """Devine Fixe/Variable à partir du nom de la catégorie, par mots-clés
    — jamais demandé à l'IA (ça alourdissait sa réponse et provoquait des
    blocages). Un classement approximatif par mots-clés reste plus fiable
    qu'une classification qui fait parfois planter le modèle."""
    categorie_minuscule = categorie.lower()
    return "Fixe" if any(mot in categorie_minuscule for mot in MOTS_CLES_FIXE) else "Variable"


def parser_csv_groupe(texte_csv: str) -> list:
    """Extrait les lignes (categorie, montant, type, nature) d'une
    réponse CSV de l'IA — tolérant aux petites erreurs de formatage.
    La nature (Fixe/Variable) est devinée par mots-clés, pas demandée
    à l'IA (voir deviner_nature)."""
    lignes = []
    lecteur = csv.reader(io.StringIO(texte_csv.strip()))
    for rang in lecteur:
        if len(rang) < 2:
            continue
        categorie = rang[0].strip()
        if not categorie or categorie.lower() in ("categorie", "category", "entree", "sortie", "type"):
            continue
        try:
            montant = float(rang[1].strip().replace(",", ".").replace("€", "").replace("$", ""))
        except (ValueError, IndexError):
            continue
        type_ = rang[2].strip() if len(rang) > 2 else "Sortie"
        nature = deviner_nature(categorie)
        lignes.append((categorie, montant, type_, nature))
    return lignes


CATEGORIES_CANONIQUES = {
    "frais carte": (r"frais.*carte", r"carte.*frais", "commission carte"),
    "achats carte": ("paiement par carte", "paiements carte", "carte bancaire", "achat carte", "achats carte"),
    "frais bancaires": ("frais bancaire", "frais package", "commission", r"frais\b(?!.*(carte|retrait|devise))"),
    "frais retrait": ("frais retrait",),
    "frais devises": ("frais devise",),
    "virement": ("virement salarial", "virement à bénéficiaire", "virement"),
    "salaire": ("salaire", "salaires"),
    "alimentation": ("alimentation", "courses", "supermarché"),
    "transport": ("transport",),
    "services": ("services",),
}


def normaliser_categorie(categorie: str) -> str:
    """Regroupe les noms de catégories proches (ex : "Frais", "Frais
    carte", "Frais carte de crédit") sous un même nom — chaque groupe
    analysé séparément peut nommer légèrement différemment la même
    chose ; sans ça, l'addition ne les reconnaît pas comme identiques
    et le résultat final est éclaté en plein de petites lignes."""
    minuscule = categorie.lower().strip()
    for canonique, variantes in CATEGORIES_CANONIQUES.items():
        for variante in variantes:
            if re.search(variante, minuscule):
                return canonique.title()
    return categorie.strip()


def additionner_totaux(tous_les_csv: list) -> dict:
    """Combine plusieurs réponses CSV en additionnant les montants par
    catégorie — calcul Python déterministe, jamais une nouvelle demande
    à l'IA. Les noms de catégories proches sont regroupés avant
    addition (voir normaliser_categorie), puis un second passage
    regroupe les noms très similaires mais pas identiques au caractère
    près (ex : "ADOBE" et "Adobe Inc" sur deux mois différents) — sans
    ça, un même abonnement mensuel pourrait apparaître comme plusieurs
    petites lignes séparées au lieu de s'additionner correctement."""
    totaux = {}
    for texte_csv in tous_les_csv:
        for categorie, montant, type_, nature in parser_csv_groupe(texte_csv):
            categorie_normalisee = normaliser_categorie(categorie)
            cle = (categorie_normalisee, type_, nature)
            totaux[cle] = totaux.get(cle, 0) + montant
    return _fusionner_categories_proches(totaux)


def _fusionner_categories_proches(totaux: dict, seuil: float = 0.82) -> dict:
    """Deuxième passage : fusionne les catégories dont le nom se
    ressemble fortement (même type/nature), au cas où le même vendeur
    ou poste soit nommé un peu différemment d'un groupe à l'autre."""
    from difflib import SequenceMatcher

    cles = list(totaux.keys())
    fusionne = {}
    deja_traite = set()

    for i, cle_a in enumerate(cles):
        if cle_a in deja_traite:
            continue
        categorie_a, type_a, nature_a = cle_a
        montant_total = totaux[cle_a]
        deja_traite.add(cle_a)

        for cle_b in cles[i + 1:]:
            if cle_b in deja_traite:
                continue
            categorie_b, type_b, nature_b = cle_b
            if type_b != type_a or nature_b != nature_a:
                continue
            similarite = SequenceMatcher(None, categorie_a.lower(), categorie_b.lower()).ratio()
            inclusion = categorie_a.lower() in categorie_b.lower() or categorie_b.lower() in categorie_a.lower()
            if similarite >= seuil or (inclusion and min(len(categorie_a), len(categorie_b)) >= 4):
                montant_total += totaux[cle_b]
                deja_traite.add(cle_b)

        fusionne[(categorie_a, type_a, nature_a)] = montant_total

    return fusionne


def detecter_montants_suspects(totaux: dict) -> list:
    """Repère les montants qui semblent anormalement élevés par rapport
    au reste des données du même type — signale une probable erreur
    d'extraction (ex : un retrait mal lu depuis un PDF) plutôt que de
    corriger silencieusement un chiffre qu'on ne peut pas deviner."""
    suspects = []
    for (categorie, type_, nature), montant in totaux.items():
        autres = [m for (c, t, n), m in totaux.items() if t == type_ and c != categorie]
        if not autres:
            continue
        moyenne_autres = sum(autres) / len(autres)
        if moyenne_autres > 0 and montant > moyenne_autres * 8 and montant > 2000:
            suspects.append((categorie, montant))
    return suspects


def formater_totaux(totaux: dict) -> str:
    lignes = [f"{cat} ({type_}/{nature}) : {montant:.2f}" for (cat, type_, nature), montant in totaux.items()]
    return "\n".join(lignes) if lignes else "(aucune donnée exploitable trouvée)"


def generer_xlsx(totaux: dict, chemin_sortie: str):
    """Construit un vrai fichier Excel — avec de vraies formules
    (SUM, calculs), pas des chiffres figés. Si la personne modifie un
    montant ensuite dans Excel, les sous-totaux, la synthèse et les
    objectifs d'épargne se recalculent automatiquement, comme dans un
    vrai budget prévisionnel."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    entrees = sorted([(c, m) for (c, t, n), m in totaux.items() if t.lower() == "entree"], key=lambda x: -x[1])
    charges_fixes = sorted([(c, m) for (c, t, n), m in totaux.items() if t.lower() == "sortie" and n.lower() == "fixe"], key=lambda x: -x[1])
    charges_variables = sorted([(c, m) for (c, t, n), m in totaux.items() if t.lower() == "sortie" and n.lower() == "variable"], key=lambda x: -x[1])

    wb = Workbook()
    ws = wb.active
    ws.title = "Budget"

    POLICE = "Arial"
    GRAS_TITRE = Font(name=POLICE, size=13, bold=True)
    GRAS_SECTION = Font(name=POLICE, size=11, bold=True, color="FFFFFF")
    FOND_SECTION = PatternFill("solid", fgColor="4472C4")
    GRAS_TOTAL = Font(name=POLICE, bold=True)
    FOND_TOTAL = PatternFill("solid", fgColor="D9E1F2")
    POLICE_NORMALE = Font(name=POLICE)
    FORMAT_MONTANT = '#,##0.00 "€"'

    ws["A1"] = "BUDGET — Généré par Stanislas"
    ws["A1"].font = GRAS_TITRE
    ws.merge_cells("A1:B1")

    ligne = 3
    largeur_max = 10

    def ecrire_section(titre, postes):
        nonlocal ligne
        ws.cell(row=ligne, column=1, value=titre).font = GRAS_SECTION
        ws.cell(row=ligne, column=1).fill = FOND_SECTION
        ws.cell(row=ligne, column=2).fill = FOND_SECTION
        ligne += 1
        premiere_ligne_poste = ligne
        for categorie, montant in postes:
            ws.cell(row=ligne, column=1, value=categorie).font = POLICE_NORMALE
            cellule_montant = ws.cell(row=ligne, column=2, value=round(montant, 2))
            cellule_montant.font = Font(name=POLICE, color="0000FF")  # bleu = donnée modifiable
            cellule_montant.number_format = FORMAT_MONTANT
            largeur_max_local = len(categorie)
            ligne += 1
        derniere_ligne_poste = ligne - 1
        ws.cell(row=ligne, column=1, value=f"Total {titre.title()}").font = GRAS_TOTAL
        ws.cell(row=ligne, column=1).fill = FOND_TOTAL
        if derniere_ligne_poste >= premiere_ligne_poste:
            cellule_total = ws.cell(row=ligne, column=2, value=f"=SUM(B{premiere_ligne_poste}:B{derniere_ligne_poste})")
        else:
            cellule_total = ws.cell(row=ligne, column=2, value=0)
        cellule_total.font = GRAS_TOTAL
        cellule_total.fill = FOND_TOTAL
        cellule_total.number_format = FORMAT_MONTANT
        ligne_total = ligne
        ligne += 2
        return ligne_total

    ligne_total_entrees = ecrire_section("ENTREES", entrees)
    ligne_total_fixes = ecrire_section("CHARGES FIXES", charges_fixes)
    ligne_total_variables = ecrire_section("CHARGES VARIABLES", charges_variables)

    # Synthèse — tout en formules, référence aux totaux ci-dessus
    ws.cell(row=ligne, column=1, value="SYNTHESE").font = GRAS_SECTION
    ws.cell(row=ligne, column=1).fill = FOND_SECTION
    ws.cell(row=ligne, column=2).fill = FOND_SECTION
    ligne += 1
    ws.cell(row=ligne, column=1, value="Total Charges").font = POLICE_NORMALE
    c = ws.cell(row=ligne, column=2, value=f"=B{ligne_total_fixes}+B{ligne_total_variables}")
    c.number_format = FORMAT_MONTANT
    ligne_total_charges = ligne
    ligne += 1
    ws.cell(row=ligne, column=1, value="Solde").font = GRAS_TOTAL
    ws.cell(row=ligne, column=1).fill = FOND_TOTAL
    c = ws.cell(row=ligne, column=2, value=f"=B{ligne_total_entrees}-B{ligne_total_charges}")
    c.font = GRAS_TOTAL
    c.fill = FOND_TOTAL
    c.number_format = FORMAT_MONTANT
    ligne += 2

    # Épargne possible — objectif et économie en formules, liées aux
    # montants des charges variables juste au-dessus (si on change un
    # montant, l'objectif et l'économie se recalculent tout seuls)
    ws.cell(row=ligne, column=1, value="EPARGNE POSSIBLE (objectif -15% sur les charges variables)").font = GRAS_SECTION
    ws.cell(row=ligne, column=1).fill = FOND_SECTION
    for col in range(2, 5):
        ws.cell(row=ligne, column=col).fill = FOND_SECTION
    ligne += 1
    ws.cell(row=ligne, column=1, value="Categorie").font = GRAS_TOTAL
    ws.cell(row=ligne, column=2, value="Depense actuelle").font = GRAS_TOTAL
    ws.cell(row=ligne, column=3, value="Objectif (-15%)").font = GRAS_TOTAL
    ws.cell(row=ligne, column=4, value="Economie").font = GRAS_TOTAL
    ligne += 1
    premiere_ligne_epargne = ligne
    ligne_variables_debut = ligne_total_variables - len(charges_variables)
    for i, (categorie, montant) in enumerate(charges_variables):
        ligne_source = ligne_variables_debut + i
        ws.cell(row=ligne, column=1, value=categorie).font = POLICE_NORMALE
        c_actuel = ws.cell(row=ligne, column=2, value=f"=B{ligne_source}")
        c_actuel.number_format = FORMAT_MONTANT
        c_objectif = ws.cell(row=ligne, column=3, value=f"=B{ligne_source}*0.85")
        c_objectif.number_format = FORMAT_MONTANT
        c_economie = ws.cell(row=ligne, column=4, value=f"=B{ligne_source}-C{ligne}")
        c_economie.number_format = FORMAT_MONTANT
        ligne += 1
    derniere_ligne_epargne = ligne - 1
    ws.cell(row=ligne, column=1, value="Economie mensuelle totale possible").font = GRAS_TOTAL
    ws.cell(row=ligne, column=1).fill = FOND_TOTAL
    if derniere_ligne_epargne >= premiere_ligne_epargne:
        c_total_eco = ws.cell(row=ligne, column=4, value=f"=SUM(D{premiere_ligne_epargne}:D{derniere_ligne_epargne})")
    else:
        c_total_eco = ws.cell(row=ligne, column=4, value=0)
    c_total_eco.font = GRAS_TOTAL
    c_total_eco.fill = FOND_TOTAL
    c_total_eco.number_format = FORMAT_MONTANT

    ws.column_dimensions["A"].width = 38
    for col in "BCD":
        ws.column_dimensions[col].width = 16

    wb.save(chemin_sortie)


def totaux_vers_csv(totaux: dict) -> str:
    """Reproduit la structure du modèle fourni par l'utilisateur : des
    sections (Entrées, Charges Fixes, Charges Variables), chacune avec
    ses lignes puis un sous-total, une synthèse, et une vraie section
    d'épargne possible — pas juste un classement des dépenses passées,
    un vrai objectif chiffré pour la suite."""
    entrees = [(c, m) for (c, t, n), m in totaux.items() if t.lower() == "entree"]
    charges_fixes = [(c, m) for (c, t, n), m in totaux.items() if t.lower() == "sortie" and n.lower() == "fixe"]
    charges_variables = [(c, m) for (c, t, n), m in totaux.items() if t.lower() == "sortie" and n.lower() == "variable"]

    total_entrees = sum(m for _, m in entrees)
    total_charges_fixes = sum(m for _, m in charges_fixes)
    total_charges_variables = sum(m for _, m in charges_variables)
    total_charges = total_charges_fixes + total_charges_variables
    solde = total_entrees - total_charges

    lignes = ["Categorie,Montant"]

    lignes.append("ENTREES,")
    for cat, montant in sorted(entrees, key=lambda x: -x[1]):
        lignes.append(f"{cat},{montant:.2f}")
    lignes.append(f"Total Entrees,{total_entrees:.2f}")
    lignes.append(",")

    lignes.append("CHARGES FIXES,")
    for cat, montant in sorted(charges_fixes, key=lambda x: -x[1]):
        lignes.append(f"{cat},{montant:.2f}")
    lignes.append(f"Total Charges Fixes,{total_charges_fixes:.2f}")
    lignes.append(",")

    lignes.append("CHARGES VARIABLES,")
    for cat, montant in sorted(charges_variables, key=lambda x: -x[1]):
        lignes.append(f"{cat},{montant:.2f}")
    lignes.append(f"Total Charges Variables,{total_charges_variables:.2f}")
    lignes.append(",")

    lignes.append("SYNTHESE,")
    lignes.append(f"Total Charges,{total_charges:.2f}")
    lignes.append(f"Solde,{solde:.2f}")
    lignes.append(",")

    # Épargne possible : seules les charges variables sont réalistement
    # réductibles (les charges fixes, par définition, ne le sont pas
    # facilement) — objectif suggéré : 15% de réduction par poste, un
    # vrai chiffre actionnable, pas un conseil vague
    lignes.append("EPARGNE POSSIBLE (objectif -15% sur les charges variables),")
    lignes.append("Categorie,Depense actuelle,Objectif suggere,Economie possible")
    economie_totale = 0
    for cat, montant in sorted(charges_variables, key=lambda x: -x[1]):
        objectif = montant * 0.85
        economie = montant - objectif
        economie_totale += economie
        lignes.append(f"{cat},{montant:.2f},{objectif:.2f},{economie:.2f}")
    lignes.append(f"Total economie possible (mensuel),,,{economie_totale:.2f}")

    return "\n".join(lignes)


def _parser_totaux_texte(texte: str) -> dict:
    """Relit le texte 'Categorie (Type/Nature) : Montant' produit par
    formater_totaux(), pour retrouver les vrais chiffres déjà calculés."""
    totaux = {}
    for ligne in texte.split("\n"):
        m = re.match(r"^(.+?) \((\w+)/(\w+)\) : ([\d.]+)$", ligne.strip())
        if m:
            totaux[(m.group(1), m.group(2), m.group(3))] = float(m.group(4))
    return totaux


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERREUR] Aucune donnée fournie.")
        sys.exit(1)

    action = sys.argv[1]

    if action == "--decouper" and len(sys.argv) > 2:
        groupes = _decouper_en_groupes(sys.argv[2])
        print("---GROUPES---")
        print(SEPARATEUR_GROUPES.join(groupes))
        sys.exit(0)

    if action == "--additionner" and len(sys.argv) > 2:
        # Purement du calcul Python, aucun appel à l'IA ici
        tous_les_csv = sys.argv[2].split(SEPARATEUR_GROUPES)
        totaux = additionner_totaux(tous_les_csv)
        print("---TOTAUX---")
        print(formater_totaux(totaux))
        sys.exit(0)

    if ask is None:
        print("---RESULTAT---")
        print("(Analyse indisponible : module de langage local introuvable.)")
        sys.exit(0)

    if action == "--groupe" and len(sys.argv) > 2:
        resultat = ask(_prompt_groupe(sys.argv[2])).strip()
        print("---RESULTAT---")
        print(resultat)

    elif action == "--narratif" and len(sys.argv) > 2:
        totaux = _parser_totaux_texte(sys.argv[2])
        texte_detaille = totaux_vers_texte_detaille(totaux) if totaux else sys.argv[2]
        resultat = ask(_prompt_narratif(texte_detaille)).strip()

        suspects = detecter_montants_suspects(totaux) if totaux else []
        if suspects:
            liste = ", ".join(f"{cat} ({montant:.2f})" for cat, montant in suspects)
            resultat += (
                f"\n\n⚠️ Montant(s) anormalement élevé(s) détecté(s) par rapport au "
                f"reste des données : {liste}. Vérifie ces lignes — il peut s'agir "
                f"d'une erreur de lecture d'un document plutôt qu'une vraie dépense."
            )

        print("---RESULTAT---")
        print(resultat)

    elif action == "--csv" and len(sys.argv) > 2:
        # Reçoit maintenant directement des totaux déjà calculés (texte
        # "Categorie (Type/Nature) : Montant" par ligne) et les reformate
        # en CSV — calcul déterministe, pas d'appel IA nécessaire ici non plus
        totaux = _parser_totaux_texte(sys.argv[2])
        print("---CSV---")
        print(totaux_vers_csv(totaux))

    elif action == "--xlsx" and len(sys.argv) > 2:
        # Écrit directement le fichier (impossible de faire transiter du
        # binaire comme simple argument texte) — chemin horodaté auto-
        # construit dans Documents/Stanislas/Budget, même principe que
        # archiver_cli.py
        from datetime import datetime
        totaux = _parser_totaux_texte(sys.argv[2])
        dossier = os.path.expanduser(os.path.join("~", "Documents", "Stanislas", "Budget"))
        os.makedirs(dossier, exist_ok=True)
        horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
        chemin_sortie = os.path.join(dossier, f"{horodatage}.xlsx")
        generer_xlsx(totaux, chemin_sortie)
        print("---XLSX---")
        print(chemin_sortie)

    else:
        print("[ERREUR] Commande inconnue.")
        sys.exit(1)
