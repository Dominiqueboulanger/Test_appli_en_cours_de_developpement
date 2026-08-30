// Charger les critères depuis le backend
async function chargerCriteres() {
    try {
        const response = await fetch("/api/criteres");
        if (!response.ok) throw new Error("Erreur lors du chargement des critères");
        const criteres = await response.json();

        const container = document.getElementById("cartes-evaluation");
        container.innerHTML = "";

        criteres.forEach(critere => {
            const carte = document.createElement("div");
            carte.className = "carte";
            carte.innerHTML = `
                <h3>${critere.titre}</h3>
                <div class="paliers">
                    ${critere.paliers.map(palier => `
                        <div class="palier" data-niveau="${palier.niveau}" data-critere="${critere.titre}" onclick="selectPalier(this)">
                            <strong>${palier.niveau}:</strong> ${palier.texte}
                        </div>
                    `).join("")}
                </div>
            `;
            container.appendChild(carte);
        });
    } catch (error) {
        console.error("Erreur:", error);
        alert("Impossible de charger les critères. Vérifiez la connexion au serveur.");
    }
}

// Fonction pour calculer le niveau global en fonction des paliers sélectionnés
function calculerNiveauGlobal() {
    const paliersSelectionnes = document.querySelectorAll(".palier.selected");
    if (paliersSelectionnes.length === 0) {
        return "A1"; // Valeur par défaut si aucun palier n'est sélectionné
    }

    // Compte le nombre de paliers par niveau
    const compteurNiveaux = {
        "A1": 0,
        "A2": 0,
        "B1": 0,
        "B2": 0,
        "C1": 0,
        "C2": 0
    };

    paliersSelectionnes.forEach(palier => {
        const niveau = palier.dataset.niveau;
        if (compteurNiveaux[niveau] !== undefined) {
            compteurNiveaux[niveau]++;
        }
    });

    // Détermine le niveau global en fonction du niveau le plus fréquent
    let niveauGlobal = "A1";
    let maxCount = 0;

    for (const [niveau, count] of Object.entries(compteurNiveaux)) {
        if (count > maxCount) {
            maxCount = count;
            niveauGlobal = niveau;
        }
    }

    return niveauGlobal;
}

// Changer d'onglet
function changerOnglet(onglet) {
    const contents = document.querySelectorAll(".tab-content");
    contents.forEach(content => content.style.display = "none");
    document.getElementById(onglet).style.display = "block";

    const buttons = document.querySelectorAll(".tab-button");
    buttons.forEach(button => button.classList.remove("active"));
    event.target.classList.add("active");
}

// Sélectionner un palier
function selectPalier(element) {
    // Désélectionner tous les paliers de la même carte
    const paliers = element.parentElement.querySelectorAll(".palier");
    paliers.forEach(p => p.classList.remove("selected"));

    // Sélectionner le palier cliqué
    element.classList.add("selected");

    // Recalculer le niveau global
    const niveauGlobal = calculerNiveauGlobal();
    document.getElementById("niveau-global").value = niveauGlobal;
}

// Enregistrer une évaluation
async function enregistrerEvaluation() {
    const candidatId = document.getElementById("candidat-id").value;
    const commentaire = document.getElementById("commentaire").value;

    // Récupérer les paliers sélectionnés
    const paliersSelectionnes = document.querySelectorAll(".palier.selected");
    if (paliersSelectionnes.length === 0) {
        alert("Veuillez sélectionner au moins un palier.");
        return;
    }

    // Calculer le niveau global automatiquement
    const niveauGlobal = calculerNiveauGlobal();
    document.getElementById("niveau-global").value = niveauGlobal;

    // Préparer les données pour chaque palier sélectionné
    const evaluations = Array.from(paliersSelectionnes).map(palier => ({
        candidat_id: parseInt(candidatId),
        examinateur: "Dominique",
        type_epreuve: "TCF oral",
        critere: palier.dataset.critere,
        niveau: palier.dataset.niveau,
        note: 0,
        commentaire: commentaire
    }));

    try {
        // Envoyer chaque évaluation au backend
        for (const evalData of evaluations) {
            const response = await fetch("/api/evaluer", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(evalData)
            });
            if (!response.ok) throw new Error("Erreur lors de l'enregistrement");
        }
        alert("Évaluation(s) enregistrée(s) avec succès ! Niveau global : " + niveauGlobal);
    } catch (error) {
        console.error("Erreur:", error);
        alert("Erreur lors de l'enregistrement de l'évaluation.");
    }
}

// Générer un PDF
function genererPDF() {
    const candidatId = document.getElementById("candidat-id").value;
    window.location.href = `/api/generer-pdf/${candidatId}`;
}

// Initialiser l'app
document.addEventListener("DOMContentLoaded", () => {
    chargerCriteres();
});