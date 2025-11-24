"""
Générateur de PDF pour les devis de canapés marocains
VERSION MODIFIÉE : Schéma agrandi à 80% de la largeur du PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from io import BytesIO
from PIL import Image as PILImage

def generer_pdf_devis(config, prix_details, schema_image=None):
    """
    Génère un PDF de devis avec schéma agrandi à 80% de la largeur
    """
    buffer = BytesIO()
    
    # Configuration de la page A4
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style titre principal
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#372E2B'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Style sous-titre
    style_subtitle = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#8C6F63'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    # Style texte normal
    style_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#372E2B'),
        spaceAfter=6,
        fontName='Helvetica'
    )
    
    # Style bullet points
    style_bullet = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#372E2B'),
        leftIndent=20,
        spaceAfter=4,
        fontName='Helvetica'
    )
    
    # Construction du contenu
    story = []
    
    # Titre principal
    story.append(Paragraph("MON CANAPÉ MAROCAIN", style_title))
    
    # Informations principales
    dimensions = config['dimensions']
    dim_text = f"{dimensions['tx']} x {dimensions['ty']} x {dimensions['tz']} cm" if dimensions['tz'] > 0 else f"{dimensions['tx']} cm"
    
    info_data = [
        ["Dimensions:", dim_text],
        ["Confort:", config['options']['type_mousse']],
        ["Dossiers:", "Avec" if config['options']['dossier_bas'] else "Sans"],
        ["Accoudoirs:", "Oui" if config['options']['acc_left'] or config['options']['acc_right'] else "Non"],
        ["Nom:", config['client']['nom']]
    ]
    
    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#372E2B')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Description de la mousse
    mousse_desc = {
        'D25': "La mousse D25 est une mousse polyuréthane de 25kg/m3. Elle offre un bon confort pour un usage quotidien.",
        'D30': "La mousse D30 est une mousse polyuréthane de 30kg/m3. Elle est ultra ferme, idéale pour ceux qui recherchent un canapé très ferme.",
        'HR35': "La mousse HR35 est une mousse haute résilience de 35kg/m3. Elle offre un excellent soutien et une durabilité supérieure.",
        'HR45': "La mousse HR45 est une mousse haute résilience de 45kg/m3. C'est notre mousse la plus premium, offrant le meilleur confort et la plus longue durée de vie."
    }
    
    mousse_type = config['options']['type_mousse']
    if mousse_type in mousse_desc:
        story.append(Paragraph(mousse_desc[mousse_type], style_normal))
        story.append(Spacer(1, 0.5*cm))
    
    # Schéma du canapé - 🔧 MODIFICATION : 80% de la largeur
    if schema_image:
        try:
            # Ouvrir l'image avec PIL
            pil_img = PILImage.open(schema_image)
            
            # 🔧 LARGEUR MAXIMALE : 80% de la page A4 (21cm - marges 4cm = 17cm * 0.80 = 13.6cm)
            max_width = 13.6 * cm
            max_height = 16 * cm  # Hauteur augmentée pour proportions
            
            # Calculer les dimensions en préservant le ratio
            img_width, img_height = pil_img.size
            aspect = img_height / float(img_width)
            
            # Calculer la largeur finale (on vise 80% de la page)
            final_width = max_width
            final_height = final_width * aspect
            
            # Si la hauteur dépasse, ajuster
            if final_height > max_height:
                final_height = max_height
                final_width = final_height / aspect
            
            # Créer l'image ReportLab
            img = Image(schema_image, width=final_width, height=final_height)
            
            # Centrer l'image
            img.hAlign = 'CENTER'
            
            # Ajouter le titre du schéma
            type_canape = config['type_canape']
            variant_info = ""
            if 'Sans Angle' in type_canape:
                variant = 'v2' if dimensions['tx'] >= dimensions['ty'] else 'v1'
                variant_info = f" [{variant}]"
            
            schema_title = f"Canapé {type_canape}{variant_info} — "
            
            if type_canape == "Simple":
                schema_title += f"tx={dimensions['tx']} — prof={dimensions['profondeur']}"
            elif 'L' in type_canape:
                schema_title += f"tx={dimensions['tx']} / ty={dimensions['ty']} — prof={dimensions['profondeur']}"
            elif 'U' in type_canape:
                schema_title += f"tx={dimensions['tx']} / ty(left)={dimensions['ty']} / tz(right)={dimensions['tz']} — prof={dimensions['profondeur']}"
            
            # Ajouter méridienne si présente
            if config['options'].get('meridienne_len', 0) > 0:
                meridienne_side_text = 'left' if config['options'].get('meridienne_side') == 'left' else 'right'
                schema_title += f" — méridienne ={meridienne_side_text}"
            else:
                schema_title += " — méridienne =0"
            
            story.append(Paragraph(schema_title, style_subtitle))
            story.append(Spacer(1, 0.3*cm))
            story.append(img)
            story.append(Spacer(1, 0.5*cm))
            
        except Exception as e:
            story.append(Paragraph(f"Erreur lors de l'insertion du schéma: {str(e)}", style_normal))
            story.append(Spacer(1, 0.5*cm))
    
    # Prix total en grand
    prix_style = ParagraphStyle(
        'PrixStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#372E2B'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph(f"PRIX TOTAL TTC : {prix_details['total_ttc']:.2f} €", prix_style))
    
    # Saut de page pour les informations complémentaires
    story.append(PageBreak())
    
    # Informations complémentaires
    story.append(Paragraph("Il faut savoir que le tarif comprend :", style_subtitle))
    story.append(Spacer(1, 0.3*cm))
    
    inclus = [
        "Livraison bas d'immeuble",
        "Fabrication 100% artisanale France",
        "Choix du tissu n'impacte pas le devis",
        "Paiement 2 à 6 fois sans frais",
        "Livraison 5 à 7 semaines",
        "Housses déhoussables"
    ]
    
    for item in inclus:
        story.append(Paragraph(f"• {item}", style_bullet))
    
    story.append(Spacer(1, 0.5*cm))
    
    # Détails techniques
    story.append(Paragraph("Détail des cotations :", style_subtitle))
    story.append(Spacer(1, 0.3*cm))
    
    details = [
        "Accoudoir: 15cm large / 60cm haut",
        "Dossier: 10cm large / 70cm haut",
        "Coussins: 65/80/90cm large",
        f"Profondeur assise: {dimensions['profondeur']} cm",
        f"Hauteur assise: 46 cm (Mousse {config['options']['epaisseur']}cm)"
    ]
    
    for item in details:
        story.append(Paragraph(f"• {item}", style_bullet))
    
    # Contact
    story.append(Spacer(1, 1*cm))
    
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#8C6F63'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    if config['client'].get('departement'):
        story.append(Paragraph(config['client']['departement'], contact_style))
    
    # Génération du PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer
