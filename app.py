from flask import Flask, render_template, jsonify, request, send_file
import sqlite3
import os
import io

# Gestion sécurisée de WeasyPrint en production cloud si les libs C manquent
try:
    from weasyprint import HTML
    WEASYPRINT_DISPONIBLE = True
except (ImportError, OSError):
    WEASYPRINT_DISPONIBLE = False

app = Flask(__name__)

# Chemin vers la base de données
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data", "snapeval.db")

# Route pour la page d'accueil
@app.route("/")
def index():
    return render_template("index.html")

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

# Route pour générer un PDF
@app.route("/api/generer-pdf/<int:candidat_id>")
def generer_pdf(candidat_id):
    if not WEASYPRINT_DISPONIBLE:
        return "Génération PDF non disponible (dépendances système WeasyPrint absentes sur le serveur)", 503

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT candidat_id, examinateur, type_epreuve, critere, niveau, note, commentaire
        FROM evaluations_candidats
        WHERE candidat_id = ?
    """, (candidat_id,))
    evaluations = cursor.fetchall()
    conn.close()

    # Générer le HTML pour le PDF
    html_content = f"""
    <h1>Bilan d'évaluation TCF pour le candidat {candidat_id}</h1>
    <table border="1">
        <tr><th>Critère</th><th>Niveau</th><th>Note</th><th>Commentaire</th></tr>
        {"".join(f"<tr><td>{eval[3]}</td><td>{eval[4]}</td><td>{eval[5]}</td><td>{eval[6]}</td></tr>" for eval in evaluations)}
    </table>
    """
    pdf_bytes = HTML(string=html_content).write_pdf()
    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=f"bilan_tcf_{candidat_id}.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
