# -*- coding: utf-8 -*-
"""
Module de pricing adapté pour app.py
Basé sur pricing-2.py avec ajustements pour traiter l'angle comme une banquette supplémentaire
et exposer les fonctions de calcul utilisées par l'application Streamlit.
"""

# ==========================================================================
# CONSTANTES DE PRIX
# ==========================================================================

# Prix de vente TTC
PRIX_TTC = {
    'coussins': {
        65: 35,
        80: 44,
        90: 48,
        'valise': 70,
        'auto': 0  # Calculé selon la taille optimale
    },
    'supports': {
        # Prix de vente TTC
        # Banquette et banquette d'angle sont toutes deux facturées 225€ l'unité selon le cahier des charges.
        'banquette': 225,
        'banquette_angle': 225,
        'accoudoir': 225,
        'dossier': 250
    },
    'accessoires': {
        'coussin_deco': 15,
        'traversin': 30,
        'surmatelas': 80
    }
}

# Coefficients mousse TTC
COEF_MOUSSE_TTC = {
    'D25': 16 * 25,
    'D30': 16 * 30,
    # HR35 utilise un coefficient 35 au lieu de 37 pour correspondre au calcul souhaité (16*35)
    'HR35': 16 * 35,
    'HR45': 16 * 47
}

# Prix tissu TTC
PRIX_TISSU_PETIT_TTC = 74   # Si largeur + épaisseur*2 <= 140cm
PRIX_TISSU_GRAND_TTC = 105  # Si largeur + épaisseur*2 > 140cm

# Coûts de revient HT (ce qu'on appelait "marge" avant)
COUT_REVIENT_HT = {
    'coussins': {
        65: 14,
        80: 17,
        90: 17.5,
        'valise': 25
    },
    'supports': {
        'banquette': 113,      # <= 200cm
        'banquette_long': 121,  # > 200cm
        'banquette_angle': 104.2,
        'accoudoir': 73,
        'dossier': 155.2,      # <= 200cm
        'dossier_long': 176    # > 200cm
    },
    'accessoires': {
        'coussin_deco': 9.5,
        'traversin': 11.6,
        'surmatelas': 31
    },
    'arrondis': 6.05
}

# Coefficients mousse coût HT
COEF_MOUSSE_COUT_HT = {
    'D25': 157.5,
    'D30': 188,
    'HR35': 192,
    'HR45': 245
}

# Prix tissu coût HT
PRIX_TISSU_PETIT_COUT_HT = 11.2
PRIX_TISSU_GRAND_COUT_HT = 16.16
SUPPLEMENT_TISSU_COUT_HT = 15

# ==========================================================================
# FONCTIONS DE CALCUL
# ==========================================================================

def calculer_prix_mousse_tissu_ttc(longueur, largeur, epaisseur, type_mousse):
    """Calcule le prix TTC mousse + tissu pour une banquette"""
    volume_m3 = (longueur * largeur * epaisseur) / 1000000
    coef = COEF_MOUSSE_TTC.get(type_mousse, COEF_MOUSSE_TTC['D25'])
    prix_mousse = volume_m3 * coef
    condition = largeur + (epaisseur * 2)
    if condition > 140:
        prix_tissu = (longueur / 100) * PRIX_TISSU_GRAND_TTC
    else:
        prix_tissu = (longueur / 100) * PRIX_TISSU_PETIT_TTC
    return prix_mousse + prix_tissu

def calculer_cout_mousse_tissu_ht(longueur, largeur, epaisseur, type_mousse):
    """Calcule le coût de revient HT mousse + tissu pour une banquette"""
    volume_m3 = (longueur * largeur * epaisseur) / 1000000
    coef = COEF_MOUSSE_COUT_HT.get(type_mousse, COEF_MOUSSE_COUT_HT['D25'])
    cout_mousse = volume_m3 * coef
    condition = 2 + largeur + (epaisseur * 2)
    if condition <= 140:
        cout_tissu = ((longueur / 100) * PRIX_TISSU_PETIT_COUT_HT) + SUPPLEMENT_TISSU_COUT_HT
    else:
        cout_tissu = ((longueur / 100) * PRIX_TISSU_GRAND_COUT_HT) + SUPPLEMENT_TISSU_COUT_HT
    return cout_mousse + cout_tissu

