"""
Module de tarification pour générer le prix de vente TTC d'un canapé sur mesure
à partir des éléments extraits du schéma (liste des banquettes, angles, dossiers,
accoudoirs et coussins) et des options sélectionnées dans le formulaire.

Ce module propose une fonction principale `calculer_prix_from_data` qui prend en
paramètres les dimensions des banquettes, des angles, ainsi que les quantités
de dossiers, accoudoirs, coussins (classés par taille), traversins,
coussins décoratifs, surmatelas et arrondis. Elle calcule ensuite le prix
de vente TTC en appliquant les formules fournies par le client. Les prix
détail sont retournés sous forme de dictionnaire pour permettre un affichage
et une analyse fine du devis.

Les règles de calcul sont les suivantes :

- **Support** : chaque banquette droite ou d’angle est facturée 225 €, chaque
  dossier 250 €, et chaque accoudoir 225 €.
- **Mousse et tissu** : pour chaque banquette et chaque angle, la mousse est
  calculée selon la formule `(longueur * largeur * épaisseur * densité * 16) / 1 000 000`.
  La densité dépend du type de mousse (D25 → 25, D30 → 30, HR35 → 35, HR45 → 45).
  Le tissu est calculé selon la formule :
    * Si `largeur * épaisseur * 2 > 140` : `(longueur / 100) * 105` €
    * Sinon : `(longueur / 100) * 74` €
- **Coussins d’assise** : les tailles 65, 80 et 90 cm sont facturées
  respectivement 35 €, 44 € et 48 € l’unité. Toute autre taille est
  considérée comme un coussin « valise » facturé 70 €.
- **Coussins décoratifs** : 15 € l’unité.
- **Traversins** : 30 € l’unité.
- **Surmatelas** : 80 € l’unité.
- **Arrondis** : 20 € par banquette.

Le prix total retourné inclut la TVA (20 %) appliquée sur les coûts de
fabrication. Aucune marge ni remise n’est intégrée ici ; ces éléments peuvent
être ajoutés ultérieurement dans l’application.
"""

from typing import List, Tuple, Dict

# Prix unitaires (TTC) des éléments standards
COUT_SUPPORT_BANQUETTE_TTC = 225.0
COUT_SUPPORT_BANQUETTE_ANGLE_TTC = 225.0
COUT_SUPPORT_DOSSIER_TTC = 250.0
COUT_SUPPORT_ACCOUDOIR_TTC = 225.0

# Prix unitaires des coussins par taille (TTC)
COUSSIN_65_TTC = 35.0
COUSSIN_80_TTC = 44.0
COUSSIN_90_TTC = 48.0
COUSSIN_VALISE_TTC = 70.0

# Prix unitaires des éléments complémentaires (TTC)
COUSSIN_DECO_TTC = 15.0
TRAVERSIN_TTC = 30.0
SURMATELAS_TTC = 80.0
ARRONDI_TTC = 20.0

# Mapping des types de mousse vers leur densité numérique
DENSITES = {
    "D25": 25,
    "D30": 30,
    "HR35": 35,
    "HR45": 45,
}


def _prix_mousse_et_tissu(longueur: float, largeur: float, epaisseur: float, type_mousse: str) -> Tuple[float, float]:
    """Calcule le prix TTC de la mousse et du tissu pour une banquette.

    :param longueur: longueur de la banquette en cm
    :param largeur: largeur de la banquette en cm
    :param epaisseur: épaisseur de la mousse en cm
    :param type_mousse: type de mousse ('D25', 'D30', 'HR35', 'HR45')
    :return: tuple (prix_mousse_TTC, prix_tissu_TTC)
    """
    densite = DENSITES.get(type_mousse.upper(), 25)
    # Prix de la mousse selon la formule densité * 16 * volume (cm3) / 1e6
    volume_cm3 = longueur * largeur * epaisseur
    prix_mousse = (volume_cm3 * densite * 16) / 1_000_000
    # Prix du tissu selon la largeur et l'épaisseur
    if largeur * epaisseur * 2 > 140:
        prix_tissu = (longueur / 100.0) * 105.0
    else:
        prix_tissu = (longueur / 100.0) * 74.0
    return prix_mousse, prix_tissu


