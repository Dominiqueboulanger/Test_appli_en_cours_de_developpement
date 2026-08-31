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

# Exemple de données de critères (adaptables selon votre structure exacte)
CRITERES_TCF = [
    {"id": 1, "tache": "Tâche 1", "critere": "Interaction", "description": "Capacité à entrer en contact, échanger, réagir."},
    {"id": 2, "tache": "Tâche 1", "critere": "Continuum / Discours", "description": "Capacité à se présenter et parler de soi de manière continue."},
    {"id": 3, "tache": "Tâche 2", "critere": "Enquête / Information", "description": "Capacité à poser des questions, obtenir des informations."},
    {"id": 4, "tache": "Tâche 3", "critere": "Argumentation", "description": "Capacité à défendre un point de vue, argumenter et négocier."}
]

@app.route("/")
def index():
    return render_template("index.html")

# Route pour que le front-end récupère les critères au chargement
@app.route("/api/criteres", methods=["GET"])
def get_criteres():
    return jsonify(CRITERES_TCF)

# Route pour générer le PDF directement à partir des données transmises
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
        for ev in evaluations:
            table_data.append([
                str(ev.get("critere", "")),
                str(ev.get("niveau", "")),
                str(ev.get("note", "")),
                str(ev.get("commentaire", ""))
            ])

        table = Table(table_data, colWidths=[120, 50, 40, 305])
        table.setStyle(TableStyle([
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
        ]))

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