def estimer_nombre_banquettes(type_canape, tx, ty, tz):
    """Estime le nombre de banquettes selon le type de canapé"""
    if "Simple" in type_canape:
        return 1
    elif "L" in type_canape:
        # pour les canapés en L avec angle, on considère 3 banquettes
        if "Angle" in type_canape or "LF" in type_canape:
            return 3
        return 2
    elif "U" in type_canape:
        return 3
    return 1

def estimer_nombre_coussins(type_canape, tx, ty, tz, profondeur, type_coussins):
    """Estime le nombre et la taille des coussins"""
    # Estimation basique - sera plus précise avec le wrapper canapefullv77
    if type_coussins == "auto":
        largeur_totale = tx
        if "L" in type_canape or "U" in type_canape:
            largeur_totale += (ty if ty else 0)
        if "U" in type_canape and tz:
            largeur_totale += tz
        # Estimation de la taille optimale
        if largeur_totale < 200:
            taille = 65
        elif largeur_totale < 350:
            taille = 80
        else:
            taille = 90
        nb_coussins = max(2, int(largeur_totale / taille))
        return nb_coussins, taille
    else:
        # Type fixe spécifié : calculer le nombre de coussins par section de banquette
        try:
            taille = int(type_coussins)
        except Exception:
            taille = 80
        import math
        # Déterminer la longueur utile de chaque banquette pour placer des coussins
        bench_lengths = []
        type_lower = type_canape.lower()
        if "simple" in type_lower:
            bench_lengths = [tx]
        elif "l" in type_lower:
            bench_lengths = [tx]
            if ty:
                bench_lengths.append(max(0, ty - profondeur))
        elif "u" in type_lower:
            bench_lengths = [tx]
            if ty:
                bench_lengths.append(max(0, ty - profondeur))
            if tz:
                bench_lengths.append(max(0, tz - profondeur))
        else:
            bench_lengths = [tx]
        nb_coussins = 0
        for lng in bench_lengths:
            try:
                count = math.floor(lng / taille)
                if count < 1:
                    count = 1
            except Exception:
                count = 1
            nb_coussins += count
        if nb_coussins < 2:
            nb_coussins = 2
        return nb_coussins, taille

