from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import sqlite3

app = Flask(__name__)
CORS(app)

def get_db_connection():
    # Remplacez 'database.db' par le nom exact de votre fichier de base de données si nécessaire
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return jsonify({"status": "API en ligne", "app": "Évaluation TCF Oral"})

@app.route("/api/generer-pdf/<int:candidat_id>", methods=["GET"])
def generer_pdf(candidat_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Récupérer les évaluations du candidat
    evaluations = cursor.execute(
        "SELECT * FROM evaluations_candidats WHERE candidat_id = ?", (candidat_id,)
    ).fetchall()
    conn.close()

    if not evaluations:
        return jsonify({"error": "Aucune évaluation trouvée pour ce candidat"}), 404

    # Création du buffer mémoire pour le PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=15,
        alignment=1,  # Centré
    )

    # En-tête du document
    elements.append(Paragraph(f"Bilan d'Évaluation TCF Oral — Candidat #{candidat_id}", title_style))
    elements.append(Spacer(1, 15))

    # Construction des données du tableau
    data = [["Épreuve", "Critère", "Niveau", "Note", "Commentaire"]]
    for ev in evaluations:
        data.append([
            str(ev["type_epreuve"] or ""),
            str(ev["critere"] or ""),
            str(ev["niveau"] or ""),
            str(ev["note"] or ""),
            str(ev["commentaire"] or ""),
        ])

    # Mise en forme du tableau
    table = Table(data, colWidths=[90, 90, 50, 45, 240])
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

    # Génération du PDF
    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"bilan_candidat_{candidat_id}.pdf",
        mimetype="application/pdf",
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
