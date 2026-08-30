import os
import sys
import traceback
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Démarrage du serveur sur le port {port}...", file=sys.stderr)
    try:
        # Passage en chaîne de caractères "wsgi:app" au lieu de l'objet
        uvicorn.run("wsgi:app", host="0.0.0.0", port=port, log_level="debug")
    except Exception as e:
        print("=== ERREUR CRITIQUE AU LANCEMENT ===", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
