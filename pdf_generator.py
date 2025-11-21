from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from io import BytesIO

def generer_pdf_devis(config, prix_details, schema_image=None):
    """
    Génère un PDF de devis avec la mise en page 'Style Marie'
    """
    buffer = BytesIO()
    # Marges réduites pour maximiser l'espace comme sur l'exemple
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=1.5*cm, leftMargin=1.5*cm,
                           topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- DÉFINITION DES STYLES PERSONNALISÉS ---

    # Titre principal (MONCANAPÉMAROCAIN)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.black,
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Style pour le bloc d'informations du haut (Centré)
    header_info_style = ParagraphStyle(
        'HeaderInfo',
        parent=styles['Normal'],
        fontSize=10,
        leading=14, # Espacement entre les lignes
        textColor=colors.black,
        alignment=TA_CENTER
    )
    
    # Titres des colonnes du bas (Gras, aligné gauche)
    column_header_style = ParagraphStyle(
        'ColumnHeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceAfter=5
    )

    # Texte des colonnes du bas (Plus petit, aligné gauche)
    detail_style = ParagraphStyle(
        'DetailStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.black,
        alignment=TA_LEFT
    )
    
    # Pied de page (Ville code postal)
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceBefore=10
    )
    
    # =================== 1. EN-TÊTE (TITRE) ===================
    titre = Paragraph("MON CANAPÉ MAROCAIN", title_style)
    elements.append(titre)
    elements.append(Spacer(1, 0.5*cm))
    
    # =================== 2. BLOC INFORMATIONS (HAUT) ===================
    # [cite_start]Construction des chaînes de texte selon la configuration [cite: 1, 2, 3, 4, 5, 6, 7, 8, 9, 11]
    
    # Dimensions formatées
    type_canape = config['type_canape']
    dims = config['dimensions']
    if "U" in type_canape:
        dim_str = f"{dims.get('ty',0)}x{dims.get('tx',0)}x{dims.get('tz',0)}"
    elif "L" in type_canape:
        dim_str = f"{dims.get('ty',0)}x{dims.get('tx',0)}"
    else:
        dim_str = f"{dims.get('tx',0)}x{dims.get('profondeur',0)}"
        
    # Infos techniques regroupées
    mousse = config['options'].get('type_mousse', 'HR35')
    infos_techniques = [
        f"<b>Dimensions:</b> {dim_str} cm",
        f"<b>Confort:</b> {mousse} (Haute résilience - Garantie 6 ans)",
        f"<b>Dossiers:</b> {'Avec' if config['options'].get('dossier_bas') else 'Sans'}",
        f"<b>Accoudoirs:</b> {'Oui' if config['options'].get('acc_left') or config['options'].get('acc_right') else 'Non'}"
    ]
    
    # Infos client
    client = config['client']
    infos_client = []
    if client['nom']: infos_client.append(f"<b>Nom:</b> {client['nom']}")
    if client['email']: infos_client.append(f"<b>Email:</b> {client['email']}")
    
    # Assemblage du texte centré
    full_header_text = "<br/>".join(infos_techniques)
    if infos_client:
        full_header_text += "<br/><br/><b>Informations Client:</b><br/>" + "<br/>".join(infos_client)
        
    elements.append(Paragraph(full_header_text, header_info_style))
    
    # [cite_start]Petit texte descriptif mousse (optionnel, pour imiter l'exemple) [cite: 12, 13, 14]
    desc_mousse = f"""<br/>La mousse {mousse} est une mousse haute résilience. 
    Elle est semi-ferme confortable, parfaite pour les adeptes des salons confortables."""
    elements.append(Paragraph(f"<i>{desc_mousse}</i>", header_info_style))
    
    elements.append(Spacer(1, 0.5*cm))

    # =================== 3. SCHÉMA (CENTRE) ===================
    if schema_image:
        try:
            img = Image(schema_image)
            # Calcul pour que l'image prenne une bonne largeur sans dépasser
            # Largeur page A4 = 21cm - marges (3cm) = 18cm dispo
            max_width = 17 * cm 
            aspect_ratio = img.imageHeight / float(img.imageWidth)
            img.drawWidth = max_width
            img.drawHeight = max_width * aspect_ratio
            
            elements.append(img)
            elements.append(Spacer(1, 0.5*cm))
        except Exception:
            elements.append(Paragraph("<i>(Aperçu du schéma non disponible)</i>", header_info_style))

    # =================== 4. TABLEAU DE PRIX (DÉTAILS DU DEVIS) ===================
    # Titre
    elements.append(Paragraph("<b>DÉTAILS DU DEVIS</b>", ParagraphStyle('SubTitle', parent=title_style, fontSize=12, alignment=TA_LEFT)))
    
    # Données du tableau
    prix_data = [['Désignation', 'Montant']]
    for item, prix in prix_details['details'].items():
        prix_data.append([item, f"{prix:.2f} €"])
    
    # Totaux
    prix_data.append(['', '']) # Ligne vide
    prix_data.append(['Sous-Total HT', f"{prix_details['sous_total']:.2f} €"])
    prix_data.append(['TVA (20%)', f"{prix_details['tva']:.2f} €"])
    prix_data.append(['TOTAL TTC', f"{prix_details['total_ttc']:.2f} €"])
    
    # Style du tableau (minimaliste et propre)
    table_prix = Table(prix_data, colWidths=[13*cm, 4*cm])
    table_style = [
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # En-tête gras
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black), # Ligne sous l'en-tête
        ('LINEBELOW', (0, -2), (-1, -2), 0.5, colors.grey), # Ligne avant total
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), # Total en gras
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
    ]
    table_prix.setStyle(TableStyle(table_style))
    elements.append(table_prix)
    elements.append(Spacer(1, 1*cm))

    # =================== 5. BAS DE PAGE (2 COLONNES) ===================
    # [cite_start]Reproduit exactement le contenu des exemples fournis [cite: 36, 37, 38, 39, 40, 45]

    # --- Colonne Gauche : Ce que le tarif comprend ---
    col_gauche = []
    col_gauche.append(Paragraph("Il faut savoir que le tarif remisé comprend :", column_header_style))
    
    inclus_items = [
        "La livraison en bas d'immeuble",
        "La fabrication 100% artisanale et en France",
        "Le choix du tissu n'impacte pas le devis",
        "Possibilité de régler de 2 à 6 fois sans frais",
        "Délai de livraison entre 5 à 7 semaines",
        "Housses de matelas et coussins déhoussables"
    ]
    for item in inclus_items:
        # On ajoute une puce visuelle ou textuelle
        col_gauche.append(Paragraph(f"• {item}", detail_style))

    # --- Colonne Droite : Cotations techniques ---
    col_droite = []
    col_droite.append(Paragraph("Voici le détail des cotations de votre canapé :", column_header_style))
    
    # Récupération dynamique si possible, sinon valeurs standards de l'exemple
    h_mousse = config['options'].get('epaisseur', 25)
    
    cotations_items = [
        "15 cm = largeur d'accoudoir, hauteur = 60 cm",
        "10 cm = largeur de dossier, hauteur = 70 cm",
        "65 cm / 80 cm / 90 cm = taille des coussins",
        f"{config['dimensions']['profondeur']} cm = profondeur d'assise",
        f"{46 if h_mousse > 20 else 40} cm = hauteur d'assises, hauteur de mousse = {h_mousse} cm"
    ]
    for item in cotations_items:
        col_droite.append(Paragraph(f"{item}", detail_style))

    # Mise en page en tableau invisible pour les colonnes
    table_footer = Table([[col_gauche, col_droite]], colWidths=[9*cm, 9*cm])
    table_footer.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    
    elements.append(table_footer)
    elements.append(Spacer(1, 0.5*cm))
    
    # =================== 6. FOOTER VILLE ===================
    [cite_start]elements.append(Paragraph("FRÉVENT 62270", footer_style)) # [cite: 46]
    
    # Génération
    doc.build(elements)
    buffer.seek(0)
    return buffer
