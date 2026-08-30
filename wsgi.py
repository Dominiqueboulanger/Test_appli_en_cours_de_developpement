import os
from snapeval import ApplicationTCF
from nicegui import app, ui

# On instancie explicitement l'application pour qu'Uvicorn la charge sans ambiguïté
@ui.page("/")
def main_page():
    ApplicationTCF()
