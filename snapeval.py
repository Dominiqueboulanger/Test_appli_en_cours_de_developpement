from collections import Counter
import os
import sqlite3
from nicegui import ui

DB_NAME = "/Users/dominiqueboulanger/Desktop/appli_TCF_24_aout/snapeval.db"
EXAMEN_NOM = "TCF oral"


class ApplicationTCF:

  def __init__(self):
    self.selections = {}
    self.init_ui()

  def charger_donnees_db(self):
    """Charge les critères, niveaux et marqueurs depuis la table unique aspects_qualitatifs_langue."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # On récupère les critères, niveaux et marqueurs
    cursor.execute("""
            SELECT id, critere, niveau, descripteur, marqueur 
            FROM aspects_qualitatifs_langue 
            ORDER BY id
        """)
    rows = cursor.fetchall()
    conn.close()
    return rows

  @property
  def criteres_actifs(self):
    """Reconstruit dynamiquement la structure des critères à partir de la base de données."""
    rows = self.charger_donnees_db()
    criteres_dict = {}

    # Ordre standard des niveaux pour le tri
    ordre_niveaux = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

    for row_id, critere, niveau, descripteur, marqueur in rows:
      # Utilisation du marqueur comme texte principal (ou descripteur si présent)
      texte = marqueur if marqueur else (descripteur if descripteur else "")
      if critere not in criteres_dict:
        criteres_dict[critere] = []
      criteres_dict[critere].append((niveau, texte))

    # Formater sous forme de liste de dictionnaires exploitable par l'UI
    resultat = []
    for titre, paliers in criteres_dict.items():
      # Trier les paliers selon l'ordre A1 -> C2
      paliers_tries = sorted(
          paliers, key=lambda x: ordre_niveaux.get(x[0], 99)
      )
      resultat.append({"titre": titre, "paliers": paliers_tries})

    return resultat

  def init_ui(self):
    ui.add_head_html(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
    )

    with ui.tabs().classes("w-full bg-slate-200") as tabs:
      tab_eval = ui.tab("Évaluation TCF Oral", icon="assessment")
      tab_admin = ui.tab("Admin Marqueurs", icon="settings")

    with ui.tab_panels(tabs, value=tab_eval).classes("w-full"):
      # --- ONGLET 1 : ÉVALUATION ---
      with ui.tab_panel(tab_eval):
        with ui.column().classes("w-full max-w-5xl mx-auto p-4 items-center"):
          with ui.row().classes(
              "w-full justify-between items-center mb-2 px-2"
          ):
            ui.label("Évaluation TCF Oral — Grille et Bilan").classes(
                "text-xl font-extrabold text-slate-800"
            )

          self.container_cartes = ui.row().classes(
              "w-full overflow-x-auto flex-nowrap gap-4 p-2 items-stretch"
              " no-scrollbar"
          )
          self.actualiser_cartes_evaluation()

          with ui.card().classes(
              "w-full max-w-5xl p-4 bg-white shadow-md border rounded-xl mt-4"
              " gap-3"
          ):
            ui.label("Synthèse & Évaluation Finale").classes(
                "text-base font-bold text-slate-800 border-b pb-1"
            )
            with ui.row().classes("w-full justify-between items-center gap-2"):
              self.lbl_tendance = ui.label("En attente d'évaluations...").classes(
                  "text-xs font-semibold text-blue-700"
              )
              self.select_niveau_global = ui.select(
                  options=["A1", "A2", "B1", "B2", "C1", "C2"],
                  value="B1",
                  label="Niveau",
              ).props("dense outlined").classes("w-24")

            self.textarea_synthese = (
                ui.textarea(placeholder="Appréciation globale...")
                .props("outlined dense")
                .classes("w-full text-xs bg-slate-50")
            )
            ui.button(
                "Valider et archiver", on_click=self.valider_evaluation
            ).classes(
                "bg-blue-600 text-white font-bold px-4 py-2 rounded text-xs"
                " self-end"
            )

      # --- ONGLET 2 : ADMIN (aspects_qualitatifs_langue) ---
      with ui.tab_panel(tab_admin):
        with ui.column().classes("w-full max-w-4xl mx-auto p-4 gap-4"):
          ui.label(
              "Gestion des Marqueurs (Table : aspects_qualitatifs_langue)"
          ).classes("text-xl font-extrabold text-slate-800")

          with ui.card().classes("w-full p-4 bg-white shadow-sm border gap-3"):
            ui.label("Ajouter ou modifier un marqueur").classes(
                "text-sm font-bold text-slate-700"
            )
            with ui.row().classes("w-full gap-2"):
              self.input_critere = (
                  ui.input(label="Critère (ex: lexique, débit...)")
                  .props("outlined dense")
                  .classes("flex-grow")
              )
              self.select_niv = (
                  ui.select(
                      label="Niveau",
                      options=["A1", "A2", "B1", "B2", "C1", "C2"],
                      value="A1",
                  )
                  .props("outlined dense")
                  .classes("w-28")
              )

            self.input_marqueur = (
                ui.textarea(label="Marqueur / Description")
                .props("outlined dense")
                .classes("w-full")
            )

            ui.button(
                "Enregistrer dans la base", on_click=self.sauvegarder_marqueur
            ).classes(
                "bg-blue-600 text-white font-bold px-4 py-2 rounded text-xs"
                " self-end"
            )

          with ui.card().classes("w-full p-4 bg-white shadow-sm border gap-3"):
            ui.label("Marqueurs enregistrés").classes(
                "text-sm font-bold text-slate-700"
            )
            self.container_admin_liste = ui.column().classes("w-full gap-2")
            self.actualiser_admin_liste()

  def actualiser_cartes_evaluation(self):
    self.container_cartes.clear()
    criteres = self.criteres_actifs
    with self.container_cartes:
      for idx, critere in enumerate(criteres):
        self.creer_carte_critere(idx, critere)

  def creer_carte_critere(self, idx, critere):
    with ui.card().classes(
        "flex-shrink-0 w-72 p-4 bg-white shadow-sm border rounded-xl flex"
        " flex-col justify-between"
    ):
      with ui.column().classes("w-full gap-2"):
        ui.label(critere["titre"]).classes(
            "text-base font-bold text-slate-700 border-b pb-1 uppercase"
        )
        lbl_choix = ui.label("Non noté").classes(
            "text-[10px] font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded w-fit"
        )
        setattr(self, f"lbl_choix_{idx}", lbl_choix)

        with ui.column().classes("w-full gap-2 mt-1"):
          for niveau, desc in critere["paliers"]:
            self.creer_ligne_epuree(idx, critere["titre"], niveau, desc)

  def creer_ligne_epuree(self, crit_idx, critere_titre, niveau, description):
    classes_couleurs = {
        "A1": "bg-sky-100 text-sky-800",
        "A2": "bg-blue-200 text-blue-900",
        "B1": "bg-blue-400 text-white",
        "B2": "bg-blue-600 text-white",
        "C1": "bg-blue-800 text-white",
        "C2": "bg-slate-900 text-white",
    }
    style_badge = classes_couleurs.get(niveau, "bg-blue-100 text-blue-800")

    with ui.row().classes(
        "w-full p-1.5 bg-slate-50 rounded-lg items-center gap-1.5 border"
    ):

      def clic_selectionner():
        self.selections[critere_titre] = niveau
        lbl = getattr(self, f"lbl_choix_{crit_idx}")
        lbl.text = f"Niveau {niveau}"
        lbl.classes(
            replace=(
                "text-[10px] font-bold text-white bg-blue-600 px-2 py-0.5"
                " rounded w-fit"
            )
        )
        self.mettre_a_jour_tendance()

      ui.button(niveau, on_click=clic_selectionner).props("flat dense").classes(
          f"text-[10px] font-extrabold px-1.5 py-0.5 rounded {style_badge}"
      )

      ui.label(description).classes(
          "text-[11px] text-slate-700 flex-grow bg-white px-1 py-0.5 rounded"
      )

  def mettre_a_jour_tendance(self):
    if not self.selections:
      return
    niveaux_notes = list(self.selections.values())
    compte = Counter(niveaux_notes)
    niveau_frequent, occurrence = compte.most_common(1)[0]
    self.lbl_tendance.text = (
        f"Tendance : {niveau_frequent} ({occurrence} critère(s))"
    )
    self.select_niveau_global.value = niveau_frequent

  def valider_evaluation(self):
    ui.notify(
        f"Évaluation TCF Oral enregistrée ! Niveau :"
        f" {self.select_niveau_global.value}",
        color="positive",
    )
    self.actualiser_cartes_evaluation()

  def sauvegarder_marqueur(self):
    crit = self.input_critere.value.strip()
    niv = self.select_niv.value
    marq = self.input_marqueur.value.strip()

    if not crit or not marq:
      ui.notify(
          "Veuillez remplir le critère et le texte du marqueur.",
          color="negative",
      )
      return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Vérifier si l'enregistrement existe déjà pour ce couple critère/niveau
    cursor.execute(
        """
        SELECT id FROM aspects_qualitatifs_langue 
        WHERE LOWER(critere) = LOWER(?) AND UPPER(niveau) = UPPER(?)
    """,
        (crit, niv),
    )
    existe = cursor.fetchone()

    if existe:
      cursor.execute(
          """
            UPDATE aspects_qualitatifs_langue 
            SET marqueur = ? 
            WHERE LOWER(critere) = LOWER(?) AND UPPER(niveau) = UPPER(?)
        """,
          (marq, crit, niv),
      )
    else:
      cursor.execute(
          """
            INSERT INTO aspects_qualitatifs_langue (critere, niveau, marqueur) 
            VALUES (?, ?, ?)
        """,
          (crit, niv, marq),
      )

    conn.commit()
    conn.close()

    ui.notify("Marqueur enregistré avec succès !", color="positive")
    self.input_critere.value = ""
    self.input_marqueur.value = ""
    self.actualiser_admin_liste()
    self.actualiser_cartes_evaluation()

  def actualiser_admin_liste(self):
    self.container_admin_liste.clear()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, critere, niveau, marqueur FROM aspects_qualitatifs_langue"
        " ORDER BY critere, niveau"
    )
    lignes = cursor.fetchall()
    conn.close()

    if not lignes:
      with self.container_admin_liste:
        ui.label("Aucun marqueur trouvé dans la base.").classes(
            "text-xs text-slate-400 italic"
        )
      return

    for row_id, critere, niveau, marqueur in lignes:
      with self.container_admin_liste:
        with ui.row().classes(
            "w-full items-center justify-between p-2 bg-slate-50 rounded"
            " border gap-2"
        ):
          ui.label(critere).classes(
              "text-xs font-bold text-slate-800 w-32 uppercase"
          )
          ui.label(f"[{niveau}]").classes(
              "text-xs font-extrabold text-slate-700 w-8"
          )

          input_edit = (
              ui.input(value=marqueur if marqueur else "")
              .props("dense borderless")
              .classes(
                  "flex-grow text-xs bg-white px-2 py-1 rounded border"
              )
          )

          def modifier(r_id=row_id, inp=input_edit):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE aspects_qualitatifs_langue SET marqueur = ? WHERE id"
                " = ?",
                (inp.value.strip(), r_id),
            )
            conn.commit()
            conn.close()
            ui.notify("Marqueur mis à jour !", color="positive")
            self.actualiser_cartes_evaluation()

          ui.button(
              icon="save",
              on_click=lambda r_id=row_id, inp=input_edit: modifier(r_id, inp),
          ).props("flat dense").classes("text-blue-600").tooltip(
              "Modifier / Enregistrer"
          )

          def supprimer(r_id=row_id):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM aspects_qualitatifs_langue WHERE id = ?", (r_id,)
            )
            conn.commit()
            conn.close()
            ui.notify("Marqueur supprimé.", color="warning")
            self.actualiser_admin_liste()
            self.actualiser_cartes_evaluation()

          ui.button(
              icon="delete", on_click=lambda r_id=row_id: supprimer(r_id)
          ).props("flat dense").classes("text-red-600").tooltip("Supprimer")


@ui.page("/")
def main_page():
  ApplicationTCF()


if __name__ in {"__main__", "__mp_main__"}:
  ui.run(
      title="TCF Oral",
      host="0.0.0.0",
      port=int(os.environ.get("PORT", 8080)),
      reload=False,
      reconnect_timeout=30,
      show=False,
  )