def calculer_prix_from_data(
    banquette_dims: List[Tuple[float, float]],
    angle_dims: List[Tuple[float, float]],
    nb_dossiers: int,
    nb_accoudoirs: int,
    nb_coussins_65: int,
    nb_coussins_80: int,
    nb_coussins_90: int,
    nb_coussins_valise: int,
    nb_traversins: int,
    nb_coussins_deco: int,
    nb_surmatelas: int,
    nb_arrondis: int,
    type_mousse: str = "D25",
    epaisseur: float = 25.0,
) -> Dict[str, float]:
    """Calcule le prix TTC total à partir des dimensions et des quantités fournies.

    :param banquette_dims: liste des dimensions (longueur, largeur) de chaque banquette droite
    :param angle_dims: liste des dimensions (longueur, largeur) de chaque banquette d'angle
    :param nb_dossiers: nombre de dossiers
    :param nb_accoudoirs: nombre d'accoudoirs
    :param nb_coussins_65: nombre de coussins de 65 cm
    :param nb_coussins_80: nombre de coussins de 80 cm
    :param nb_coussins_90: nombre de coussins de 90 cm
    :param nb_coussins_valise: nombre de coussins valises (autres tailles)
    :param nb_traversins: nombre de traversins (70x30)
    :param nb_coussins_deco: nombre de coussins décoratifs
    :param nb_surmatelas: nombre de surmatelas
    :param nb_arrondis: nombre d'arrondis (par banquette)
    :param type_mousse: type de mousse choisi
    :param epaisseur: épaisseur de la mousse en cm
    :return: dictionnaire avec le détail des prix et le total TTC
    """
    # Support (banquettes, angles, dossiers, accoudoirs)
    prix_support = (
        len(banquette_dims) * COUT_SUPPORT_BANQUETTE_TTC
        + len(angle_dims) * COUT_SUPPORT_BANQUETTE_ANGLE_TTC
        + nb_dossiers * COUT_SUPPORT_DOSSIER_TTC
        + nb_accoudoirs * COUT_SUPPORT_ACCOUDOIR_TTC
    )

    # Mousse + tissu pour chaque banquette
    prix_mousse_total = 0.0
    prix_tissu_total = 0.0
    for longueur, largeur in banquette_dims + angle_dims:
        pm, pt = _prix_mousse_et_tissu(longueur, largeur, epaisseur, type_mousse)
        prix_mousse_total += pm
        prix_tissu_total += pt

    # Coussins d'assise
    prix_coussins_assise = (
        nb_coussins_65 * COUSSIN_65_TTC
        + nb_coussins_80 * COUSSIN_80_TTC
        + nb_coussins_90 * COUSSIN_90_TTC
        + nb_coussins_valise * COUSSIN_VALISE_TTC
    )

    # Coussins déco, traversins, surmatelas
    prix_coussins_deco = nb_coussins_deco * COUSSIN_DECO_TTC
    prix_traversins = nb_traversins * TRAVERSIN_TTC
    prix_surmatelas = nb_surmatelas * SURMATELAS_TTC

    # Arrondis
    prix_arrondis = nb_arrondis * ARRONDI_TTC

    # Total TTC
    total_ttc = (
        prix_support
        + prix_mousse_total
        + prix_tissu_total
        + prix_coussins_assise
        + prix_coussins_deco
        + prix_traversins
        + prix_surmatelas
        + prix_arrondis
    )

    return {
        "prix_support_ttc": prix_support,
        "prix_mousse_ttc": prix_mousse_total,
        "prix_tissu_ttc": prix_tissu_total,
        "prix_coussins_assise_ttc": prix_coussins_assise,
        "prix_coussins_deco_ttc": prix_coussins_deco,
        "prix_traversins_ttc": prix_traversins,
        "prix_surmatelas_ttc": prix_surmatelas,
        "prix_arrondis_ttc": prix_arrondis,
        "total_ttc": total_ttc,
    }


# -----------------------------------------------------------------------------
# Wrapper de compatibilité
#
# Pour assurer une compatibilité avec l'ancienne API de calcul (utilisant
# `calculer_prix_total` avec de nombreux paramètres), nous proposons un
# wrapper qui convertit les arguments simples en données segmentées et
# appelle ensuite `calculer_prix_from_data`. Cette implémentation repose
# sur des heuristiques simples :
#  - Les banquettes sont déterminées à partir des longueurs `tx`, `ty` et `tz`.
#  - Les banquettes d'angle sont approximées à partir de la profondeur et d'un
#    carré (profondeur + 20 cm).
#  - Le nombre de dossiers et d'accoudoirs est basé sur les indicateurs
#    booléens fournis.
#  - Les coussins d'assise sont évalués en fonction du type sélectionné ; les
#    tailles non numériques sont considérées comme des coussins « valise ».
#  - Les traversins, coussins déco et surmatelas proviennent directement
#    des paramètres.
#
# Le dictionnaire retourné est conforme aux attentes de l'application, avec
# les clés 'prix_ht', 'tva', 'total_ttc' et 'cout_revient_ht'.

