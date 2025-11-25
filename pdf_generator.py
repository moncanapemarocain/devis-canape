from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# --- POLICE UNICODE ---
FONT_NAME_UNICODE = 'DejaVuSans'
FONT_FILE = 'DejaVuSans.ttf'

if os.path.exists(FONT_FILE):
    pdfmetrics.registerFont(TTFont(FONT_NAME_UNICODE, FONT_FILE))
    BASE_FONT = FONT_NAME_UNICODE
else:
    BASE_FONT = 'Helvetica'
    print(f"ATTENTION : Le fichier de police {FONT_FILE} est introuvable.")
# ----------------------

# --- MAPPING DES IMAGES ---
IMAGE_FILES = {
    'D25': 'D25.png',
    'D30': 'D30.png',
    'HR35': 'HR35.png',
    'HR45': 'HR45.png'
}


def generer_pdf_devis(config, prix_details, schema_image=None, breakdown_rows=None, reduction_ttc=0.0):
    """
    Génère un PDF de devis. La première page contient le résumé et le schéma, la seconde page
    (facultative) présente un tableau détaillé des éléments et des prix. Une remise TTC peut
    être indiquée et sera visible sur les deux pages. Un pied de page fixe est ajouté à
    chaque page.
    """
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=1*cm, leftMargin=1*cm,
                           topMargin=1*cm, bottomMargin=6*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- DÉFINITION DES STYLES ---
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'], fontSize=14, textColor=colors.black, 
        spaceAfter=5, alignment=TA_CENTER, fontName=BASE_FONT + '-Bold'
    )
    
    header_info_style = ParagraphStyle(
        'HeaderInfo', parent=styles['Normal'], fontSize=12, leading=14, 
        textColor=colors.black, alignment=TA_CENTER, fontName=BASE_FONT
    )
    
    price_style = ParagraphStyle(
        'PriceStyle', parent=styles['Heading2'], fontSize=16, alignment=TA_CENTER, 
        fontName=BASE_FONT, textColor=colors.black, spaceBefore=10, spaceAfter=10
    )
    
    # Style de description de mousse
    # Réduction de la taille de police (12 -> 10) pour laisser plus de place au schéma et aux informations
    description_mousse_style = ParagraphStyle(
        'MousseDesc', parent=styles['Normal'], fontSize=10, leading=11, 
        textColor=colors.black, alignment=TA_LEFT, fontName=BASE_FONT
    )
    
    # Styles pour le pied de page
    # Les tailles de police sont légèrement réduites pour alléger le pied de page
    column_header_style = ParagraphStyle(
        'ColumnHeaderStyle', parent=styles['Normal'], fontSize=11, alignment=TA_LEFT, 
        fontName=BASE_FONT + '-Bold', spaceAfter=6
    )

    detail_style = ParagraphStyle(
        'DetailStyle', parent=styles['Normal'], fontSize=10, leading=11, 
        textColor=colors.black, alignment=TA_LEFT, fontName=BASE_FONT
    )
    
    footer_style = ParagraphStyle(
        'FooterStyle', parent=styles['Normal'], fontSize=12, textColor=colors.black, 
        alignment=TA_CENTER, spaceBefore=10, fontName=BASE_FONT
    )

    # --- FONCTION INTERNE POUR DESSINER LE PIED DE PAGE FIXE ---
    def draw_footer(canvas, doc):
        canvas.saveState()
        
        # 1. Préparation des données des colonnes
        
        # Colonne Gauche
        col_gauche = []
        col_gauche.append(Paragraph("Il faut savoir que le tarif comprend :", column_header_style))
        inclus_items = [
            "Livraison bas d'immeuble",
            "Fabrication 100% artisanale France",
            "Choix du tissu n'impacte pas le devis",
            "Paiement 2 à 6 fois sans frais",
            "Livraison 5 à 7 semaines",
            "Housses déhoussables"
        ]
        for item in inclus_items:
            col_gauche.append(Paragraph(f"• {item}", detail_style))

        # Colonne Droite
        col_droite = []
        col_droite.append(Paragraph("Détail des cotations :", column_header_style))
        
        h_mousse = config['options'].get('epaisseur', 25)
        h_assise = 46 if h_mousse > 20 else 40
        
        cotations_items = [
            "Accoudoir: 15cm large / 60cm haut",
            "Dossier: 10cm large / 70cm haut",
            "Coussins: 65/80/90cm large",
            f"Profondeur assise: {config['dimensions']['profondeur']} cm",
            f"Hauteur assise: {h_assise} cm (Mousse {h_mousse}cm)"
        ]
        for item in cotations_items:
            col_droite.append(Paragraph(f"• {item}", detail_style))

        table_footer = Table([[col_gauche, col_droite]], colWidths=[9.5*cm, 9.5*cm])
        table_footer.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        w, h = table_footer.wrap(doc.width, doc.bottomMargin)
        table_footer.drawOn(canvas, doc.leftMargin, 1.5*cm)
        
        # 2. Ville (ex-Partie 6)
        p_ville = Paragraph("FRÉVENT 62270", footer_style)
        w_ville, h_ville = p_ville.wrap(doc.width, doc.bottomMargin)
        p_ville.drawOn(canvas, doc.leftMargin, 0.5*cm)
        
        canvas.restoreState()

    # =================== CONTENU DU DOCUMENT ===================
    
    # 1. TITRE et INFOS HAUTES
    elements.append(Paragraph("MON CANAPÉ MAROCAIN", title_style))
    
    # Préparation des informations générales pour la suite
    type_canape = config.get('type_canape', '')
    dims = config.get('dimensions', {})
    # Détermination de la chaîne de dimensions selon le type de canapé
    if "U" in type_canape:
        dim_str = f"{dims.get('ty',0)} x {dims.get('tx',0)} x {dims.get('tz',0)}"
    elif "L" in type_canape:
        dim_str = f"{dims.get('ty',0)} x {dims.get('tx',0)}"
    else:
        dim_str = f"{dims.get('tx',0)} x {dims.get('profondeur',0)}"

    mousse_type = config.get('options', {}).get('type_mousse', 'HR35')
    dossier_txt = 'Avec' if config.get('options', {}).get('dossier_bas') else 'Sans'
    acc_txt = 'Oui' if (config.get('options', {}).get('acc_left') or config.get('options', {}).get('acc_right')) else 'Non'

    # En-tête client uniquement : ne pas afficher dimensions/confort/dossiers/accoudoirs ici
    client = config.get('client', {})
    lignes_info = []
    if client.get('nom'):
        lignes_info.append(f"<b>Nom:</b> {client['nom']}")
    if client.get('telephone'):
        lignes_info.append(f"<b>Téléphone:</b> {client['telephone']}")
    # Afficher l'en-tête client seulement si au moins une information est renseignée
    if lignes_info:
        elements.append(Paragraph("<br/>".join(lignes_info), header_info_style))
    
    # Description mousse dynamique
    descriptions_mousse = {
        'D25': "La mousse D25 est une mousse polyuréthane de 25kg/m3. Elle est très ferme, parfaite pour les habitués des banquettes marocaines classiques.",
        'D30': "La mousse D30 est une mousse polyuréthane de 30kg/m3. Elle est ultra ferme, idéale pour ceux qui recherchent un canapé très ferme.",
        'HR35': "La mousse HR35 est une mousse haute résilience de 35kg/m3. Elle est semi ferme confortable, parfaite pour les adeptes des salons confortables.<br/>Les mousses haute résilience reprennent rapidement leur forme initiale et donc limitent l’affaissement dans le temps.",
        'HR45': "La mousse HR45 est une mousse haute résilience de 45kg/m3. Elle est ferme confortable, parfaite pour les adeptes des salons confortables mais pas trop moelleux.<br/>Les mousses haute résilience reprennent rapidement leur forme initiale et donc limitent l’affaissement dans le temps."
    }
    texte_mousse = descriptions_mousse.get(mousse_type, descriptions_mousse['HR35'])
    
    elements.append(Spacer(1, 0.2*cm))
    
    # --- MODIFICATION CLÉ : Image et Texte en Tableau ---
    image_path = IMAGE_FILES.get(mousse_type)
    
    if image_path:
        try:
            img_mousse = Image(image_path, width=2.5*cm, height=2.5*cm)
            text_flowable = Paragraph(f"<i>{texte_mousse}</i>", description_mousse_style)
            
            # Ajustement des colWidths pour laisser plus de marge
            # 18cm de largeur totale disponible (A4 - 2x1cm marge)
            mousse_table = Table([[img_mousse, text_flowable]], colWidths=[3*cm, 14*cm]) 
            
            mousse_table.setStyle(TableStyle([
                # Centrage vertical par rapport à l'image
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
                # Ajout de padding à gauche et à droite de la table complète pour effet de marge
                ('LEFTPADDING', (0, 0), (0, 0), 0.5*cm), # Marge à gauche de l'image
                ('RIGHTPADDING', (0, 0), (-1, -1), 0.5*cm), # Marge à droite du texte
            ]))
            elements.append(mousse_table)
        except Exception:
            # En cas d'erreur de fichier, afficher le texte seul 
            elements.append(Paragraph(f"<i>{texte_mousse}</i>", description_mousse_style))
    else:
        elements.append(Paragraph(f"<i>{texte_mousse}</i>", description_mousse_style))

    elements.append(Spacer(1, 0.3*cm))

    # 3. SCHÉMA
    if schema_image:
        try:
            img = Image(schema_image)
            # Pour obtenir un schéma plus grand dans le devis, on étend l’espace
            # disponible pour l’image. La largeur disponible est fixée à la
            # largeur utile de la page (`doc.width`), et la hauteur maximale est
            # augmentée à 13 cm (au lieu de 10 cm) pour offrir une vue plus
            # détaillée du schéma tout en laissant de la place pour le texte et
            # le prix.
            avail_width = doc.width
            avail_height = 13 * cm
            
            img_w = img.imageWidth
            img_h = img.imageHeight
            
            if img_w > 0:
                aspect = img_h / float(img_w)
            else:
                aspect = 1.0

            if aspect > (avail_height / avail_width):
                img.drawHeight = avail_height
                img.drawWidth = avail_height / aspect
            else:
                img.drawWidth = avail_width
                img.drawHeight = avail_width * aspect
            
            elements.append(img)
        except Exception:
            elements.append(Paragraph("<i>(Schéma non disponible)</i>", header_info_style))

    # Ajouter un espace avant le récapitulatif du devis
    elements.append(Spacer(1, 0.5 * cm))

    # 4. DÉTAIL DU DEVIS (remplace l'ancien bloc prix/remise et la page supplémentaire)
    # Calculs des montants nécessaires
    montant_ttc_val = float(prix_details.get('total_ttc', 0.0))
    montant_ttc = f"{montant_ttc_val:.2f} €"
    # Réduction TTC
    reduction_ttc_val = float(reduction_ttc or 0.0)
    # Prix avant réduction = montant actuel + réduction
    prix_avant_reduc_val = montant_ttc_val + reduction_ttc_val
    prix_avant_reduc = f"{prix_avant_reduc_val:.2f} €"

    # Déterminer le nombre de coussins d'assise à partir du tableau détaillé, si disponible
    nb_coussins_assise = None
    if breakdown_rows:
        try:
            for row in breakdown_rows:
                if isinstance(row, (list, tuple)) and len(row) >= 2 and "Coussins assise" in str(row[0]):
                    nb_coussins_assise = row[1]
                    break
        except Exception:
            nb_coussins_assise = None

    # Détermination de la taille des coussins selon l'option choisie
    type_coussins = config.get('options', {}).get('type_coussins', 'auto')
    if type_coussins in ['65', '80', '90']:
        taille_coussins = f"{type_coussins} cm"
    elif type_coussins == 'auto':
        taille_coussins = "65/80/90 cm"
    elif type_coussins == 'valise':
        taille_coussins = "format valise"
    elif type_coussins == 'p':
        taille_coussins = "petit modèle"
    elif type_coussins == 'g':
        taille_coussins = "grand modèle"
    else:
        taille_coussins = str(type_coussins)

    # Colonne gauche : caractéristiques générales
    col_left = []
    col_left.append(Paragraph("Détail du devis :", column_header_style))
    col_left.append(Paragraph(f"Dimensions : {dim_str} cm", detail_style))
    col_left.append(Paragraph(f"Mousse : {mousse_type}", detail_style))
    col_left.append(Paragraph(f"Accoudoirs : {acc_txt}", detail_style))
    col_left.append(Paragraph(f"Dossiers : {dossier_txt}", detail_style))
    col_left.append(Paragraph(f"Profondeur : {dims.get('profondeur', 0)} cm", detail_style))

    # Colonne droite : coussins, livraison, réduction et prix
    col_right = []
    if nb_coussins_assise is not None:
        col_right.append(Paragraph(f"Nombre de coussins : {nb_coussins_assise} de {taille_coussins}", detail_style))
    else:
        col_right.append(Paragraph("Nombre de coussins : -", detail_style))
    # Livraison : gratuite
    col_right.append(Paragraph("Livraison : <b>gratuite</b>", detail_style))
    # Réduction TTC si fournie
    col_right.append(Paragraph(f"Réduction : {reduction_ttc_val:.2f} €", detail_style))
    # Prix d'angle (le prix final après réduction)
    col_right.append(Paragraph(f"Prix canapé d'angle : <b>{montant_ttc}</b>", detail_style))
    # Prix avant réduction
    col_right.append(Paragraph(f"Prix avant réduction : {prix_avant_reduc}", detail_style))

    # Construction du tableau à deux colonnes
    devis_table = Table([[col_left, col_right]], colWidths=[9.5 * cm, 9.5 * cm])
    devis_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(devis_table)

    # Construction du document PDF : une seule page, avec pied de page sur toutes les pages
    doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)
    buffer.seek(0)
    return buffer
