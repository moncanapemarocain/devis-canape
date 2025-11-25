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
