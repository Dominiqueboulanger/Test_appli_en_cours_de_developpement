import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # On lance Uvicorn en ciblant le module wsgi:app
    uvicorn.run("wsgi:app", host="0.0.0.0", port=port, log_level="info")