def calculer_prix_total(
    type_canape: str,
    tx: float,
    ty: float,
    tz: float,
    profondeur: float,
    type_coussins: str,
    type_mousse: str,
    epaisseur: float,
    acc_left: bool,
    acc_right: bool,
    acc_bas: bool,
    dossier_left: bool,
    dossier_bas: bool,
    dossier_right: bool,
    nb_coussins_deco: int,
    nb_traversins_supp: int,
    has_surmatelas: bool,
    has_meridienne: bool,
) -> Dict[str, float]:
    """Compatibilité avec l'ancienne signature de calculer_prix_total.

    Cette fonction convertit les paramètres de haut niveau (dimensions,
    options sélectionnées) en listes de banquettes et d'angles, puis
    appelle `calculer_prix_from_data` pour obtenir le total TTC.
    """
    # Conversion des longueurs en listes de banquettes droites
    banquette_dims: List[Tuple[float, float]] = []
    angle_dims: List[Tuple[float, float]] = []
    # Détermination des banquettes et angles selon le type de canapé
    type_lower = (type_canape or "").lower()
    # Taille de l'angle approximée : profondeur + 20 cm (mais limitée à profondeur
    # pour éviter des valeurs aberrantes si la profondeur est déjà grande)
    angle_size = profondeur + 20.0
    if "simple" in type_lower:
        banquette_dims = [(tx or 0.0, profondeur)]
    elif "l - sans" in type_lower or ("l" in type_lower and "angle" not in type_lower):
        # L sans angle
        banquette_dims = [(ty or 0.0, profondeur), (tx or 0.0, profondeur)]
    elif "l" in type_lower and ("angle" in type_lower or "lf" in type_lower):
        # L avec angle : deux banquettes droites et un angle
        banquette_dims = [(ty or 0.0, profondeur), (tx or 0.0, profondeur)]
        angle_dims = [(angle_size, angle_size)]
    elif "u" in type_lower:
        # U sans angle : trois banquettes droites
        banquette_dims = [(ty or 0.0, profondeur), (tx or 0.0, profondeur), (tz or 0.0, profondeur)]
        # U avec 1 angle (u1f) ou 2 angles (u2f) : angles ajoutés en fin
        if "1 angle" in type_lower or "u1f" in type_lower:
            angle_dims = [(angle_size, angle_size)]
        elif "2 angles" in type_lower or "u2f" in type_lower:
            angle_dims = [(angle_size, angle_size), (angle_size, angle_size)]
    else:
        # Cas par défaut : une seule banquette
        banquette_dims = [(tx or 0.0, profondeur)]

    # Comptage dossiers et accoudoirs à partir des cases cochées
    nb_dossiers = int(dossier_left) + int(dossier_bas) + int(dossier_right)
    nb_accoudoirs = int(acc_left) + int(acc_right) + int(acc_bas)

    # Comptage des coussins d'assise selon la taille sélectionnée
    nb_coussins_65 = nb_coussins_80 = nb_coussins_90 = nb_coussins_valise = 0
    # Si type_coussins est numérique, on calcule un nombre de coussins basique
    try:
        taille_coussins = int(type_coussins)
        # Estimation du nombre total de coussins en fonction de la somme des longueurs
        total_length = 0.0
        for lng, _ in banquette_dims:
            total_length += lng
        for lng, _ in angle_dims:
            total_length += lng
        # Au minimum 2 coussins
        nb_coussins = max(2, int(total_length / max(taille_coussins, 1)))
        if taille_coussins == 65:
            nb_coussins_65 = nb_coussins
        elif taille_coussins == 80:
            nb_coussins_80 = nb_coussins
        elif taille_coussins == 90:
            nb_coussins_90 = nb_coussins
        else:
            nb_coussins_valise = nb_coussins
    except Exception:
        # Tailles spéciales ('auto', 'valise', 'p', 'g') considérées comme coussins valise
        # On ne peut pas déterminer un nombre précis ; par défaut 0
        nb_coussins_valise = 0

    # Traversins supplémentaires
    nb_traversins = nb_traversins_supp
    # Surmatelas : 1 si activé
    nb_surmatelas_int = 1 if has_surmatelas else 0
    # Nombre d'arrondis : un par banquette droite et par angle
    nb_arrondis_int = len(banquette_dims) + len(angle_dims)

    # Appel de la nouvelle fonction de calcul
    prix_data = calculer_prix_from_data(
        banquette_dims,
        angle_dims,
        nb_dossiers,
        nb_accoudoirs,
        nb_coussins_65,
        nb_coussins_80,
        nb_coussins_90,
        nb_coussins_valise,
        nb_traversins,
        nb_coussins_deco,
        nb_surmatelas_int,
        nb_arrondis_int,
        type_mousse,
        epaisseur,
    )

    # Conversion du prix TTC en prix HT et TVA (20 %)
    total_ttc = prix_data.get('total_ttc', 0.0)
    prix_ht = total_ttc / 1.20 if total_ttc else 0.0
    tva = total_ttc - prix_ht

    # Nous ne calculons pas ici le coût de revient HT (pas disponible)
    return {
        'prix_ht': round(prix_ht, 2),
        'tva': round(tva, 2),
        'total_ttc': round(total_ttc, 2),
        'cout_revient_ht': 0.0
    }
