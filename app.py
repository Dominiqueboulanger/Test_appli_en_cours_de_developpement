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

# Dégradé de bleu du A1 (clair) au C2 (marine) pour la confidentialité sur mobile
COULEURS_NIVEAUX = {
    "A1": "#bae6fd",  # Bleu ciel clair
    "A2": "#7dd3fc",  # Bleu ciel
    "B1": "#38bdf8",  # Bleu moyen clair
    "B2": "#0284c7",  # Bleu
    "C1": "#0369a1",  # Bleu foncé
    "C2": "#0c4a6e"   # Bleu marine très sombre
}

# Route pour la page d'accueil
@app.route("/")
def index():
    return render_template("index.html")

# Route pour récupérer les critères, niveaux et leurs couleurs associées
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
        
        # Attribution de la couleur associée au niveau
        niveau_str = str(niveau).upper()
        couleur = COULEURS_NIVEAUX.get(niveau_str, "#ffffff")
        
        criteres_dict[critere].append({
            "niveau": niveau, 
            "texte": texte,
            "couleur": couleur
        })

    resultat = []
    for titre, paliers in criteres_dict.items():
        paliers_tries = sorted(paliers, key=lambda x: ordre_niveaux.get(str(x["niveau"]).upper(), 99))
        resultat.append({"titre": titre, "paliers": paliers_tries})

    return jsonify(resultat)

# Route pour enregistrer une évaluation
@app.route("/api/evaluer", methods=["POST"])
def evaluer():
    data = request.json
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO evaluations_candidats (candidat_id, examinateur, type_epreuve, critere, niveau, note, commentaire)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("candidat_id", 1),
            data.get("examinateur", "Dominique"),
            data.get("type_epreuve", "TCF oral"),
            data.get("critere", ""),
            data.get("niveau", ""),
            data.get("note", 0),
            data.get("commentaire", "")
        ))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

# Route pour générer un PDF avec ReportLab intégrant les couleurs des niveaux
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
            critere = str(ev[3] or "")
            niveau = str(ev[4] or "").upper()
            note = str(ev[5] or "")
            commentaire = str(ev[6] or "")

            table_data.append([critere, niveau, note, commentaire])

            # Coloration dynamique de la cellule du niveau dans le PDF selon le code couleur
            if niveau in COULEURS_NIVEAUX:
                style_commands.append(('BACKGROUND', (1, index), (1, index), colors.HexColor(COULEURS_NIVEAUX[niveau])))
                # Texte blanc pour les niveaux sombres (C1, C2), sombre pour les autres
                text_col = colors.whitesmoke if niveau in ["C1", "C2"] else colors.HexColor('#1a202c')
                style_commands.append(('TEXTCOLOR', (1, index), (1, index), text_col))
                style_commands.append(('ALIGN', (1, index), (1, index), 'CENTER'))

        table = Table(table_data, colWidths=[120, 50, 40, 305])
        table.setStyle(TableStyle(style_commands))

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
