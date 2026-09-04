from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
import io

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

# Dégradé de bleu du A1 (clair) au C2 (marine)
COULEURS_NIVEAUX = {
    "A1": "#bae6fd",
    "A2": "#7dd3fc",
    "B1": "#38bdf8",
    "B2": "#0284c7",
    "C1": "#0369a1",
    "C2": "#0c4a6e"
}

CRITERES_TCF = [
    {"id": 1, "tache": "Tâche 1", "critere": "Interaction", "description": "Capacité à entrer en contact, échanger, réagir."},
    {"id": 2, "tache": "Tâche 1", "critere": "Continuum / Discours", "description": "Capacité à se présenter et parler de soi de manière continue."},
    {"id": 3, "tache": "Tâche 2", "critere": "Enquête / Information", "description": "Capacité à poser des questions, obtenir des informations."},
    {"id": 4, "tache": "Tâche 3", "critere": "Argumentation", "description": "Capacité à défendre un point de vue, argumenter et négocier."}
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/criteres", methods=["GET"])
def get_criteres():
    # On renvoie aussi les couleurs pour que le front-end puisse les afficher sous forme de puces
    return jsonify({
        "criteres": CRITERES_TCF,
        "couleurs": COULEURS_NIVEAUX
    })

@app.route("/api/generer-pdf", methods=["POST"])
def generer_pdf():
    try:
        data = request.json
        candidat_nom = data.get("candidat_nom", "Candidat_Inconnu").strip()
        evaluations = data.get("evaluations", [])

        if not evaluations:
            return jsonify({"error": "Aucune évaluation transmise"}), 400

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=40, 
            leftMargin=40, 
            topMargin=40, 
            bottomMargin=40
        )
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=15,
            alignment=1
        )
        
        elements.append(Paragraph(f"Bilan d'Évaluation TCF Oral — {candidat_nom}", title_style))
        elements.append(Spacer(1, 10))

        table_data = [["Critère", "Niveau", "Note", "Commentaire"]]
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        for index, ev in enumerate(evaluations, start=1):
            niveau = str(ev.get("niveau", "")).upper()
            table_data.append([
                str(ev.get("critere", "")),
                niveau,
                str(ev.get("note", "")),
                str(ev.get("commentaire", ""))
            ])
            # Coloration dynamique de la cellule du niveau dans le PDF si le niveau existe
            if niveau in COULEURS_NIVEAUX:
                style_commands.append(('BACKGROUND', (1, index), (1, index), colors.HexColor(COULEURS_NIVEAUX[niveau])))
                # Texte en blanc pour les teintes sombres (C1, C2), sombre pour le reste
                text_col = colors.whitesmoke if niveau in ["C1", "C2"] else colors.HexColor('#1a202c')
                style_commands.append(('TEXTCOLOR', (1, index), (1, index), text_col))
                style_commands.append(('ALIGN', (1, index), (1, index), 'CENTER'))

        table = Table(table_data, colWidths=[120, 50, 40, 305])
        table.setStyle(TableStyle(style_commands))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        nom_fichier_clean = "".join(c for c in candidat_nom if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"bilan_tcf_{nom_fichier_clean}.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
