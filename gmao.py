#gmao.py
table_corrigee = None

import tkinter as tk
from tkinter import messagebox
import sqlite3

# Import des modules pages
import parc
import interventions
import catalogue
import stock
import commandes
import genes
import documents
import cuves  
import emissaire
import effluents


# Ouvrir la connexion SQLite globale
conn = sqlite3.connect('gmao.db')

def quitter():
    if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter ?"):
        conn.close()
        root.destroy()

def set_active_button(active_name):
    for name, btn in buttons.items():
        if name == active_name:
            btn.config(state="disabled", bg="lightgray")
        else:
            btn.config(state="normal", bg=default_btn_bg)

modules = {
    "Parc": parc,
    "Interventions": interventions,
    "Catalogue": catalogue,
    "Stock": stock,
    "Commandes": commandes,
    "Générateurs": genes,
    "Documents": documents,
    "Cuves": cuves, 
    "Emissaire": emissaire,
    "Effluents": effluents, 
}

def load_page(page_name):
    set_active_button(page_name)

    for widget in frame_left.winfo_children():
        widget.destroy()
    for widget in frame_right.winfo_children():
        widget.destroy()

    modules[page_name].load(frame_left, frame_right, conn)

# Création fenêtre principale
root = tk.Tk()
root.title("GMAO Modulaire")

# Barre de menu horizontale en haut
top_frame = tk.Frame(root)
top_frame.pack(side="top", fill="x")

buttons = {}
for page in ["Parc", "Interventions", "Catalogue", "Stock", "Commandes", "Générateurs", "Documents", "Cuves", "Emissaire", "Effluents"]:  
    btn = tk.Button(top_frame, text=page, width=15,
                    command=lambda p=page: load_page(p))
    btn.pack(side="left", padx=2, pady=2)
    buttons[page] = btn

# Bouton Quitter
btn_quit = tk.Button(top_frame, text="Quitter", width=10, command=quitter)
btn_quit.pack(side="right", padx=10, pady=2)

default_btn_bg = buttons["Parc"].cget("background")

# Cadres gauche/droite
bottom_frame = tk.Frame(root)
bottom_frame.pack(side="top", fill="both", expand=True)

bottom_frame.rowconfigure(0, weight=1)
bottom_frame.columnconfigure(0, weight=1)
bottom_frame.columnconfigure(1, weight=1)

frame_left = tk.Frame(bottom_frame, bg="white")
frame_left.grid(row=0, column=0, sticky="nsew")

frame_right = tk.Frame(bottom_frame, bg="white")
frame_right.grid(row=0, column=1, sticky="nsew")

# Page par défaut
load_page("Parc")

root.mainloop()

