from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import sqlite3
import os
import io

# Définition du chemin de base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data", "snapeval.db")

app = Flask(__name__)
CORS(app)

# Route pour la page d'accueil
@app.route("/")
def index():
    return render_template("index.html")

# Route pour récupérer les critères et niveaux
@app.route("/api/criteres")
def get_criteres():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, critere, niveau, descripteur, marqueur
            FROM aspects_qualitatifs_langue
            ORDER BY id
        """)
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        return jsonify({"erreur": str(e), "db_path": DB_NAME, "existe": os.path.exists(DB_NAME)}), 500

    criteres_dict = {}
    ordre_niveaux = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

    for row_id, critere, niveau, descripteur, marqueur in rows:
        texte = marqueur if marqueur else (descripteur if descripteur else "")
        if critere not in criteres_dict:
            criteres_dict[critere] = []
        criteres_dict[critere].append({"niveau": niveau, "texte": texte})

    resultat = []
    for titre, paliers in criteres_dict.items():
        paliers_tries = sorted(paliers, key=lambda x: ordre_niveaux.get(x["niveau"], 99))
        resultat.append({"titre": titre, "paliers": paliers_tries})

    return jsonify(resultat)

# Route pour enregistrer une évaluation
@app.route("/api/evaluer", methods=["POST"])
def evaluer():
    data = request.json
    print("Données reçues du front-end :", data)  # Visible dans les logs Clever Cloud
    
    if not data:
        return jsonify({"erreur": "Aucune donnée reçue"}), 400

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Si le front-end envoie une liste d'évaluations d'un coup
        evaluations_list = data if isinstance(data, list) else [data]

        for item in evaluations_list:
            cursor.execute("""
                INSERT INTO evaluations_candidats (candidat_id, examinateur, type_epreuve, critere, niveau, note, commentaire)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("candidat_id", 1),
                item.get("examinateur", "Dominique"),
                item.get("type_epreuve", "TCF oral"),
                item.get("critere", ""),
                item.get("niveau", ""),
                item.get("note", 0),
                item.get("commentaire", "")
            ))
            
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        print("Erreur SQL lors de l'enregistrement :", str(e))
        return jsonify({"erreur": str(e)}), 500


# Route pour générer un PDF avec ReportLab
@app.route("/api/generer-pdf/<int:candidat_id>", methods=["GET"])
def generer_pdf(candidat_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        evaluations = cursor.execute("""
            SELECT candidat_id, examinateur, type_epreuve, critere, niveau, note, commentaire
            FROM evaluations_candidats
            WHERE candidat_id = ?
        """, (candidat_id,)).fetchall()
        conn.close()

        if not evaluations:
            return jsonify({"error": "Aucune évaluation trouvée pour ce candidat"}), 404

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
        
        elements.append(Paragraph(f"Bilan d'Évaluation TCF Oral — Candidat #{candidat_id}", title_style))
        elements.append(Spacer(1, 10))

        data = [["Critère", "Niveau", "Note", "Commentaire"]]
        for ev in evaluations:
            data.append([
                str(ev[3] or ""),
                str(ev[4] or ""),
                str(ev[5] or ""),
                str(ev[6] or "")
            ])

        table = Table(data, colWidths=[120, 50, 40, 305])
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

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"bilan_tcf_{candidat_id}.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
