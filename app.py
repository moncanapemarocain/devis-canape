"""
Application Streamlit pour générer des devis de canapés sur mesure
Compatible Streamlit Cloud - Utilise canapematplot.py
"""

import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

# Import des modules personnalisés
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
def generer_schema_canape(type_canape, tx, ty, tz, profondeur, 
                          acc_left, acc_right, acc_bas,
                          dossier_left, dossier_bas, dossier_right,
                          meridienne_side, meridienne_len, coussins="auto"):
    """Génère le schéma du canapé"""
    fig = plt.figure(figsize=(12, 8))
    
    try:
        if "Simple" in type_canape:
            render_Simple1(
                tx=tx, profondeur=profondeur, dossier=dossier_bas,
                acc_left=acc_left, acc_right=acc_right,
                meridienne_side=meridienne_side, meridienne_len=meridienne_len,
                coussins=coussins, window_title="Canapé Simple"
            )
        elif "L - Sans Angle" in type_canape:
            render_LNF(
                tx=tx, ty=ty, profondeur=profondeur,
                dossier_left=dossier_left, dossier_bas=dossier_bas,
                acc_left=acc_left, acc_bas=acc_bas,
                meridienne_side=meridienne_side, meridienne_len=meridienne_len,
                coussins=coussins, variant="auto", window_title="Canapé L - Sans Angle"
            )
        elif "L - Avec Angle" in type_canape:
            render_LF_variant(
                tx=tx, ty=ty, profondeur=profondeur,
                dossier_left=dossier_left, dossier_bas=dossier_bas,
                acc_left=acc_left, acc_bas=acc_bas,
                meridienne_side=meridienne_side, meridienne_len=meridienne_len,
                coussins=coussins, window_title="Canapé L - Avec Angle"
            )
        elif "U - Sans Angle" in type_canape:
            render_U(
                tx=tx, ty_left=ty, tz_right=tz, profondeur=profondeur,
                dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                acc_left=acc_left, acc_bas=acc_bas, acc_right=acc_right,
                coussins=coussins, variant="auto", window_title="Canapé U - Sans Angle"
            )
        elif "U - 1 Angle" in type_canape:
            render_U1F_v1(
                tx=tx, ty=ty, tz=tz, profondeur=profondeur,
                dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                acc_left=acc_left, acc_right=acc_right,
                meridienne_side=meridienne_side, meridienne_len=meridienne_len,
                coussins=coussins, window_title="Canapé U - 1 Angle"
            )
        elif "U - 2 Angles" in type_canape:
            render_U2f_variant(
                tx=tx, ty_left=ty, tz_right=tz, profondeur=profondeur,
                dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                acc_left=acc_left, acc_bas=acc_bas, acc_right=acc_right,
                meridienne_side=meridienne_side, meridienne_len=meridienne_len,
                coussins=coussins, window_title="Canapé U - 2 Angles"
            )
        
        fig = plt.gcf()
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

# Création des onglets
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Type", "Dimensions", "Options", "Matériaux", "Client"])

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

# ONGLET 3: OPTIONS
with tab3:
    st.markdown("### Options de configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Accoudoirs**")
        acc_left = st.checkbox("Accoudoir Gauche", value=True)
        acc_right = st.checkbox("Accoudoir Droit", value=True)
        if "L" not in st.session_state.type_canape and "Simple" not in st.session_state.type_canape:
            acc_bas = st.checkbox("Accoudoir Bas", value=True)
        else:
            acc_bas = st.checkbox("Accoudoir Bas", value=True) if "L" in st.session_state.type_canape else False
        
        st.markdown("**Dossiers**")
        dossier_left = st.checkbox("Dossier Gauche", value=True) if "Simple" not in st.session_state.type_canape else False
        dossier_bas = st.checkbox("Dossier Bas", value=True)
        dossier_right = st.checkbox("Dossier Droit", value=True) if ("U" in st.session_state.type_canape) else False
    
    with col2:
        st.markdown("**Méridienne**")
        has_meridienne = st.checkbox("Ajouter une méridienne", value=False)
        
        if has_meridienne:
            meridienne_side = st.selectbox(
                "Position de la méridienne",
                ["left", "right"],
                format_func=lambda x: "Gauche" if x == "left" else "Droite"
            )
            meridienne_len = st.number_input("Longueur (cm)", min_value=80, max_value=200, value=120, step=10)
        else:
            meridienne_side = "left"
            meridienne_len = 0
        
        st.markdown("**Coussins**")
        type_coussins = st.selectbox(
            "Type de coussins",
            ["auto", "65", "80", "90", "valise", "p", "g"],
            help="Auto = optimisation automatique"
        )
        
        nb_coussins_deco = st.number_input("Coussins décoratifs", min_value=0, max_value=10, value=0)
        nb_traversins_supp = st.number_input("Traversins supplémentaires", min_value=0, max_value=5, value=0)
        has_surmatelas = st.checkbox("Surmatelas")

