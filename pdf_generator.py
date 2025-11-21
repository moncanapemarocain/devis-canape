from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO

def generer_pdf_devis(config, prix_details, schema_image=None):
    """
    Génère un PDF de devis (1 page) avec un pied de page fixe en bas.
    """
    buffer = BytesIO()
    
    # IMPORTANT : On augmente la marge du bas (bottomMargin) à 6cm
    # pour réserver l'espace nécessaire au pied de page fixe.
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=1*cm, leftMargin=1*cm,
                           topMargin=1*cm, bottomMargin=6*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- DÉFINITION DES STYLES ---
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=14, textColor=colors.black, spaceAfter=5, alignment=TA_CENTER, fontName='Helvetica-Bold')
    header_info_style = ParagraphStyle('HeaderInfo', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.black, alignment=TA_CENTER)
    price_style = ParagraphStyle('PriceStyle', parent=styles['Heading2'], fontSize=16, alignment=TA_CENTER, fontName='Helvetica', textColor=colors.black, spaceBefore=10, spaceAfter=10)
    
    # Styles pour le pied de page
    column_header_style = ParagraphStyle('ColumnHeaderStyle', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', alignment=TA_LEFT, spaceAfter=2)
    detail_style = ParagraphStyle('DetailStyle', parent=styles['Normal'], fontSize=10, leading=10, textColor=colors.black, alignment=TA_LEFT)
    footer_style = ParagraphStyle('FooterStyle', parent=styles['Normal'], fontSize=10, textColor=colors.black, alignment=TA_CENTER)

    # --- FONCTION INTERNE POUR DESSINER LE PIED DE PAGE FIXE ---
    def draw_footer(canvas, doc):
        canvas.saveState()
        
        # 1. Préparation des données des colonnes (ex-Partie 5)
        
        # Colonne Gauche
        col_gauche = []
        col_gauche.append(Paragraph("Il faut savoir que le tarif comprend :", column_header_style))
        inclus_items = [
            "Livraison bas d'immeuble",
            "Fabrication 100% artisanale France",
            "Choix du tissu qui n'impacte pas le devis",
            "Possibilité de payer en 2 à 6 fois sans frais",
            "Livraison en bas d'immeuble en 5 à 7 semaines",
            "Housses de matelas et coussins déhoussables"
        ]
        for item in inclus_items:
            col_gauche.append(Paragraph(f"• {item}", detail_style))

        # Colonne Droite
        col_droite = []
        col_droite.append(Paragraph("Détail des cotations du canapé:", column_header_style))
        
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

        # Création du tableau pour les colonnes
        table_footer = Table([[col_gauche, col_droite]], colWidths=[9.5*cm, 9.5*cm])
        table_footer.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        # Calcul de la taille et dessin
        # On le dessine à 2cm du bas de la page (juste au-dessus de la ville)
        w, h = table_footer.wrap(doc.width, doc.bottomMargin)
        table_footer.drawOn(canvas, doc.leftMargin, 1.5*cm)
        
        # 2. Ville (ex-Partie 6) - Tout en bas
        p_ville = Paragraph("FRÉVENT 62270", footer_style)
        w_ville, h_ville = p_ville.wrap(doc.width, doc.bottomMargin)
        p_ville.drawOn(canvas, doc.leftMargin, 0.5*cm)
        
        canvas.restoreState()

    # =================== CONTENU DU DOCUMENT ===================
    
    # 1. TITRE
    elements.append(Paragraph("MON CANAPÉ MAROCAIN", title_style))
    
    # 2. INFORMATIONS (HAUT)
    type_canape = config['type_canape']
    dims = config['dimensions']
    
    if "U" in type_canape:
        dim_str = f"{dims.get('ty',0)} x {dims.get('tx',0)} x {dims.get('tz',0)}"
    elif "L" in type_canape:
        dim_str = f"{dims.get('ty',0)} x {dims.get('tx',0)}"
    else:
        dim_str = f"{dims.get('tx',0)} x {dims.get('profondeur',0)}"
        
    mousse_type = config['options'].get('type_mousse', 'HR35')
    dossier_txt = 'Avec' if config['options'].get('dossier_bas') else 'Sans'
    acc_txt = 'Oui' if (config['options'].get('acc_left') or config['options'].get('acc_right')) else 'Non'

    lignes_info = [
        f"<b>Dimensions:</b> {dim_str} cm",
        f"<b>Confort:</b> {mousse_type}",
        f"<b>Dossiers:</b> {dossier_txt}",
        f"<b>Accoudoirs:</b> {acc_txt}"
    ]
    
    client = config['client']
    if client['nom']: lignes_info.append(f"<b>Nom:</b> {client['nom']}")
    if client['email']: lignes_info.append(f"<b>Email:</b> {client['email']}")
    
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
    elements.append(Paragraph(f"<i>{texte_mousse}</i>", header_info_style))
    elements.append(Spacer(1, 0.3*cm))

    # 3. SCHÉMA
    if schema_image:
        try:
            img = Image(schema_image)
            avail_width = 18 * cm
            avail_height = 10 * cm
            
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

    elements.append(Spacer(1, 0.5*cm))

    # 4. PRIX
    montant_ttc = f"{prix_details['total_ttc']:.2f} €"
    elements.append(Paragraph(f"PRIX TOTAL TTC : {montant_ttc}", price_style))
    elements.append(Paragraph("<hr width='100%' color='black'/>", styles['Normal']))

    # Note : On n'ajoute plus les parties 5 et 6 ici (colonnes et footer)
    # Elles sont gérées par la fonction draw_footer appelée via onFirstPage
    
    # GÉNÉRATION AVEC CALLBACK POUR LE FOOTER
    doc.build(elements, onFirstPage=draw_footer)
    buffer.seek(0)
    return buffer
