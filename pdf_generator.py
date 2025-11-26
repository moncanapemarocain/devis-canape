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


def generer_pdf_devis(config, prix_details, schema_image=None, breakdown_rows=None,
                      reduction_ttc=0.0, show_detail_devis=True, show_detail_cr=True):
    """
    Génère un PDF de devis. La première page contient le résumé et le schéma. Des pages
    supplémentaires peuvent être ajoutées pour présenter le détail du prix (page 2) et
    le détail du coût de revient (page 3). Ces pages ne sont ajoutées que si
    ``show_detail_devis`` et ``show_detail_cr`` sont à ``True``.

    :param config: Configuration du canapé et des options.
    :param prix_details: Dictionnaire renvoyé par ``calculer_prix_total`` contenant les totaux et
        éventuellement des listes ``calculation_details`` et ``calculation_details_cr``.
    :param schema_image: Image du schéma généré (objet BytesIO ou chemin), optionnel.
    :param breakdown_rows: Tableau simple du détail du devis, optionnel.
    :param reduction_ttc: Montant de réduction TTC appliqué.
    :param show_detail_devis: Booléen contrôlant l'ajout de la page 2 détaillant le prix.
    :param show_detail_cr: Booléen contrôlant l'ajout de la page 3 détaillant le coût de
        revient.
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

    # Style spécifique pour les en-têtes du pied de page (« Il faut savoir que le tarif comprend »
    # et « Détail des cotations »). Il hérite de column_header_style mais réduit la taille de
    # police de deux points pour correspondre aux exigences utilisateur.
    footer_header_style = ParagraphStyle(
        'FooterHeaderStyle', parent=column_header_style,
        fontSize=column_header_style.fontSize - 2,
        alignment=TA_LEFT,
        fontName=column_header_style.fontName,
        spaceAfter=column_header_style.spaceAfter
    )

    # --- FONCTION INTERNE POUR DESSINER LE PIED DE PAGE FIXE ---
    def draw_footer(canvas, doc):
        canvas.saveState()
        
        # 1. Préparation des données des colonnes
        
        # Colonne Gauche
        col_gauche = []
        col_gauche.append(Paragraph("Il faut savoir que le tarif comprend :", footer_header_style))
        inclus_items = [
            # "Livraison bas d'immeuble" a été retiré conformément aux spécifications
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
        col_droite.append(Paragraph("Détail des cotations :", footer_header_style))
        
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
    # Le titre principal "MON CANAPÉ MAROCAIN" est omis selon les directives.
    
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

    # Déterminer le nombre d'accoudoirs (0, 1 ou 2)
    acc_count = 0
    if config.get('options', {}).get('acc_left', False):
        acc_count += 1
    if config.get('options', {}).get('acc_right', False):
        acc_count += 1
    # Afficher "Avec" s'il y a au moins un accoudoir, sinon "Sans"
    acc_txt = "Avec" if acc_count > 0 else "Sans"

    # Déterminer les positions de dossiers : bas, gauche, droite
    opts = config.get('options', {})
    dossier_positions = []
    if opts.get('dossier_bas', False):
        dossier_positions.append('bas')
    if opts.get('dossier_left', False) or opts.get('dossier_gauche', False):
        dossier_positions.append('gauche')
    if opts.get('dossier_right', False) or opts.get('dossier_droite', False):
        dossier_positions.append('droite')
    # Si des dossiers sont présents (peu importe leur nombre ou position), afficher « Avec », sinon « Sans »
    if len(dossier_positions) == 0:
        dossier_txt = 'Sans'
    else:
        dossier_txt = 'Avec'

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

        # Ajouter un espace avant le récapitulatif du devis. L'utilisateur souhaite que la section
        # « Détail du devis » soit légèrement plus basse par rapport au schéma ; on augmente donc l'espace.
        elements.append(Spacer(1, 1.0 * cm))

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
    elif type_coussins == '80-90':
        # Nouvelle option 80-90 : chaque côté peut être optimisé en 80 ou 90 cm
        taille_coussins = "80/90 cm"
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

    # Déterminer l'étiquette de la ligne coussins. Pour les modèles valise/petit/grand, on utilise
    # « Coussins valises » afin de refléter le type choisi ; sinon « Coussins ».
    coussins_label = "Coussins"
    if type_coussins in ['valise', 'p', 'g']:
        coussins_label = "Coussins valises"

    # Préparer des lignes supplémentaires pour traversins, coussins déco et surmatelas dans le tableau récapitulatif.
    traversins_line = ""
    deco_line = ""
    surmatelas_line = ""
    # Les informations détaillées se trouvent dans prix_details['calculation_details'] (si disponible)
    details_list = prix_details.get('calculation_details', None)
    if details_list:
        try:
            for entry in details_list:
                cat = entry.get('category', '').lower()
                item = entry.get('item', '').lower()
                qty = entry.get('quantity', 0)
                if cat == 'traversin' and qty:
                    # Les traversins ont des dimensions fixes 70x30 cm
                    traversins_line = f"Traversins : {qty} traversin{'s' if qty > 1 else ''} de 70x30cm"
                elif cat == 'surmatelas' and qty:
                    # Les surmatelas sont spécifiés comme "surmatelas confort" dans le devis
                    surmatelas_line = f"Surmatelas : {qty} surmatelas confort"
                elif cat == 'cushion' and 'déco' in item and qty:
                    deco_line = f"Coussins déco : {qty}"
        except Exception:
            pass

    # === Construction de la section « Détail du devis » ===
    # Création d'un tableau ligne par ligne pour aligner correctement les informations de gauche et de droite.
    table_rows = []
    # Ligne 0 : titre à gauche, cellule vide à droite
    table_rows.append([Paragraph("Détail du devis :", column_header_style), Paragraph("", detail_style)])
    # Ligne 1 : Dimensions et Coussins
    # Générer le descriptif des coussins d'assise en se basant sur les détails de calcul.
    coussins_descr = ""
    # Construire un dictionnaire du nombre de coussins par taille (hors coussins déco)
    cushion_counts = {}
    if details_list:
        try:
            for entry in details_list:
                if entry.get('category', '').lower() == 'cushion':
                    item_name = entry.get('item', '').lower()
                    qty = entry.get('quantity', 0)
                    # Ignorer les coussins déco
                    if 'déco' in item_name:
                        continue
                    # Déterminer un identifiant de taille : soit une valeur numérique (avant 'cm'), soit 'valise', 'petit modèle' ou 'grand modèle'
                    parts = item_name.split()
                    size_label = None
                    # Chercher une taille numérique
                    for p in parts:
                        t = p.replace('cm', '')
                        if t.isdigit():
                            size_label = f"{t}cm"
                            break
                    # Si aucune taille numérique trouvée, identifier les coussins spéciaux
                    if size_label is None:
                        if 'valise' in item_name:
                            size_label = 'valise'
                        elif 'petit' in item_name:
                            size_label = 'petit modèle'
                        elif 'grand' in item_name:
                            size_label = 'grand modèle'
                    if size_label and qty:
                        cushion_counts[size_label] = cushion_counts.get(size_label, 0) + qty
        except Exception:
            pass
    # Construire la chaîne descriptive si des données sont disponibles
    if cushion_counts:
        # Trier les tailles par ordre numérique si possible (ex : 65cm, 80cm, 90cm),
        # puis placer les libellés non numériques (valise, petit modèle, grand modèle) à la fin.
        import re  # import local pour trier les libellés de coussins
        def _cushion_sort_key(label: str):
            m = re.match(r'^(\d+(?:\.\d+)?)cm$', label)
            if m:
                # Clé numérique pour tri ascendant
                return (0, float(m.group(1)))
            # Les libellés non numériques (valise, petit modèle, grand modèle) sont classés après
            return (1, label)
        parts = []
        for size in sorted(cushion_counts.keys(), key=_cushion_sort_key):
            # Préparer l'affichage : pour les tailles numériques, séparer la valeur et l'unité ; sinon utiliser le libellé tel quel
            if re.match(r'^(\d+(?:\.\d+)?)cm$', size):
                disp = f"{size[:-2]} cm"
            else:
                disp = size
            parts.append(f"{cushion_counts[size]} x {disp}")
        coussins_descr = ", ".join(parts)
    else:
        # Si aucun détail, utiliser le nombre et la taille des coussins saisis
        if nb_coussins_assise is not None:
            coussins_descr = f"{nb_coussins_assise} x {taille_coussins}"
        else:
            coussins_descr = "-"
    right_coussins = Paragraph(f"{coussins_label} : {coussins_descr}", detail_style)
    table_rows.append([Paragraph(f"Dimensions : {dim_str} cm", detail_style), right_coussins])
    # Ligne 2 : Mousse et éventuels traversins, coussins déco ou surmatelas
    # Construire le contenu de la colonne de droite : concaténer les lignes non vides avec des sauts de ligne
    extra_lines = []
    if traversins_line:
        extra_lines.append(traversins_line)
    if deco_line:
        extra_lines.append(deco_line)
    if surmatelas_line:
        extra_lines.append(surmatelas_line)
    right_second_cell_content = "<br/>".join(extra_lines) if extra_lines else ""
    table_rows.append([
        Paragraph(f"Mousse : {mousse_type}", detail_style),
        Paragraph(right_second_cell_content, detail_style)
    ])
    # Ligne 3 : Accoudoirs et Réduction
    table_rows.append([Paragraph(f"Accoudoirs : {acc_txt}", detail_style), Paragraph(f"Réduction : {reduction_ttc_val:.2f} €", detail_style)])
    # Ligne 4 : Dossiers et Prix final
    table_rows.append([Paragraph(f"Dossiers : {dossier_txt}", detail_style), Paragraph(f"Prix canapé d'angle : <b>{montant_ttc}</b>", detail_style)])
    # Ligne 5 : Profondeur et Prix avant réduction
    # Affichage de la profondeur issue de la configuration sans précision « d'assise »
    profondeur_val = dims.get('profondeur', 0)
    table_rows.append([Paragraph(f"Profondeur : {profondeur_val}cm", detail_style), Paragraph(f"Prix avant réduction : {prix_avant_reduc}", detail_style)])
    devis_table = Table(table_rows, colWidths=[9.5 * cm, 9.5 * cm])
    devis_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(devis_table)

    # Préparer les données détaillées pour le prix et le coût de revient
    calculation_details = prix_details.get('calculation_details', None)
    cr_details = prix_details.get('calculation_details_cr', None)

    # Gestion conditionnelle des pages 2 et 3 en fonction des options
    if show_detail_devis:
        # Priorité à la liste complète de détails
        if calculation_details:
            elements.append(PageBreak())
            elements.append(Paragraph("Détail des calculs du prix", title_style))
            elements.append(Spacer(1, 0.3 * cm))
            # Créer un tableau avec colonnes : Catégorie, Article, Quantité, Prix unitaire, Formule, Total
            table_data = []
            # En-têtes
            table_data.append([
                Paragraph('<b>Catégorie</b>', styles['Normal']),
                Paragraph('<b>Article</b>', styles['Normal']),
                Paragraph('<b>Qté</b>', styles['Normal']),
                Paragraph('<b>Prix unitaire</b>', styles['Normal']),
                Paragraph('<b>Formule</b>', styles['Normal']),
                Paragraph('<b>Total</b>', styles['Normal'])
            ])
            # Rows for each calculation detail
            for entry in calculation_details:
                cat = entry.get('category', '')
                item = entry.get('item', '')
                qty = entry.get('quantity', '')
                unit = entry.get('unit_price', '')
                formula = entry.get('formula', '')
                total = entry.get('total_price', '')
                # Ensure floats are formatted with 2 decimals
                if isinstance(unit, (int, float)):
                    unit = f"{unit:.2f} €"
                if isinstance(total, (int, float)):
                    total = f"{total:.2f} €"
                table_data.append([cat.capitalize(), item, qty, unit, formula, total])
            # Append summary totals at the end
            table_data.append([
                Paragraph('<b>Total HT</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('prix_ht', 0.0):.2f} €"
            ])
            table_data.append([
                Paragraph('<b>TVA (20 %)</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('tva', 0.0):.2f} €"
            ])
            table_data.append([
                Paragraph('<b>Total TTC</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('total_ttc', 0.0):.2f} €"
            ])
            # Define column widths (6 columns)
            col_widths = [3.0 * cm, 5.0 * cm, 1.5 * cm, 3.0 * cm, 4.5 * cm, 3.0 * cm]
            detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F5')),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # quantity column
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),  # unit price column
                ('ALIGN', (5, 1), (5, -1), 'RIGHT'),  # total column
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            elements.append(detail_table)

            # Si on souhaite également voir le coût de revient, on l'ajoute sur une page suivante
            if show_detail_cr and cr_details:
                elements.append(PageBreak())
                elements.append(Paragraph("Détail des calculs du coût de revient", title_style))
                elements.append(Spacer(1, 0.3 * cm))
                cr_table_data = []
                cr_table_data.append([
                    Paragraph('<b>Catégorie</b>', styles['Normal']),
                    Paragraph('<b>Article</b>', styles['Normal']),
                    Paragraph('<b>Qté</b>', styles['Normal']),
                    Paragraph('<b>Coût unitaire</b>', styles['Normal']),
                    Paragraph('<b>Formule</b>', styles['Normal']),
                    Paragraph('<b>Total</b>', styles['Normal'])
                ])
                for entry in cr_details:
                    cat = entry.get('category', '')
                    item = entry.get('item', '')
                    qty = entry.get('quantity', '')
                    unit = entry.get('unit_price', '')
                    formula = entry.get('formula', '')
                    total = entry.get('total_price', '')
                    if isinstance(unit, (int, float)):
                        unit = f"{unit:.2f} €"
                    if isinstance(total, (int, float)):
                        total = f"{total:.2f} €"
                    cr_table_data.append([cat.capitalize(), item, qty, unit, formula, total])
                cr_table_data.append([
                    Paragraph('<b>Coût de revient total HT</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('cout_revient_ht', 0.0):.2f} €"
                ])
                if 'marge_ht' in prix_details:
                    cr_table_data.append([
                        Paragraph('<b>Marge totale HT</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('marge_ht', 0.0):.2f} €"
                    ])
                cr_col_widths = [3.0 * cm, 5.0 * cm, 1.5 * cm, 3.0 * cm, 4.5 * cm, 3.0 * cm]
                cr_detail_table = Table(cr_table_data, colWidths=cr_col_widths, repeatRows=1)
                cr_detail_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F5')),
                    ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                    ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                    ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                    ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                elements.append(cr_detail_table)
        else:
            # Aucune liste complète mais des totaux disponibles : créer une page simple
            if any(k in prix_details for k in ['foam_total', 'fabric_total', 'support_total', 'cushion_total', 'traversin_total', 'surmatelas_total']):
                elements.append(PageBreak())
                elements.append(Paragraph("Détail des calculs du prix", title_style))
                elements.append(Spacer(1, 0.3 * cm))
                detail_rows = []
                if 'foam_total' in prix_details:
                    detail_rows.append(["Mousse", f"{prix_details['foam_total']:.2f} €"])
                if 'fabric_total' in prix_details:
                    detail_rows.append(["Tissu", f"{prix_details['fabric_total']:.2f} €"])
                if 'support_total' in prix_details:
                    detail_rows.append(["Supports (banquettes, angles, dossiers)", f"{prix_details['support_total']:.2f} €"])
                if 'cushion_total' in prix_details:
                    detail_rows.append(["Coussins (assise & déco)", f"{prix_details['cushion_total']:.2f} €"])
                if 'traversin_total' in prix_details:
                    detail_rows.append(["Traversins", f"{prix_details['traversin_total']:.2f} €"])
                if 'surmatelas_total' in prix_details:
                    detail_rows.append(["Surmatelas", f"{prix_details['surmatelas_total']:.2f} €"])
                detail_rows.append(["Total HT", f"{prix_details.get('prix_ht', 0.0):.2f} €"])
                detail_rows.append(["TVA (20 %)", f"{prix_details.get('tva', 0.0):.2f} €"])
                detail_rows.append(["Total TTC", f"{prix_details.get('total_ttc', 0.0):.2f} €"])
                col_widths_simple = [10 * cm, 8 * cm]
                detail_table_simple = Table(detail_rows, colWidths=col_widths_simple)
                detail_table_simple.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F5')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                    ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                ]))
                elements.append(detail_table_simple)
                # Ajouter ensuite la page de coût de revient si demandée
                if show_detail_cr and cr_details:
                    elements.append(PageBreak())
                    elements.append(Paragraph("Détail des calculs du coût de revient", title_style))
                    elements.append(Spacer(1, 0.3 * cm))
                    cr_table_data = []
                    cr_table_data.append([
                        Paragraph('<b>Catégorie</b>', styles['Normal']),
                        Paragraph('<b>Article</b>', styles['Normal']),
                        Paragraph('<b>Qté</b>', styles['Normal']),
                        Paragraph('<b>Coût unitaire</b>', styles['Normal']),
                        Paragraph('<b>Formule</b>', styles['Normal']),
                        Paragraph('<b>Total</b>', styles['Normal'])
                    ])
                    for entry in cr_details:
                        cat = entry.get('category', '')
                        item = entry.get('item', '')
                        qty = entry.get('quantity', '')
                        unit = entry.get('unit_price', '')
                        formula = entry.get('formula', '')
                        total = entry.get('total_price', '')
                        if isinstance(unit, (int, float)):
                            unit = f"{unit:.2f} €"
                        if isinstance(total, (int, float)):
                            total = f"{total:.2f} €"
                        cr_table_data.append([cat.capitalize(), item, qty, unit, formula, total])
                    cr_table_data.append([
                        Paragraph('<b>Coût de revient total HT</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('cout_revient_ht', 0.0):.2f} €"
                    ])
                    if 'marge_ht' in prix_details:
                        cr_table_data.append([
                            Paragraph('<b>Marge totale HT</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('marge_ht', 0.0):.2f} €"
                        ])
                    cr_col_widths_simple = [3.0 * cm, 5.0 * cm, 1.5 * cm, 3.0 * cm, 4.5 * cm, 3.0 * cm]
                    cr_detail_table_simple = Table(cr_table_data, colWidths=cr_col_widths_simple, repeatRows=1)
                    cr_detail_table_simple.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F5')),
                        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                        ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                        ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ]))
                    elements.append(cr_detail_table_simple)
            else:
                # Pas de détails ni de totaux à afficher, mais on peut quand même afficher le coût de revient si demandé
                if show_detail_cr and cr_details:
                    elements.append(PageBreak())
                    elements.append(Paragraph("Détail des calculs du coût de revient", title_style))
                    elements.append(Spacer(1, 0.3 * cm))
                    cr_table_data = []
                    cr_table_data.append([
                        Paragraph('<b>Catégorie</b>', styles['Normal']),
                        Paragraph('<b>Article</b>', styles['Normal']),
                        Paragraph('<b>Qté</b>', styles['Normal']),
                        Paragraph('<b>Coût unitaire</b>', styles['Normal']),
                        Paragraph('<b>Formule</b>', styles['Normal']),
                        Paragraph('<b>Total</b>', styles['Normal'])
                    ])
                    for entry in cr_details:
                        cat = entry.get('category', '')
                        item = entry.get('item', '')
                        qty = entry.get('quantity', '')
                        unit = entry.get('unit_price', '')
                        formula = entry.get('formula', '')
                        total = entry.get('total_price', '')
                        if isinstance(unit, (int, float)):
                            unit = f"{unit:.2f} €"
                        if isinstance(total, (int, float)):
                            total = f"{total:.2f} €"
                        cr_table_data.append([cat.capitalize(), item, qty, unit, formula, total])
                    cr_table_data.append([
                        Paragraph('<b>Coût de revient total HT</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('cout_revient_ht', 0.0):.2f} €"
                    ])
                    if 'marge_ht' in prix_details:
                        cr_table_data.append([
                            Paragraph('<b>Marge totale HT</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('marge_ht', 0.0):.2f} €"
                        ])
                    cr_col_widths_only = [3.0 * cm, 5.0 * cm, 1.5 * cm, 3.0 * cm, 4.5 * cm, 3.0 * cm]
                    cr_detail_table_only = Table(cr_table_data, colWidths=cr_col_widths_only, repeatRows=1)
                    cr_detail_table_only.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F5')),
                        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                        ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                        ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ]))
                    elements.append(cr_detail_table_only)
    else:
        # Ne pas afficher le détail du prix ; seulement, si demandé, afficher le coût de revient
        if show_detail_cr and cr_details:
            elements.append(PageBreak())
            elements.append(Paragraph("Détail des calculs du coût de revient", title_style))
            elements.append(Spacer(1, 0.3 * cm))
            cr_table_data = []
            cr_table_data.append([
                Paragraph('<b>Catégorie</b>', styles['Normal']),
                Paragraph('<b>Article</b>', styles['Normal']),
                Paragraph('<b>Qté</b>', styles['Normal']),
                Paragraph('<b>Coût unitaire</b>', styles['Normal']),
                Paragraph('<b>Formule</b>', styles['Normal']),
                Paragraph('<b>Total</b>', styles['Normal'])
            ])
            for entry in cr_details:
                cat = entry.get('category', '')
                item = entry.get('item', '')
                qty = entry.get('quantity', '')
                unit = entry.get('unit_price', '')
                formula = entry.get('formula', '')
                total = entry.get('total_price', '')
                if isinstance(unit, (int, float)):
                    unit = f"{unit:.2f} €"
                if isinstance(total, (int, float)):
                    total = f"{total:.2f} €"
                cr_table_data.append([cat.capitalize(), item, qty, unit, formula, total])
            cr_table_data.append([
                Paragraph('<b>Coût de revient total HT</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('cout_revient_ht', 0.0):.2f} €"
            ])
            if 'marge_ht' in prix_details:
                cr_table_data.append([
                    Paragraph('<b>Marge totale HT</b>', styles['Normal']), '', '', '', '', f"{prix_details.get('marge_ht', 0.0):.2f} €"
                ])
            cr_col_widths_only2 = [3.0 * cm, 5.0 * cm, 1.5 * cm, 3.0 * cm, 4.5 * cm, 3.0 * cm]
            cr_detail_table_only2 = Table(cr_table_data, colWidths=cr_col_widths_only2, repeatRows=1)
            cr_detail_table_only2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F5')),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            elements.append(cr_detail_table_only2)

    # Construction du document PDF : toutes les pages assemblées, avec pied de page sur chacune
    doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)
    buffer.seek(0)
    return buffer