def calculer_prix_total(type_canape, tx, ty, tz, profondeur,
                        type_coussins, type_mousse, epaisseur,
                        acc_left, acc_right, acc_bas,
                        dossier_left, dossier_bas, dossier_right,
                        nb_coussins_deco, nb_traversins_supp,
                        has_surmatelas, has_meridienne):
    """
    Calcule le prix total TTC et le coût de revient HT.
    Traite l'angle comme une banquette supplémentaire pour les modèles en L avec angle.

    Returns:
        dict avec tous les détails + la marge réelle
    """
    details = {}
    prix_ttc_total = 0
    cout_revient_ht_total = 0
    # ======================================================================
    # BANQUETTES (Mousse + Tissu + Support)
    # ======================================================================
    prix_banquettes_ttc = 0
    cout_banquettes_ht = 0
    # Normaliser le type de canapé
    type_lower = type_canape.lower() if isinstance(type_canape, str) else ""
    banquettes_dims = []
    angle_dims = []
    segmentation_used = False
    try:
        import importlib
        canape_mod = importlib.import_module("canapfullv81matplot")
        # Gestion spécifique des canapés en L avec angle (LF)
        if "lf" in type_lower:
            # Calcul des points et des polygones du schéma
            pts = canape_mod.compute_points_LF_variant(
                tx,
                ty,
                profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                acc_left=acc_left,
                acc_bas=acc_bas,
                meridienne_side=None,
                meridienne_len=0,
            )
            polys = canape_mod.build_polys_LF_variant(
                pts,
                tx,
                ty,
                profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                acc_left=acc_left,
                acc_bas=acc_bas,
                meridienne_side=None,
                meridienne_len=0,
            )
            # Récupérer les dimensions de chaque assise (banquettes) et de l'angle
            banquettes_dims = [
                canape_mod.banquette_dims(poly) for poly in polys.get("banquettes", [])
            ]
            angle_dims = [
                canape_mod.banquette_dims(poly) for poly in polys.get("angle", [])
            ]
            # Déterminer le nombre de dossiers en utilisant la fonction pondérée
            # et en tenant compte des scissions (split_flags)
            dossiers_count = canape_mod._compute_dossiers_count(polys)
            split_flags = polys.get("split_flags", {})
            add_split = int(split_flags.get("left", False) and dossier_left) + int(
                split_flags.get("bottom", False) and dossier_bas
            )
            seg_nb_dossiers = int(round(dossiers_count)) + add_split
            # Nombre d'accoudoirs : chaque polygone d'accoudoir représente un accoudoir
            seg_nb_accoudoirs = len(polys.get("accoudoirs", []))
            # Conserver les points pour l'estimation des coussins auto
            seg_pts = pts
            segmentation_used = True
    except Exception:
        segmentation_used = False
    if not segmentation_used:
        nb_banquettes = estimer_nombre_banquettes(type_canape, tx, ty, tz)
        if "simple" in type_lower:
            banquettes_dims = [(tx, profondeur)]
        elif "l" in type_lower:
            if "angle" in type_lower or "lf" in type_lower:
                banquettes_dims = [
                    (tx, profondeur),
                    (ty if ty else profondeur, profondeur),
                ]
                angle_dims = [(profondeur + 20, profondeur + 20)]
            else:
                banquettes_dims = [(tx, profondeur), (ty if ty else 150, profondeur)]
        elif "u" in type_lower:
            banquettes_dims = [
                (tx, profondeur),
                (ty if ty else 150, profondeur),
                (tz if tz else 150, profondeur),
            ]
        else:
            banquettes_dims = [(tx, profondeur)]
    # Mousse + tissu + support pour banquettes hors angle
    for longueur, largeur in banquettes_dims:
        prix_mt = calculer_prix_mousse_tissu_ttc(longueur, largeur, epaisseur, type_mousse)
        prix_banquettes_ttc += prix_mt
        cout_mt = calculer_cout_mousse_tissu_ht(longueur, largeur, epaisseur, type_mousse)
        cout_banquettes_ht += cout_mt
        prix_banquettes_ttc += PRIX_TTC['supports']['banquette']
        if longueur <= 200:
            cout_banquettes_ht += COUT_REVIENT_HT['supports']['banquette']
        else:
            cout_banquettes_ht += COUT_REVIENT_HT['supports']['banquette_long']
    # Mousse + tissu + support pour banquettes d'angle
    for longueur, largeur in angle_dims:
        prix_mt = calculer_prix_mousse_tissu_ttc(longueur, largeur, epaisseur, type_mousse)
        prix_banquettes_ttc += prix_mt
        cout_mt = calculer_cout_mousse_tissu_ht(longueur, largeur, epaisseur, type_mousse)
        cout_banquettes_ht += cout_mt
        prix_banquettes_ttc += PRIX_TTC['supports']['banquette_angle']
        cout_banquettes_ht += COUT_REVIENT_HT['supports']['banquette_angle']
    nb_banquettes_effectif = len(banquettes_dims) + len(angle_dims)
    details['Banquettes (mousse + tissu + support)'] = round(prix_banquettes_ttc, 2)
    prix_ttc_total += prix_banquettes_ttc
    cout_revient_ht_total += cout_banquettes_ht
    # ======================================================================
    # DOSSIERS
    # ======================================================================
    nb_dossiers = 0
    if 'seg_nb_dossiers' in locals():
        nb_dossiers = seg_nb_dossiers
    else:
        if dossier_left:
            nb_dossiers += 1
        if dossier_bas:
            nb_dossiers += 1
        if dossier_right:
            nb_dossiers += 1
        if ("angle" in type_lower or "lf" in type_lower or "u" in type_lower) and nb_dossiers < nb_banquettes_effectif:
            nb_dossiers = nb_banquettes_effectif
    prix_dossiers_ttc = nb_dossiers * PRIX_TTC['supports']['dossier']
    details['Dossiers'] = prix_dossiers_ttc
    prix_ttc_total += prix_dossiers_ttc
    cout_dossiers_ht = nb_dossiers * COUT_REVIENT_HT['supports']['dossier']
    cout_revient_ht_total += cout_dossiers_ht
    # ======================================================================
    # ACCOUDOIRS
    # ======================================================================
    nb_accoudoirs = 0
    if 'seg_nb_accoudoirs' in locals():
        nb_accoudoirs = seg_nb_accoudoirs
    else:
        if acc_left:
            nb_accoudoirs += 1
        if acc_right:
            nb_accoudoirs += 1
        if acc_bas:
            nb_accoudoirs += 1
    prix_accoudoirs_ttc = nb_accoudoirs * PRIX_TTC['supports']['accoudoir']
    details['Accoudoirs'] = prix_accoudoirs_ttc
    prix_ttc_total += prix_accoudoirs_ttc
    cout_accoudoirs_ht = nb_accoudoirs * COUT_REVIENT_HT['supports']['accoudoir']
    cout_revient_ht_total += cout_accoudoirs_ht
    # ======================================================================
    # COUSSINS
    # ======================================================================
    # Détermination du nombre et de la taille des coussins d'assise. Si
    # ``segmentation_used`` est vrai, on calcule la longueur utile de
    # chaque banquette et on divise par la taille de coussin. Sinon on
    # retombe sur l'estimation heuristique. Si la taille n'est pas 65,
    # 80 ou 90 cm, les coussins sont considérés comme des valises.
    nb_coussins = 0
    taille_coussin = None
    coussins_valise = False
    # Convertir le type de coussin en chaîne (si None)
    if not type_coussins:
        type_coussins = "auto"
    # Choix de la taille
    if isinstance(type_coussins, str) and type_coussins.strip().lower() == "auto":
        if segmentation_used and 'seg_pts' in locals():
            # Pour l'automatique, s'appuyer sur le schéma pour choisir la taille optimale
            try:
                taille_auto = canape_mod._choose_cushion_size_auto(seg_pts, tx, ty, None, 0, traversins=None)
                taille_coussin = taille_auto
            except Exception:
                # Fallback sur une estimation basique
                longueur_totale = tx
                if "l" in type_lower or "u" in type_lower:
                    longueur_totale += (ty or 0)
                if "u" in type_lower:
                    longueur_totale += (tz or 0)
                if longueur_totale < 200:
                    taille_coussin = 65
                elif longueur_totale < 350:
                    taille_coussin = 80
                else:
                    taille_coussin = 90
        else:
            # Estimation simple de la taille optimale en fonction de la longueur totale
            longueur_totale = tx
            if "l" in type_lower or "u" in type_lower:
                longueur_totale += (ty or 0)
            if "u" in type_lower:
                longueur_totale += (tz or 0)
            if longueur_totale < 200:
                taille_coussin = 65
            elif longueur_totale < 350:
                taille_coussin = 80
            else:
                taille_coussin = 90
    else:
        # Taille fixe spécifiée
        try:
            taille_coussin = int(type_coussins)
        except Exception:
            taille_coussin = 80
    # Les tailles non standard sont considérées comme valises
    if taille_coussin not in (65, 80, 90):
        coussins_valise = True
    # Calcul du nombre de coussins
    if segmentation_used:
        # Utiliser la longueur utile de chaque banquette (hors angle) pour la répartition des coussins
        utile_lengths = []
        for (L, P) in banquettes_dims:
            if L >= P:
                utile = L
            else:
                utile = max(0.0, L - profondeur)
            utile_lengths.append(utile)
        nb_coussins = 0
        for lng in utile_lengths:
            if taille_coussin > 0:
                nb_coussins += max(1, int(math.floor(lng / taille_coussin)))
            else:
                nb_coussins += 1
        if nb_coussins < 2:
            nb_coussins = 2
    else:
        # Heuristique d'estimation (basée sur la somme des longueurs)
        nb_coussins, _ = estimer_nombre_coussins(type_canape, tx, ty, tz, profondeur, taille_coussin)
    # Ajustement pour la méridienne
    if has_meridienne:
        nb_coussins = max(1, nb_coussins - 1)
    # Application des prix
    if coussins_valise:
        prix_unitaire_coussin = PRIX_TTC['coussins']['valise']
        cout_unitaire_coussin = COUT_REVIENT_HT['coussins']['valise']
        coussin_label = f'Coussins valise (×{nb_coussins})'
    else:
        prix_unitaire_coussin = PRIX_TTC['coussins'].get(taille_coussin, PRIX_TTC['coussins'][80])
        cout_unitaire_coussin = COUT_REVIENT_HT['coussins'].get(taille_coussin, COUT_REVIENT_HT['coussins'][80])
        coussin_label = f'Coussins {taille_coussin}cm (×{nb_coussins})'
    prix_coussins_ttc = nb_coussins * prix_unitaire_coussin
    details[coussin_label] = prix_coussins_ttc
    prix_ttc_total += prix_coussins_ttc
    cout_coussins_ht = nb_coussins * cout_unitaire_coussin
    cout_revient_ht_total += cout_coussins_ht
    # ======================================================================
    # ACCESSOIRES
    # ======================================================================
    if nb_coussins_deco > 0:
        prix_deco = nb_coussins_deco * PRIX_TTC['accessoires']['coussin_deco']
        details[f'Coussins déco (×{nb_coussins_deco})'] = prix_deco
        prix_ttc_total += prix_deco
        cout_deco = nb_coussins_deco * COUT_REVIENT_HT['accessoires']['coussin_deco']
        cout_revient_ht_total += cout_deco
    if nb_traversins_supp > 0:
        prix_trav = nb_traversins_supp * PRIX_TTC['accessoires']['traversin']
        details[f'Traversins (×{nb_traversins_supp})'] = prix_trav
        prix_ttc_total += prix_trav
        cout_trav = nb_traversins_supp * COUT_REVIENT_HT['accessoires']['traversin']
        cout_revient_ht_total += cout_trav
    if has_surmatelas:
        prix_surmat = PRIX_TTC['accessoires']['surmatelas']
        details['Surmatelas'] = prix_surmat
        prix_ttc_total += prix_surmat
        cout_surmat = COUT_REVIENT_HT['accessoires']['surmatelas']
        cout_revient_ht_total += cout_surmat
    # ======================================================================
    # ARRONDIS (coût uniquement)
    # ======================================================================
    # Un coût d'arrondi est appliqué par banquette et par banquette d'angle
    nb_arrondis = len(banquettes_dims) + len(angle_dims)
    cout_revient_ht_total += nb_arrondis * COUT_REVIENT_HT['arrondis']
    # ======================================================================
    # CALCULS FINAUX
    # ======================================================================
    sous_total = prix_ttc_total / 1.2
    tva = prix_ttc_total - sous_total
    prix_ht = prix_ttc_total / 1.2
    marge_ht = prix_ht - cout_revient_ht_total
    taux_marge = (marge_ht / prix_ht * 100) if prix_ht > 0 else 0
    return {
        'details': details,
        'sous_total': round(sous_total, 2),
        'tva': round(tva, 2),
        'total_ttc': round(prix_ttc_total, 2),
        'prix_ht': round(prix_ht, 2),
        'cout_revient_ht': round(cout_revient_ht_total, 2),
        'marge_ht': round(marge_ht, 2),
        'taux_marge': round(taux_marge, 1),
        'nb_banquettes': nb_banquettes_effectif,
        'nb_dossiers': nb_dossiers,
        'nb_accoudoirs': nb_accoudoirs,
        'nb_coussins': nb_coussins,
        'taille_coussins': taille_coussin
    }

# ==========================================================================
# CLASSE POUR COMPATIBILITÉ AVEC NOUVEAU CODE
# ==========================================================================

class CanapePricing:
    """Classe de compatibilité pour le nouveau système"""
    def __init__(self):
        pass
    def calculer_devis_complet(self, configuration):
        """Méthode de compatibilité pour le nouveau système"""
        # Convertir la configuration en paramètres pour calculer_prix_total
        # Cette méthode sera utilisée si vous voulez migrer vers le nouveau système
        pass
