from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
# Assurez-vous d'importer PageBreak si vous l'utilisez, et Image pour le schéma
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO

def generer_pdf_devis(config, prix_details, schema_image=None):
    """
    Génère un PDF de devis professionnel
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- DÉFINITION DES STYLES ---

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # MODIFICATION 1 : Ajout de alignment=TA_CENTER pour centrer Dimensions, Caractéristiques, Client
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=8,
        spaceBefore=4,
        leftIndent=0,
        alignment=TA_CENTER  # <--- C'est ici que ça se joue pour le centrage
    )
    
    # AJOUT : Un style aligné à gauche spécifiquement pour les colonnes du bas
    # (car des listes à puces centrées sont difficiles à lire)
    column_header_style = ParagraphStyle(
        'ColumnHeaderStyle',
        parent=section_style,
        alignment=TA_LEFT
    )

    detail_style = ParagraphStyle(
        'DetailStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=4,
        leftIndent=10,
        alignment=TA_LEFT
    )
    
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    # =================== TITRE ===================
    titre = Paragraph("MON CANAPÉ MAROCAIN", title_style)
    elements.append(titre)
    elements.append(Spacer(0.5, 0.5*cm))
    
    # =================== DIMENSIONS DU CANAPÉ (Sera centré via section_style) ===================
    type_canape = config['type_canape']
    dimensions = config['dimensions']
    type_text = f"<b>Configuration :</b> {type_canape}"
    
    # Logique corrigée pour les dimensions (L et U)
    if "U" in type_canape:
        dim_text = f"<b>Dimensions :</b> {dimensions['ty']}x{dimensions['tx']}x{dimensions['tz']}cm"
    elif "L" in type_canape:
        dim_text = f"<b>Dimensions :</b> {dimensions['ty']}x{dimensions['tx']}cm"
    else:
        dim_text = f"<b>Dimensions :</b> {dimensions['tx']}cm"
    
    elements.append(Paragraph(type_text, section_style))
    elements.append(Paragraph(dim_text, section_style))

    # =================== CARACTÉRISTIQUES (Sera centré) ===================
    elements.append(Paragraph(f"<b>Profondeur :</b> {dimensions['profondeur']}cm", section_style))
    
    mousse = config['options'].get('type_mousse', 'D25')
    elements.append(Paragraph(f"<b>Mousse :</b> {mousse}", section_style))
    
    has_dossier = (config['options'].get('dossier_left', False) or 
                   config['options'].get('dossier_bas', False) or 
                   config['options'].get('dossier_right', False))
    elements.append(Paragraph(f"<b>Dossier :</b> {'Avec' if has_dossier else 'Sans'}", section_style))
    
    nb_accoudoirs = sum([config['options'].get('acc_left', False),
                         config['options'].get('acc_right', False),
                         config['options'].get('acc_bas', False)])
    elements.append(Paragraph(f"<b>Accoudoirs :</b> {nb_accoudoirs}", section_style))
    
    # =================== INFORMATIONS CLIENT (Sera centré) ===================
    if config['client']['nom']:
        elements.append(Paragraph(f"<b>Client :</b> {config['client']['nom']}", section_style))
        if config['client']['email']:
            elements.append(Paragraph(f"<b>Email :</b> {config['client']['email']}", section_style))
    
    elements.append(Spacer(1, 0.5*cm))

    # =================== SCHÉMA (Centré par défaut car c'est une image) ===================
    if schema_image:
        try:
            img = Image(schema_image)
            max_width = 14 * cm # Un peu plus petit pour bien centrer visuellement
            aspect_ratio = img.imageHeight / float(img.imageWidth)
            img.drawWidth = max_width
            img.drawHeight = max_width * aspect_ratio
            
            elements.append(Spacer(1, 0.2*cm))
            elements.append(img)
            elements.append(Spacer(1, 0.5*cm))
        except Exception:
            pass
            
# =================== MODIFICATION 2 : COLONNES CÔTE À CÔTE ===================
    # Pour mettre deux éléments côte à côte, on crée un tableau invisible de 1 ligne et 2 colonnes.
    # Chaque cellule contient une liste d'éléments (Paragraphs).

    # --- Colonne Gauche : Inclus ---
    col_gauche_content = []
    col_gauche_content.append(Paragraph("<b>Le tarif comprend :</b>", column_header_style))
    col_gauche_content.append(Spacer(1, 0.2*cm))
    
    inclus_items = [
        "Livraison en bas d'immeuble",
        "Fabrication 100% artisanale",
        "Le choix du tissu n'impacte pas le devis",
        "Possibilité de régler de 2 à 6 fois sans frais",
        "Délai de livraison entre 5 à 7 semaines",
        "Housses de matelas et coussins déhoussables"
    ]
    for item in inclus_items:
        col_gauche_content.append(Paragraph(f"• {item}", detail_style))

    # --- Colonne Droite : Cotations ---
    col_droite_content = []
    col_droite_content.append(Paragraph("<b>Détail des cotations :</b>", column_header_style))
    col_droite_content.append(Spacer(1, 0.2*cm))
    
    cotations_items = [
        "Accoudoir : 15cm large / 60cm haut",
        "Dossier : 10cm large / 70cm haut",
        "Coussins : 65/80/90cm large",
        "Profondeur assise : 70cm",
        "Hauteur assise : 46cm",
        "Hauteur mousse : 25 cm"
    ]
    for item in cotations_items:
        col_droite_content.append(Paragraph(f"• {item}", detail_style))

    # Création du tableau conteneur pour les deux colonnes
    # On utilise la largeur restante (environ 17-18cm) divisée par 2
    table_colonnes = Table([[col_gauche_content, col_droite_content]], colWidths=[8.5*cm, 8.5*cm])
    
    table_colonnes.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'), # Aligner le contenu en haut
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    elements.append(table_colonnes)
    elements.append(Spacer(1, 1*cm))

    # =================== TABLEAU DES PRIX ===================
    # Titre du tableau (Centré)
    elements.append(Paragraph("<b>DÉTAILS DU DEVIS</b>", section_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # ... (Logique du tableau de prix inchangée) ...
    prix_data = [['Désignation', 'Prix (€)']]
    for item, prix in prix_details['details'].items():
        prix_data.append([item, f"{prix:.2f} €"])
    
    prix_data.append(['', ''])
    prix_data.append(['SOUS-TOTAL HT', f"{prix_details['sous_total']:.2f} €"])
    prix_data.append(['TVA (20%)', f"{prix_details['tva']:.2f} €"])
    prix_data.append(['', ''])
    prix_data.append(['TOTAL TTC', f"{prix_details['total_ttc']:.2f} €"])
    
    table_prix = Table(prix_data, colWidths=[12*cm, 5*cm])
    
    # Style du tableau de prix (identique à avant)
    table_style = [
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
    ]
    sous_total_row = len(prix_data) - 4
    table_style.extend([
        ('FONTNAME', (0, sous_total_row), (-1, sous_total_row + 1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, sous_total_row), (-1, sous_total_row), 1, colors.black),
    ])
    total_row = len(prix_data) - 1
    table_style.extend([
        ('FONTNAME', (0, total_row), (-1, total_row), 'Helvetica-Bold'),
        ('FONTSIZE', (0, total_row), (-1, total_row), 14),
        ('LINEABOVE', (0, total_row), (-1, total_row), 2, colors.black),
    ])
    
    table_prix.setStyle(TableStyle(table_style))
    elements.append(table_prix)
    elements.append(Spacer(1, 1.5*cm))

    # =================== FOOTER ===================
    elements.append(Paragraph("<b>FRÉVENT 62270</b>", footer_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
