import os
import sys
import traceback

try:
    import uvicorn
    from wsgi import app
except Exception as e:
    with open("crash_error.log", "w") as f:
        f.write("Erreur au chargement :\n")
        traceback.print_exc(file=f)
    raise e

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        with open("crash_error.log", "a") as f:
            f.write("Erreur au lancement d'Uvicorn :\n")
            traceback.print_exc(file=f)
        raise e
