"""
Application Streamlit pour générer des devis de canapés sur mesure
Compatible Streamlit Cloud - Utilise canapematplot.py
"""

import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
from typing import Optional, Dict

# Palette de couleurs personnalisable pour le rendu du schéma.
# La clef "Transparent (par défaut)" correspond à une absence de remplissage
# (les rectangles seront transparents). Les autres entrées sont converties
# en codes hexadécimaux lors du rendu.
COLOR_PALETTE: Dict[str, Optional[str]] = {
    # La première entrée correspond à la sélection « Blanc » par défaut.  L'ancienne entrée
    # « Transparent (par défaut) » est conservée comme option mais n'est plus utilisée comme valeur par défaut.
    "Blanc": "#ffffff",
    "Transparent": None,
    "Beige": "#d8c4a8",
    "Beige clair": "#e6dac8",
    "Crème": "#f4f1e9",
    "Taupe": "#8B7E74",
    "Gris foncé": "#7d7d7d",
    "Gris clair": "#cfcfcf",
    "Marron clair": "#a1866f",
}

# Import des modules personnalisés
# Import du nouveau module de pricing (avec angle traité comme banquette)
from pricing import calculer_prix_total
from pdf_generator import generer_pdf_devis

# Import des fonctions de génération de schémas
from canapematplot import (
    render_LNF, render_LF_variant, render_U2f_variant,
    render_U, render_U1F_v1, render_U1F_v2, render_U1F_v3, render_U1F_v4,
    render_Simple1
)

# Configuration de la page
st.set_page_config(
    page_title="Configurateur Canapé Marocain",
    page_icon="🛋️",
    layout="wide"
)

