import tkinter as tk
from datetime import datetime, timedelta

def load(frame_left, frame_right, conn):
    # Vider frames
    for w in frame_left.winfo_children(): w.destroy()
    for w in frame_right.winfo_children(): w.destroy()

    cursor = conn.cursor()
    cursor.execute(
        "SELECT rowid, nos, nochu, nol, ref_fab, service, date_acq, fin_garantie, commentaires, fournisseur, date_fab, date_ref, pj FROM parc"
    )
    rows = cursor.fetchall()

    # Partie gauche : liste + Rafraîchir
    container_left = tk.Frame(frame_left)
    container_left.pack(fill='both', expand=True)

    scrollbar = tk.Scrollbar(container_left)
    scrollbar.pack(side='right', fill='y')
    listbox = tk.Listbox(container_left, yscrollcommand=scrollbar.set)
    listbox.pack(side='left', fill='both', expand=True)
    scrollbar.config(command=listbox.yview)

    ctrl_left = tk.Frame(container_left)
    ctrl_left.pack(fill='x', pady=5)
    tk.Button(ctrl_left, text="Rafraîchir", command=lambda: load(frame_left, frame_right, conn)).pack(side='right', padx=2)

    data_by_index = {}
    for i, row in enumerate(rows):
        # Affichage résumé : ref_fab et service
        summary = f"{row[4]} - {row[5]}"
        listbox.insert(tk.END, summary)
        data_by_index[i] = row

    # Partie droite : détails + CRUD
    details_frame = tk.Frame(frame_right)
    details_frame.pack(fill='both', expand=True)

    def refresh(): load(frame_left, frame_right, conn)

    def display_details(row):
        for w in details_frame.winfo_children(): w.destroy()
        champs = ["rowid","nos","nochu","nol","ref_fab","service","date_acq","fin_garantie","commentaires","fournisseur","date_fab","date_ref","pj"]
        for i, (champ, val) in enumerate(zip(champs, row)):
            tk.Label(details_frame, text=f"{champ}:", font=("Arial",10,"bold")).grid(row=i, column=0, sticky='w', padx=5, pady=2)
            tk.Label(details_frame, text=str(val)).grid(row=i, column=1, sticky='w', padx=5, pady=2)
        # Boutons CRUD à droite
        btn_frame = tk.Frame(details_frame)
        btn_frame.grid(row=len(champs), column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Ajouter", command=lambda: show_form(None)).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Modifier", command=lambda: show_form(row)).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Supprimer", command=lambda: delete_selected()).pack(side='left', padx=5)

    def show_details(event):
        sel = listbox.curselection()
        if not sel: return
        row = data_by_index[sel[0]]
        display_details(row)

    def show_form(data):
        # Formulaire d'ajout/modification
        for w in details_frame.winfo_children(): w.destroy()
        champs = ["nos","nochu","nol","ref_fab","service","date_acq","fin_garantie","commentaires","fournisseur","date_fab","date_ref","pj"]
        entries = {}
        for i, champ in enumerate(champs):
            tk.Label(details_frame, text=f"{champ}:").grid(row=i, column=0, sticky='w', padx=5, pady=2)
            entry = tk.Entry(details_frame)
            entry.grid(row=i, column=1, padx=5, pady=2)
            if data:
                entry.insert(0, data[i+1])
            entries[champ] = entry

        def valider():
            vals = [entries[c].get() for c in champs]
            cur = conn.cursor()
            if data is None:
                cur.execute(
                    "INSERT INTO parc (nos,nochu,nol,ref_fab,service,date_acq,fin_garantie,commentaires,fournisseur,date_fab,date_ref,pj) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", vals)
            else:
                key = data[0]
                cur.execute(
                    "UPDATE parc SET nos=?,nochu=?,nol=?,ref_fab=?,service=?,date_acq=?,fin_garantie=?,commentaires=?,fournisseur=?,date_fab=?,date_ref=?,pj=? WHERE rowid=?", vals + [key])
            conn.commit(); refresh()

        tk.Button(details_frame, text="Valider", command=valider).grid(row=len(champs), column=0, columnspan=2, pady=10)

    def delete_selected():
        sel = listbox.curselection()
        if not sel: return
        key = data_by_index[sel[0]][0]
        cur = conn.cursor()
        cur.execute("DELETE FROM parc WHERE rowid=?", (key,))
        conn.commit(); refresh()

    listbox.bind('<<ListboxSelect>>', show_details)