# ONGLET 4: MATÉRIAUX
with tab4:
    st.markdown("### Mousse et tissus")
    
    col1, col2 = st.columns(2)
    
    with col1:
        type_mousse = st.selectbox("Type de mousse", ["D25", "D30", "HR35", "HR45"])
        epaisseur = st.number_input("Épaisseur (cm)", min_value=15, max_value=35, value=25, step=5)
    
    with col2:
        st.info("Les options de tissus seront affichées après validation de la configuration")

# ONGLET 5: CLIENT
with tab5:
    st.markdown("### Informations Client")
    st.markdown("Renseignez les coordonnées du client pour finaliser le devis")
    
    col_client1, col_client2 = st.columns(2)
    
    with col_client1:
        nom_client = st.text_input("Nom du client *", placeholder="Entrez le nom du client")
        telephone_client = st.text_input("N° de téléphone", placeholder="06 12 34 56 78")
    
    with col_client2:
        email_client = st.text_input("Email (optionnel)", placeholder="client@example.com")
        departement_client = st.text_input("Département", placeholder="Ex: Nord (59)")
    
    if email_client:
        st.info("L'email permet d'envoyer le devis au client")
    
    st.markdown("---")
    st.markdown("### Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👁️ Générer l'Aperçu", use_container_width=True):
            with st.spinner("Génération du schéma en cours..."):
                try:
                    fig = generer_schema_canape(
                        type_canape=st.session_state.type_canape,
                        tx=st.session_state.tx, ty=st.session_state.ty, tz=st.session_state.tz,
                        profondeur=st.session_state.profondeur,
                        acc_left=acc_left, acc_right=acc_right, acc_bas=acc_bas,
                        dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                        meridienne_side=meridienne_side, meridienne_len=meridienne_len,
                        coussins=type_coussins
                    )
                    
                    st.pyplot(fig)
                    plt.close()
                    st.success("✅ Schéma généré avec succès !")
                    
                    # Calcul du prix
                    prix_details = calculer_prix_total(
                        type_canape=st.session_state.type_canape,
                        tx=st.session_state.tx, ty=st.session_state.ty, tz=st.session_state.tz,
                        profondeur=st.session_state.profondeur,
                        type_coussins=type_coussins, type_mousse=type_mousse, epaisseur=epaisseur,
                        acc_left=acc_left, acc_right=acc_right, acc_bas=acc_bas,
                        dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                        nb_coussins_deco=nb_coussins_deco, nb_traversins_supp=nb_traversins_supp,
                        has_surmatelas=has_surmatelas, has_meridienne=has_meridienne
                    )
                    
                    st.markdown("### 📊 Détails du Devis")
                    col_p1, col_p2, col_p3 = st.columns(3)
                    
                    with col_p1:
                        st.metric("Prix HT", f"{prix_details['prix_ht']}€")
                    with col_p2:
                        st.metric("TVA (20%)", f"{prix_details['tva']}€")
                    with col_p3:
                        st.metric("TOTAL TTC", f"{prix_details['total_ttc']}€")
                    
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")
    
    with col2:
        if st.button("📄 Générer le Devis PDF", type="primary", use_container_width=True):
            if not nom_client:
                st.warning("⚠️ Veuillez renseigner le nom du client")
            else:
                with st.spinner("Création du PDF en cours..."):
                    try:
                        fig = generer_schema_canape(
                            type_canape=st.session_state.type_canape,
                            tx=st.session_state.tx, ty=st.session_state.ty, tz=st.session_state.tz,
                            profondeur=st.session_state.profondeur,
                            acc_left=acc_left, acc_right=acc_right, acc_bas=acc_bas,
                            dossier_left=dossier_left, dossier_bas=dossier_bas, dossier_right=dossier_right,
                            meridienne_side=meridienne_side, meridienne_len=meridienne_len,
                            coussins=type_coussins
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
                                'type_coussins': type_coussins, 'type_mousse': type_mousse, 'epaisseur': epaisseur
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
                            nb_coussins_deco=nb_coussins_deco, nb_traversins_supp=nb_traversins_supp,
                            has_surmatelas=has_surmatelas, has_meridienne=has_meridienne
                        )
                        
                        pdf_buffer = generer_pdf_devis(config, prix_details, schema_image=img_buffer)
                        
                        st.download_button(
                            label="⬇️ Télécharger le Devis PDF",
                            data=pdf_buffer,
                            file_name=f"devis_canape_{nom_client.replace(' ', '_')}.pdf",
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