# CSS personnalisé pour le design
st.markdown("""
<style>
    /* Fond principal */
    .stApp {
        background-color: #FBF6EF;
    }
    
    /* Titres */
    h1, h2, h3 {
        color: #372E2B !important;
    }

    p {
        color: #8C6F63 !important;
    }
    
    /* Onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #EDE7DE;
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #EDE7DE;
        color: #8C6F63;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FBF6EF !important;
        color: #8C6F63 !important;
        font-weight: 600;
    }
    
    /* Champs de saisie */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: #EDE7DE !important;
        color: #8C6F63 !important;
        border: 1px solid #D5CFC6 !important;
        border-radius: 8px !important;
    }
    
    .stTextInput label, .stNumberInput label, .stSelectbox label {
        color: #8C6F63 !important;
        font-weight: 500;
    }

    div.st-an {
        background-color : red 
    }
    
    /* Checkbox */
    .stCheckbox label {
        color: #8C6F63 !important;
    }

    div.st-emotion-cache-1q82h82.e1wr3kle3 {
        color: black;
    }
    
    /* Boutons normaux */
    .stButton button {
        background-color: #EDE7DE !important;
        color: #8C6F63 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #D5CFC6 !important;
        transform: translateY(-2px);
    }

    
    .stButton button[kind="primary"]:hover {
        background-color: #D5CFC6 !important;
    }
    
    /* Conteneurs */
    .stContainer {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Messages */
    .stSuccess {
        background-color: #D4EDDA !important;
        color: #155724 !important;
        border-radius: 8px;
    }
    
    .stError {
        background-color: #F8D7DA !important;
        color: #721C24 !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)
def generer_schema_canape(
    type_canape,
    tx,
    ty,
    tz,
    profondeur,
    acc_left,
    acc_right,
    acc_bas,
    dossier_left,
    dossier_bas,
    dossier_right,
    meridienne_side,
    meridienne_len,
    coussins="auto",
    nb_traversins_supp: int = 0,
    traversins_positions: list[str] | None = None,
    couleurs: Optional[Dict[str, Optional[str]]] = None,
) -> plt.Figure:
    """Génère le schéma du canapé.

    Parameters
    ----------
    type_canape : str
        Libellé du type de canapé (p. ex. "Simple (S)", "L - Sans Angle", etc.).
    tx, ty, tz : int or None
        Dimensions horizontales du canapé selon la configuration.
    profondeur : int
        Profondeur d'assise en centimètres.
    acc_left, acc_right, acc_bas : bool
        Indiquent la présence d'accoudoirs à gauche, à droite et en bas.
    dossier_left, dossier_bas, dossier_right : bool
        Indiquent la présence de dossiers sur les côtés.
    meridienne_side : str or None
        Côté de la méridienne ("g" ou "d"), ou None s'il n'y en a pas.
    meridienne_len : int
        Longueur de la méridienne en centimètres.
    coussins : str or int
        Mode d'optimisation des coussins ("auto", "65", "80", "80-90", "90", "valise", etc.).
    nb_traversins_supp : int, optional
        Nombre de traversins supplémentaires sélectionnés dans le formulaire. Si strictement positif,
        des traversins seront dessinés selon la géométrie du canapé.  Par défaut, aucun traversin
        n'est dessiné.

    Returns
    -------
    matplotlib.figure.Figure
        La figure générée représentant le canapé.
    """
    fig = plt.figure(figsize=(12, 8))

    try:
        # Initialiser la configuration des traversins uniquement si au moins un traversin
        # supplémentaire est demandé.  Cela permet d'afficher les traversins sur le schéma
        # uniquement lorsque l'utilisateur l'a explicitement indiqué dans le formulaire.
        traversins_cfg: str | None = None
        # Si l'utilisateur a sélectionné explicitement des positions pour les traversins,
        # on les utilise pour le schéma.  Les valeurs possibles en entrée sont des
        # libellés en français ("Gauche", "Droite", "Bas"); on les convertit en
        # codes attendus par canapematplot/canapefullv88 : g, d, b.
        if traversins_positions:
            mapping = {
                "gauche": "g",
                "droite": "d",
                "bas": "b",
                "Gauche": "g",
                "Droite": "d",
                "Bas": "b",
            }
            codes = []
            for pos in traversins_positions:
                key = pos.strip().lower()
                if key in mapping:
                    codes.append(mapping[key])
            # On trie et on supprime les doublons pour former la chaîne
            if codes:
                traversins_cfg = ",".join(sorted(set(codes)))
        elif nb_traversins_supp and nb_traversins_supp > 0:
            # Déterminer la configuration par défaut en fonction du type de canapé.
            if "Simple" in type_canape:
                traversins_cfg = "g,d"
            elif "L" in type_canape:
                traversins_cfg = "g,b"
            elif "U" in type_canape:
                traversins_cfg = "g,b,d"

        # Choisir la fonction de rendu appropriée en fonction du type de canapé.
        if "Simple" in type_canape:
            render_Simple1(
                tx=tx,
                profondeur=profondeur,
                dossier=dossier_bas,
                acc_left=acc_left,
                acc_right=acc_right,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len,
                coussins=coussins,
                traversins=traversins_cfg,
                couleurs=couleurs,
                window_title="Canapé Simple",
            )
        elif "L - Sans Angle" in type_canape:
            render_LNF(
                tx=tx,
                ty=ty,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                acc_left=acc_left,
                acc_bas=acc_bas,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len,
                coussins=coussins,
                traversins=traversins_cfg,
                variant="auto",
                couleurs=couleurs,
                window_title="Canapé L - Sans Angle",
            )
        elif "L - Avec Angle" in type_canape:
            render_LF_variant(
                tx=tx,
                ty=ty,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                acc_left=acc_left,
                acc_bas=acc_bas,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len,
                coussins=coussins,
                traversins=traversins_cfg,
                couleurs=couleurs,
                window_title="Canapé L - Avec Angle",
            )
        elif "U - Sans Angle" in type_canape:
            render_U(
                tx=tx,
                ty_left=ty,
                tz_right=tz,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                dossier_right=dossier_right,
                acc_left=acc_left,
                acc_bas=acc_bas,
                acc_right=acc_right,
                coussins=coussins,
                traversins=traversins_cfg,
                variant="auto",
                couleurs=couleurs,
                window_title="Canapé U - Sans Angle",
            )
        elif "U - 1 Angle" in type_canape:
            render_U1F_v1(
                tx=tx,
                ty=ty,
                tz=tz,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                dossier_right=dossier_right,
                acc_left=acc_left,
                acc_right=acc_right,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len,
                coussins=coussins,
                traversins=traversins_cfg,
                couleurs=couleurs,
                window_title="Canapé U - 1 Angle",
            )
        elif "U - 2 Angles" in type_canape:
            render_U2f_variant(
                tx=tx,
                ty_left=ty,
                tz_right=tz,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                dossier_right=dossier_right,
                acc_left=acc_left,
                acc_bas=acc_bas,
                acc_right=acc_right,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len,
                coussins=coussins,
                traversins=traversins_cfg,
                couleurs=couleurs,
                window_title="Canapé U - 2 Angles",
            )

        fig = plt.gcf()
        # Supprimer tout titre ou supertitre afin d'éviter l'affichage du nom de variante dans les exports
        try:
            fig.suptitle("")
        except Exception:
            pass
        return fig
    except Exception as e:
        plt.close()
        raise Exception(f"Erreur lors de la génération du schéma : {str(e)}")

# Initialiser les variables de session
if 'type_canape' not in st.session_state:
    st.session_state.type_canape = "Simple (S)"
if 'tx' not in st.session_state:
    st.session_state.tx = 280
if 'ty' not in st.session_state:
    st.session_state.ty = 250
if 'tz' not in st.session_state:
    st.session_state.tz = 250
if 'profondeur' not in st.session_state:
    st.session_state.profondeur = 70

# En-tête
st.title("Configurez votre canapé marocain personnalisé")
st.markdown("Créez votre canapé marocain personnalisé et obtenez un devis instantané")
st.markdown("---")

# Création des onglets avec la nouvelle structure :
# 1 : Type, 2 : Dimensions, 3 : Structure (anciennement Options),
# 4 : Coussins, 5 : Mousse (anciennement Matériaux), 6 : Client,
# 7 : Couleurs.
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Type", "Dimensions", "Structure", "Coussins", "Mousse", "Client", "Couleurs"
])

# Onglet 7 : Couleurs
with tab7:
    st.markdown("### Choix des couleurs du schéma")
    st.info(
        "Par défaut, la structure et les banquettes/mousses sont blanches, tandis que les coussins sont beige clair. "
        "Vous pouvez personnaliser ces couleurs ci‑dessous."
    )
    # Sélecteurs de couleur pour la structure (accoudoirs et dossiers)
    color_structure_choice = st.selectbox(
        "Couleur de la structure (accoudoirs et dossiers)",
        list(COLOR_PALETTE.keys()),
        index=list(COLOR_PALETTE.keys()).index("Blanc"),
        key="color_structure_choice",
        help="Choisissez la couleur des accoudoirs et des dossiers, ou laissez Transparent pour ne pas colorier ces éléments."
    )
    # Sélecteur pour la couleur des banquettes/mousses (assise)
    color_banquette_choice = st.selectbox(
        "Couleur des banquettes/mousses (assise)",
        list(COLOR_PALETTE.keys()),
        index=list(COLOR_PALETTE.keys()).index("Blanc"),
        key="color_banquette_choice",
        help="Choisissez la couleur des banquettes/mousses, ou laissez Transparent pour ne pas colorier ces éléments."
    )
    # Sélecteur pour la couleur des coussins
    color_coussins_choice = st.selectbox(
        "Couleur des coussins",
        list(COLOR_PALETTE.keys()),
        index=list(COLOR_PALETTE.keys()).index("Beige clair"),
        key="color_coussins_choice",
        help="Choisissez la couleur des coussins. Le choix par défaut est Beige clair."
    )

# ONGLET 1: TYPE
with tab1:
    st.markdown("### Sélectionnez le type de canapé")
    
    type_canape = st.selectbox(
        "Type de canapé",
        ["Simple (S)", "L - Sans Angle", "L - Avec Angle (LF)", 
         "U - Sans Angle", "U - 1 Angle (U1F)", "U - 2 Angles (U2F)"],
        key="type_canape"
    )

# ONGLET 2: DIMENSIONS
with tab2:
    st.markdown("### Dimensions du canapé (en cm)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if "Simple" in st.session_state.type_canape:
            tx = st.number_input("Largeur (Tx)", min_value=100, max_value=600, value=280, step=10, key="tx")
            ty = tz = None
        elif "L" in st.session_state.type_canape:
            tx = st.number_input("Largeur bas (Tx)", min_value=100, max_value=600, value=350, step=10, key="tx")
            ty = st.number_input("Hauteur gauche (Ty)", min_value=100, max_value=600, value=250, step=10, key="ty")
            tz = None
        else:  # U
            tx = st.number_input("Largeur bas (Tx)", min_value=100, max_value=600, value=450, step=10, key="tx")
            ty = st.number_input("Hauteur gauche (Ty)", min_value=100, max_value=600, value=300, step=10, key="ty")
            tz = st.number_input("Hauteur droite (Tz)", min_value=100, max_value=600, value=280, step=10, key="tz")
    
    with col2:
        profondeur = st.number_input("Profondeur d'assise", min_value=50, max_value=120, value=70, step=5, key="profondeur")

# ONGLET 3 : STRUCTURE
with tab3:
    st.markdown("### Composition de la structure")

    # Deux colonnes pour séparer accoudoirs/dossiers et méridienne
    col1, col2 = st.columns(2)

    # Colonne gauche : accoudoirs et dossiers
    with col1:
        st.markdown("**Accoudoirs**")
        # Gestion des accoudoirs selon le type de canapé :
        # Pour les canapés en U (U, U1F, U2F) : uniquement gauche et droite sont visibles et pré-cochés.
        # L'accoudoir bas n'est pas visible et n'est pas pris en compte dans le schéma/prix.
        if "U" in st.session_state.type_canape:
            # Dans le cas des canapés en U : seuls les accoudoirs gauche et droit sont disponibles
            acc_left = st.checkbox("Accoudoir Gauche", value=True)
            acc_right = st.checkbox("Accoudoir Droit", value=True)
            acc_bas = False
        elif "L" in st.session_state.type_canape:
            # Pour les canapés en L (avec ou sans angle) : on affiche uniquement l'accoudoir gauche et bas
            acc_left = st.checkbox("Accoudoir Gauche", value=True)
            # L'accoudoir droit n'est pas proposé pour les configurations en L
            acc_right = False
            acc_bas = st.checkbox("Accoudoir Bas", value=True)
        else:
            # Pour les canapés simples : accoudoirs gauche et droit visibles, pas d'accoudoir bas
            acc_left = st.checkbox("Accoudoir Gauche", value=True)
            acc_right = st.checkbox("Accoudoir Droit", value=True)
            acc_bas = False

        st.markdown("**Dossiers**")
        # Les dossiers sont conservés tels quels : Gauche et Droit visibles selon le type
        dossier_left = st.checkbox("Dossier Gauche", value=True) if "Simple" not in st.session_state.type_canape else False
        dossier_bas = st.checkbox("Dossier Bas", value=True)
        dossier_right = st.checkbox("Dossier Droit", value=True) if ("U" in st.session_state.type_canape) else False

    # Colonne droite : méridienne
    with col2:
        st.markdown("**Méridienne**")
        has_meridienne = st.checkbox("Ajouter une méridienne", value=False)

        if has_meridienne:
            meridienne_side = st.selectbox(
                "Position de la méridienne",
                ["left", "right"],
                format_func=lambda x: "Gauche" if x == "left" else "Droite"
            )
            # Par défaut, longueur 50cm si la méridienne est activée
            # Valeur par défaut 50 cm, et minimum 50 cm pour éviter une erreur StreamlitValueBelowMinError
            meridienne_len = st.number_input("Longueur (cm)", min_value=50, max_value=200, value=50, step=10)
        else:
            meridienne_side = "left"
            meridienne_len = 0

        # fin de la colonne méridienne

# ONGLET 4 : COUSSINS
with tab4:
    st.markdown("### Composition des coussins")
    
    # Les éléments liés aux coussins étaient auparavant dans les options ; ils sont déplacés ici.
    type_coussins = st.selectbox(
        "Type de coussins",
        ["auto", "65", "80", "90", "80-90", "valise", "g", "p"],
        help="Auto = optimisation automatique, 80-90 = optimisation par côté entre 80 et 90 cm;\nvalise/p/g = optimisation sur plage de tailles valise (p=petit, g=grand)."
    )

    nb_coussins_deco = st.number_input("Coussins décoratifs", min_value=0, max_value=10, value=0)
    nb_traversins_supp = st.number_input("Traversins supplémentaires", min_value=0, max_value=5, value=0)
    # Permettre à l'utilisateur de choisir l'emplacement des traversins lorsqu'il en ajoute.
    # On détermine les positions autorisées selon la forme du canapé :
    #  - Simple : gauche/droite
    #  - L (LF/LNF) : gauche/bas
    #  - U : gauche/droite/bas (le bas est parfois inopérant selon la variante)
    traversins_positions = []
    if nb_traversins_supp > 0:
        if "Simple" in st.session_state.type_canape:
            trav_options = ["Gauche", "Droite"]
        elif "L" in st.session_state.type_canape:
            trav_options = ["Gauche", "Bas"]
        else:
            trav_options = ["Gauche", "Droite", "Bas"]
        traversins_positions = st.multiselect(
            "Position des traversins",
            trav_options,
            default=trav_options,
            help="Sélectionnez où placer les traversins supplémentaires"
        )

    # Calculer le nombre effectif de traversins en fonction des positions sélectionnées.
    # Si aucune position n'est sélectionnée, considérer qu'il n'y a pas de traversin supplémentaire.
    if traversins_positions:
        nb_traversins_effectif = len(traversins_positions)
    else:
        nb_traversins_effectif = 0
    has_surmatelas = st.checkbox("Surmatelas")

# ONGLET 5 : MOUSSE
with tab5:
    st.markdown("### Paramètres de la mousse")
    
    col1, col2 = st.columns(2)
    
    with col1:
        type_mousse = st.selectbox("Type de mousse", ["D25", "D30", "HR35", "HR45"])
        epaisseur = st.number_input("Épaisseur (cm)", min_value=15, max_value=35, value=25, step=5)
        # Ajout de l'option arrondis (par défaut cochée) permettant de majorer le prix de 20€ par banquette et par banquette d'angle
        arrondis = st.checkbox("Arrondis (bords arrondis)", value=True)
    
    with col2:
        st.info("Les options de tissus seront affichées après validation de la configuration")

# ONGLET 6 : CLIENT
with tab6:
    st.markdown("### Informations Client")
    st.markdown("Renseignez les coordonnées du client pour finaliser le devis")
    
    col_client1, col_client2 = st.columns(2)
    
    with col_client1:
        # Le nom du client n'est plus obligatoire : on retire l'astérisque et on laisse le champ facultatif
        nom_client = st.text_input("Nom du client", placeholder="Entrez le nom du client")
        telephone_client = st.text_input("N° de téléphone", placeholder="06 12 34 56 78")
    
    with col_client2:
        email_client = st.text_input("Email (optionnel)", placeholder="client@example.com")
        departement_client = st.text_input("Département", placeholder="Ex: Nord (59)")
    
    if email_client:
        st.info("L'email permet d'envoyer le devis au client")

    # Champ de réduction TTC (optionnel)
    reduction_ttc = st.number_input(
        "Réduction (TTC €)",
        min_value=0.0,
        value=0.0,
        step=10.0,
        help="Saisissez une réduction en euros TTC qui sera appliquée au total."
    )
    # Enregistrer la réduction dans la session pour qu'elle soit accessible lors du calcul du devis
    st.session_state['reduction_ttc'] = reduction_ttc

    # Options pour afficher ou non les pages détaillées du devis et du coût de revient dans le PDF
    show_detail_devis = st.checkbox(
        "Afficher le détail du devis (page 2)",
        value=False,
        help="Lorsque cette option est cochée, la page 2 du PDF affichera le tableau complet des calculs du prix."
    )
    show_detail_cr = st.checkbox(
        "Afficher le détail du coût de revient (page 3)",
        value=False,
        help="Lorsque cette option est cochée, la page 3 du PDF affichera le tableau complet des calculs du coût de revient."
    )

    # Stocker les choix dans la session pour les utiliser lors de la génération du PDF
    st.session_state['show_detail_devis'] = show_detail_devis
    st.session_state['show_detail_cr'] = show_detail_cr

    st.markdown("---")
    st.markdown("### Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👁️ Générer l'Aperçu", use_container_width=True):
            with st.spinner("Génération du schéma en cours..."):
                try:
                    # Préparer le dictionnaire de couleurs à partir des choix de l'utilisateur
                    try:
                        struct_choice = st.session_state.get('color_structure_choice')
                    except Exception:
                        struct_choice = None
                    try:
                        banq_choice = st.session_state.get('color_banquette_choice')
                    except Exception:
                        banq_choice = None
                    try:
                        cous_choice = st.session_state.get('color_coussins_choice')
                    except Exception:
                        cous_choice = None
                    # Construire la palette de couleurs pour le schéma.  Si la couleur de la structure
                    # (accoudoirs/dossiers) est "Transparent", on utilise une chaîne vide pour accoudoirs
                    # et dossiers afin d'éviter un éclaircissement par défaut dans canapematplot.
                    struct_val = COLOR_PALETTE.get(struct_choice)
                    if struct_val is None:
                        acc_val = ""
                        dos_val = ""
                    else:
                        acc_val = struct_val
                        dos_val = struct_val
                    ass_val = COLOR_PALETTE.get(banq_choice)
                    ass_val = ass_val if ass_val is not None else None
                    cous_val = COLOR_PALETTE.get(cous_choice)
                    couleurs = {
                        'accoudoirs': acc_val,
                        'dossiers': dos_val,
                        'assise': ass_val,
                        'coussins': cous_val,
                    }

                    # Générer le schéma avec les paramètres actuels
                    fig = generer_schema_canape(
                        type_canape=st.session_state.type_canape,
                        tx=st.session_state.tx, ty=st.session_state.ty, tz=st.session_state.tz,
                        profondeur=st.session_state.profondeur,
                        acc_left=acc_left, acc_right=acc_right, acc_bas=acc_bas,
                        dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                        meridienne_side=meridienne_side, meridienne_len=meridienne_len,
                        coussins=type_coussins,
                        nb_traversins_supp=nb_traversins_supp,
                        traversins_positions=traversins_positions,
                        couleurs=couleurs
                    )

                    # Préparer une fonction utilitaire pour calculer les prix HT
                    base_params = {
                        'type_canape': st.session_state.type_canape,
                        'tx': st.session_state.tx, 'ty': st.session_state.ty, 'tz': st.session_state.tz,
                        'profondeur': st.session_state.profondeur,
                        'type_coussins': type_coussins,
                        'type_mousse': type_mousse, 'epaisseur': epaisseur,
                        'acc_left': acc_left, 'acc_right': acc_right, 'acc_bas': acc_bas,
                        'dossier_left': dossier_left, 'dossier_bas': dossier_bas, 'dossier_right': dossier_right,
                        'nb_coussins_deco': nb_coussins_deco, 'nb_traversins_supp': nb_traversins_effectif,
                        'has_surmatelas': has_surmatelas,
                        'has_meridienne': has_meridienne,
                        # transmettre également les positions des traversins pour un calcul cohérent
                        'traversins_positions': traversins_positions
                    }
                    def price_ht_for(update_dict):
                        params = base_params.copy()
                        params.update(update_dict)
                        return calculer_prix_total(**params)['prix_ht']

                    # Déterminer le nombre de banquettes et d'angles
                    nb_banquettes, nb_angles = 0, 0
                    tc = st.session_state.type_canape
                    if "Simple" in tc:
                        nb_banquettes, nb_angles = 1, 0
                    elif "L - Sans Angle" in tc:
                        nb_banquettes, nb_angles = 2, 0
                    elif "L - Avec Angle" in tc:
                        nb_banquettes, nb_angles = 2, 1
                    elif "U - Sans Angle" in tc:
                        nb_banquettes, nb_angles = 3, 0
                    elif "U - 1 Angle" in tc:
                        nb_banquettes, nb_angles = 3, 1
                    elif "U - 2 Angles" in tc:
                        nb_banquettes, nb_angles = 3, 2

                    # Prix de base (banquettes seules avec mousse de base D25 et sans options)
                    alt_no_extras_ht = price_ht_for({
                        'acc_left': False, 'acc_right': False, 'acc_bas': False,
                        'dossier_left': False, 'dossier_bas': False, 'dossier_right': False,
                        'type_coussins': 'auto', 'nb_coussins_deco': 0, 'nb_traversins_supp': 0, 'has_surmatelas': False,
                        'type_mousse': 'D25'
                    })

                    # Prix avec accoudoirs uniquement (mousse base)
                    alt_with_acc_ht = price_ht_for({
                        'acc_left': acc_left, 'acc_right': acc_right, 'acc_bas': acc_bas,
                        'dossier_left': False, 'dossier_bas': False, 'dossier_right': False,
                        'type_coussins': 'auto', 'nb_coussins_deco': 0, 'nb_traversins_supp': 0, 'has_surmatelas': False,
                        'type_mousse': 'D25'
                    })
                    price_acc = max(0, alt_with_acc_ht - alt_no_extras_ht)

                    # Prix avec dossiers uniquement (mousse base)
                    alt_with_dossier_ht = price_ht_for({
                        'acc_left': False, 'acc_right': False, 'acc_bas': False,
                        'dossier_left': dossier_left, 'dossier_bas': dossier_bas, 'dossier_right': dossier_right,
                        'type_coussins': 'auto', 'nb_coussins_deco': 0, 'nb_traversins_supp': 0, 'has_surmatelas': False,
                        'type_mousse': 'D25'
                    })
                    price_dossiers = max(0, alt_with_dossier_ht - alt_no_extras_ht)

                    # Prix avec mousse sélectionnée (sans autres options)
                    alt_with_mousse_ht = price_ht_for({
                        'acc_left': False, 'acc_right': False, 'acc_bas': False,
                        'dossier_left': False, 'dossier_bas': False, 'dossier_right': False,
                        'type_coussins': 'auto', 'nb_coussins_deco': 0, 'nb_traversins_supp': 0, 'has_surmatelas': False,
                        'type_mousse': type_mousse
                    })
                    price_mousse = max(0, alt_with_mousse_ht - alt_no_extras_ht)

                    # Prix des coussins (assise + déco + traversins + surmatelas) avec mousse base
                    alt_with_coussins_ht = price_ht_for({
                        'acc_left': False, 'acc_right': False, 'acc_bas': False,
                        'dossier_left': False, 'dossier_bas': False, 'dossier_right': False,
                        'type_coussins': type_coussins, 'nb_coussins_deco': nb_coussins_deco, 'nb_traversins_supp': nb_traversins_supp, 'has_surmatelas': has_surmatelas,
                        'type_mousse': 'D25'
                    })
                    price_coussins_total = max(0, alt_with_coussins_ht - alt_no_extras_ht)

                    # Total hors arrondis (base + options)
                    prix_ht_sans_arrondis = alt_no_extras_ht + price_acc + price_dossiers + price_mousse + price_coussins_total

                    # Calcul complet du devis via le module de pricing (inclut arrondis)
                    prix_details_full = calculer_prix_total(
                        type_canape=st.session_state.type_canape,
                        tx=st.session_state.tx, ty=st.session_state.ty, tz=st.session_state.tz,
                        profondeur=st.session_state.profondeur,
                        type_coussins=type_coussins, type_mousse=type_mousse, epaisseur=epaisseur,
                        acc_left=acc_left, acc_right=acc_right, acc_bas=acc_bas,
                        dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                        nb_coussins_deco=nb_coussins_deco, nb_traversins_supp=nb_traversins_supp,
                        has_surmatelas=has_surmatelas, has_meridienne=has_meridienne,
                        arrondis=arrondis,
                        traversins_positions=traversins_positions
                    )
                    # Récupération des totaux HT et TTC
                    prix_ht_total = prix_details_full.get('prix_ht', 0.0)
                    prix_ttc_total_avant_remise = prix_details_full.get('total_ttc', 0.0)

                    # Récupération de la remise
                    reduction_ttc = st.session_state.get('reduction_ttc', 0.0) or 0.0
                    reduction_ht = reduction_ttc / 1.20 if reduction_ttc else 0.0

                    prix_ht_apres_remise = max(0, prix_ht_total - reduction_ht)
                    tva_apres_remise = round(prix_ht_apres_remise * 0.20, 2)
                    total_ttc_apres_remise = round(prix_ht_apres_remise + tva_apres_remise, 2)

                    # Montant TTC des arrondis pour l'affichage dans le récapitulatif
                    # On récupère le montant TTC directement depuis le module de pricing
                    suppl_arrondis_ttc = prix_details_full.get('arrondis_total', 0.0)

                    # Quantités
                    nb_acc_selected = int(acc_left) + int(acc_right) + int(acc_bas)
                    nb_dossier_selected = int(dossier_left) + int(dossier_bas) + int(dossier_right)

                    # Nombre de coussins d'assise (approximation si dimension numérique)
                    nb_coussins_assise = 0
                    try:
                        couss_dim = int(type_coussins)
                        bench_lengths = []
                        if "Simple" in tc:
                            bench_lengths = [st.session_state.tx]
                        elif "L" in tc:
                            bench_lengths = [st.session_state.ty, st.session_state.tx]
                        else:
                            bench_lengths = [st.session_state.ty, st.session_state.tx, st.session_state.tz]
                        import math
                        for lng in bench_lengths:
                            nb_coussins_assise += math.ceil(lng / couss_dim)
                    except Exception:
                        nb_coussins_assise = 0

                    nb_arrondis_units = nb_banquettes + nb_angles

                    # Construction détaillée du tableau de synthèse
                    # Prix des coussins par catégorie
                    # Prix des coussins d'assise uniquement (hors déco/traversins/surmatelas)
                    alt_only_assise_ht = price_ht_for({
                        'acc_left': False, 'acc_right': False, 'acc_bas': False,
                        'dossier_left': False, 'dossier_bas': False, 'dossier_right': False,
                        'type_coussins': type_coussins,
                        'nb_coussins_deco': 0, 'nb_traversins_supp': 0, 'has_surmatelas': False,
                        'type_mousse': 'D25'
                    })
                    price_assise = max(0, alt_only_assise_ht - alt_no_extras_ht)

                    # Prix avec coussins déco ajoutés
                    alt_assise_deco_ht = price_ht_for({
                        'acc_left': False, 'acc_right': False, 'acc_bas': False,
                        'dossier_left': False, 'dossier_bas': False, 'dossier_right': False,
                        'type_coussins': type_coussins,
                        'nb_coussins_deco': nb_coussins_deco, 'nb_traversins_supp': 0, 'has_surmatelas': False,
                        'type_mousse': 'D25'
                    })
                    price_decoratif = max(0, alt_assise_deco_ht - alt_only_assise_ht)

                    # Prix avec traversins supplémentaires
                    alt_assise_traversins_ht = price_ht_for({
                        'acc_left': False, 'acc_right': False, 'acc_bas': False,
                        'dossier_left': False, 'dossier_bas': False, 'dossier_right': False,
                        'type_coussins': type_coussins,
                        'nb_coussins_deco': 0, 'nb_traversins_supp': nb_traversins_supp, 'has_surmatelas': False,
                        'type_mousse': 'D25'
                    })
                    price_traversins = max(0, alt_assise_traversins_ht - alt_only_assise_ht)

                    # Prix avec surmatelas
                    alt_assise_surmatelas_ht = price_ht_for({
                        'acc_left': False, 'acc_right': False, 'acc_bas': False,
                        'dossier_left': False, 'dossier_bas': False, 'dossier_right': False,
                        'type_coussins': type_coussins,
                        'nb_coussins_deco': 0, 'nb_traversins_supp': 0, 'has_surmatelas': True,
                        'type_mousse': 'D25'
                    }) if has_surmatelas else alt_only_assise_ht
                    price_surmatelas = max(0, alt_assise_surmatelas_ht - alt_only_assise_ht) if has_surmatelas else 0

                    # Répartition du prix de la mousse par banquette (proportionnelle à la longueur)
                    bench_lengths = []
                    if "Simple" in tc:
                        bench_lengths = [st.session_state.tx]
                    elif "L" in tc:
                        bench_lengths = [st.session_state.ty, st.session_state.tx]
                    else:
                        bench_lengths = [st.session_state.ty, st.session_state.tx, st.session_state.tz]
                    total_length = sum(bench_lengths) if bench_lengths else 1
                    price_mousse_per_bench = []
                    for bl in bench_lengths:
                        part = (price_mousse * bl / total_length) if total_length > 0 else 0
                        price_mousse_per_bench.append(part)

                    breakdown_rows = []
                    # Banquettes de base
                    breakdown_rows.append(("Banquettes", nb_banquettes, f"{alt_no_extras_ht:.2f} €"))
                    # Accoudoirs
                    breakdown_rows.append(("Accoudoirs", nb_acc_selected, f"{price_acc:.2f} €"))
                    # Coussins d'assise
                    breakdown_rows.append(("Coussins assise", nb_coussins_assise, f"{price_assise:.2f} €"))
                    # Coussins décoratifs
                    breakdown_rows.append(("Coussins déco", nb_coussins_deco, f"{price_decoratif:.2f} €"))
                    # Traversins supplémentaires
                    breakdown_rows.append(("Traversins", nb_traversins_supp, f"{price_traversins:.2f} €"))
                    # Surmatelas
                    # Déterminer le nombre de surmatelas en se basant sur le total TTC renvoyé par
                    # ``calculer_prix_total``.  Lorsque l'option surmatelas est activée, la fonction
                    # de pricing ajoute un surmatelas par mousse (dimension) et renvoie un total TTC
                    # égal à 80 € par unité.  On divise donc ce total par 80 pour obtenir la quantité.
                    surmatelas_total_ttc = prix_details_full.get('surmatelas_total', 0.0)
                    nb_surmatelas_units = int(round(surmatelas_total_ttc / 80.0)) if has_surmatelas else 0
                    breakdown_rows.append(("Surmatelas", nb_surmatelas_units, f"{price_surmatelas:.2f} €"))
                    # Dossiers
                    breakdown_rows.append(("Dossiers", nb_dossier_selected, f"{price_dossiers:.2f} €"))
                    # Mousse par banquette
                    for idx, part_price in enumerate(price_mousse_per_bench, start=1):
                        # Libellé de la dimension : on utilise l'indice de la banquette pour différencier
                        breakdown_rows.append((f"Mousse {type_mousse} dim.{idx}", 1, f"{part_price:.2f} €"))
                    # Arrondis
                    # Utiliser le montant TTC récupéré dans prix_details_full pour l'affichage
                    breakdown_rows.append(("Arrondis", nb_arrondis_units, f"{suppl_arrondis_ttc:.2f} €"))
                    # Tissu (inclus)
                    breakdown_rows.append(("Tissu (inclus)", "", "0.00 €"))
                    # Remise
                    if reduction_ttc and reduction_ttc > 0:
                        breakdown_rows.append(("Remise", "", f"-{reduction_ttc:.2f} €"))
                    # Livraison
                    breakdown_rows.append(("Livraison bas d'immeuble/maison", "", "Gratuit"))
                    # Total TTC après remise
                    breakdown_rows.append(("Total TTC", "", f"{total_ttc_apres_remise:.2f} €"))

                    # Calcul du prix TTC total avant remise (conversion du HT en TTC)
                    prix_ttc_total_avant_remise = round(prix_ht_total * 1.20, 2)
                    # On calcule à nouveau le coût de revient pour intégrer correctement les arrondis
                    prix_details_calc = calculer_prix_total(
                        type_canape=st.session_state.type_canape,
                        tx=st.session_state.tx, ty=st.session_state.ty, tz=st.session_state.tz,
                        profondeur=st.session_state.profondeur,
                        type_coussins=type_coussins, type_mousse=type_mousse, epaisseur=epaisseur,
                        acc_left=acc_left, acc_right=acc_right, acc_bas=acc_bas,
                        dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                        nb_coussins_deco=nb_coussins_deco, nb_traversins_supp=nb_traversins_supp,
                        has_surmatelas=has_surmatelas, has_meridienne=has_meridienne,
                        arrondis=arrondis,
                        traversins_positions=traversins_positions
                    )
                    cout_revient_ht_total = prix_details_calc.get('cout_revient_ht', 0.0)
                    # Marge totale HT = (prix TTC après remise converti en HT) - coût de revient HT
                    marge_totale_ht = round((total_ttc_apres_remise / 1.20) - cout_revient_ht_total, 2)

                    # Affichage du schéma et d'un résumé simplifié du devis
                    st.success("✅ Schéma généré avec succès !")
                    st.pyplot(fig)
                    plt.close()
                    st.markdown("### 🧾 Résumé du devis", unsafe_allow_html=True)
                    st.markdown(f"**Prix de vente TTC total avant réduction :** {prix_ttc_total_avant_remise:.2f} €")
                    if reduction_ttc and reduction_ttc > 0:
                        st.markdown(f"**Réduction TTC :** -{reduction_ttc:.2f} €")
                    st.markdown(f"**Prix de vente TTC total après réduction :** {total_ttc_apres_remise:.2f} €")
                    st.markdown(f"**Marge totale HT :** {marge_totale_ht:.2f} €")

                    # Stockage des valeurs pour utilisation lors de la génération du PDF
                    st.session_state['breakdown_rows'] = breakdown_rows
                    st.session_state['prix_ht'] = prix_ht_apres_remise
                    st.session_state['tva'] = tva_apres_remise
                    st.session_state['total_ttc'] = total_ttc_apres_remise
                    st.session_state['remise_ttc'] = reduction_ttc

                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")

    with col2:
        # Suppression de l'obligation de renseigner un nom : le PDF peut être généré sans nom
        if st.button("📄 Générer le Devis PDF", type="primary", use_container_width=True):
            with st.spinner("Création du PDF en cours..."):
                try:
                    # Préparer le dictionnaire de couleurs à partir des choix de l'utilisateur pour le schéma PDF
                    try:
                        struct_choice = st.session_state.get('color_structure_choice')
                    except Exception:
                        struct_choice = None
                    try:
                        banq_choice = st.session_state.get('color_banquette_choice')
                    except Exception:
                        banq_choice = None
                    try:
                        cous_choice = st.session_state.get('color_coussins_choice')
                    except Exception:
                        cous_choice = None
                    # Construire la palette de couleurs pour le schéma PDF.
                    struct_val = COLOR_PALETTE.get(struct_choice)
                    if struct_val is None:
                        acc_val = ""
                        dos_val = ""
                    else:
                        acc_val = struct_val
                        dos_val = struct_val
                    ass_val = COLOR_PALETTE.get(banq_choice)
                    ass_val = ass_val if ass_val is not None else None
                    cous_val = COLOR_PALETTE.get(cous_choice)
                    couleurs = {
                        'accoudoirs': acc_val,
                        'dossiers': dos_val,
                        'assise': ass_val,
                        'coussins': cous_val,
                    }
                    fig = generer_schema_canape(
                        type_canape=st.session_state.type_canape,
                        tx=st.session_state.tx, ty=st.session_state.ty, tz=st.session_state.tz,
                        profondeur=st.session_state.profondeur,
                        acc_left=acc_left, acc_right=acc_right, acc_bas=acc_bas,
                        dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                        meridienne_side=meridienne_side, meridienne_len=meridienne_len,
                        coussins=type_coussins,
                        # Utiliser nb_traversins_supp (réel) pour refléter les positions sélectionnées dans le schéma PDF
                        nb_traversins_supp=nb_traversins_effectif,
                        traversins_positions=traversins_positions,
                        couleurs=couleurs
                    )
                    
                    img_buffer = BytesIO()
                    fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
                    img_buffer.seek(0)
                    plt.close(fig)
                    
                    config = {
                        'type_canape': st.session_state.type_canape,
                        'dimensions': {'tx': st.session_state.tx, 'ty': st.session_state.ty, 'tz': st.session_state.tz, 'profondeur': st.session_state.profondeur},
                        'options': {
                            'acc_left': acc_left, 'acc_right': acc_right, 'acc_bas': acc_bas,
                            'dossier_left': dossier_left, 'dossier_bas': dossier_bas, 'dossier_right': dossier_right,
                            'meridienne_side': meridienne_side, 'meridienne_len': meridienne_len,
                            'type_coussins': type_coussins, 'type_mousse': type_mousse, 'epaisseur': epaisseur,
                            'arrondis': arrondis
                        },
                        'client': {'nom': nom_client, 'email': email_client, 'telephone': telephone_client, 'departement': departement_client}
                    }
                    
                    prix_details = calculer_prix_total(
                        type_canape=st.session_state.type_canape,
                        tx=st.session_state.tx, ty=st.session_state.ty, tz=st.session_state.tz,
                        profondeur=st.session_state.profondeur,
                        type_coussins=type_coussins, type_mousse=type_mousse, epaisseur=epaisseur,
                        acc_left=acc_left, acc_right=acc_right, acc_bas=acc_bas,
                        dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                        nb_coussins_deco=nb_coussins_deco, nb_traversins_supp=nb_traversins_effectif,
                        has_surmatelas=has_surmatelas, has_meridienne=has_meridienne,
                        arrondis=arrondis,
                        traversins_positions=traversins_positions
                    )
                    # Le supplément d'arrondis est maintenant intégré dans calculer_prix_total via le paramètre arrondis

                    # Application de la réduction TTC si elle existe
                    reduction_ttc = st.session_state.get('reduction_ttc', 0.0) or 0.0
                    if reduction_ttc and reduction_ttc > 0:
                        reduction_ht = reduction_ttc / 1.20
                        prix_details['prix_ht'] = max(0, prix_details['prix_ht'] - reduction_ht)
                        prix_details['tva'] = round(prix_details['prix_ht'] * 0.20, 2)
                        prix_details['total_ttc'] = round(prix_details['prix_ht'] + prix_details['tva'], 2)
                        prix_details['reduction_ttc'] = reduction_ttc
                    else:
                        prix_details['reduction_ttc'] = 0.0

                    # Récupération du tableau détaillé du devis depuis la session
                    breakdown_rows = st.session_state.get('breakdown_rows', None)
                    
                    pdf_buffer = generer_pdf_devis(
                        config,
                        prix_details,
                        schema_image=img_buffer,
                        breakdown_rows=breakdown_rows,
                        reduction_ttc=prix_details.get('reduction_ttc', 0.0),
                        show_detail_devis=st.session_state.get('show_detail_devis', False),
                        show_detail_cr=st.session_state.get('show_detail_cr', False)
                    )
                    
                    st.download_button(
                        label="⬇️ Télécharger le Devis PDF",
                        data=pdf_buffer,
                        file_name=f"devis_canape_{(nom_client or 'client').replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                    
                    st.success("✅ PDF généré avec succès !")
                    
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #8C6F63;'>
    <p>🛋️ Configurateur de Canapé Marocain Sur Mesure</p>
</div>
""", unsafe_allow_html=True)

