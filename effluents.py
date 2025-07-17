#effluents.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sqlite3
from import_effluents import create_effluents_table, import_effluents_from_csv

PAGE_SIZE = 50  # nombre de lignes affichées dans le tableau

def load(frame_left, frame_right, conn):
    for w in frame_left.winfo_children():
        w.destroy()
    for w in frame_right.winfo_children():
        w.destroy()

    # Création de la table si elle n'existe pas
    create_effluents_table()

    # Variables de pagination
    current_page = tk.IntVar(value=0)

    # Boutons gauche
    btn_import = tk.Button(frame_left, text="Importer les effluents (.csv)", bg="lightblue", width=20)
    btn_delete_dupes = tk.Button(frame_left, text="Effacer les doublons", bg="lightcoral", width=20)

    btn_import.pack(pady=10)
    btn_delete_dupes.pack(pady=10)

    # Tableau Treeview à droite
    cols = ("protocol_id", "rack", "pos", "measurement_datetime", "tc99m_cpm", "i123_cpm", "i131_cpm", "f18_cpm")
    tree = ttk.Treeview(frame_right, columns=cols, show="headings", height=25)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=100, anchor='center')
    tree.pack(fill="both", expand=True)

    # Label pagination
    lbl_page = tk.Label(frame_right, text="")
    lbl_page.pack(pady=5)

    def load_data(page=0):
        tree.delete(*tree.get_children())
        offset = page * PAGE_SIZE
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM effluents")
        total_rows = cur.fetchone()[0]

        cur.execute(f"""
            SELECT protocol_id, rack, pos, measurement_datetime, tc99m_cpm, i123_cpm, i131_cpm, f18_cpm
            FROM effluents
            ORDER BY measurement_datetime DESC
            LIMIT {PAGE_SIZE} OFFSET {offset}
        """)
        rows = cur.fetchall()

        for row in rows:
            tree.insert("", "end", values=row)

        total_pages = (total_rows - 1) // PAGE_SIZE + 1 if total_rows else 1
        lbl_page.config(text=f"Page {page+1} / {total_pages}")
        current_page.set(page)

    def import_files():
        dossier = filedialog.askdirectory(title="Choisir le dossier CSV")
        if not dossier:
            return
        import_effluents_from_csv(db_path='gmao.db', csv_dir=dossier, verbose=True)
        messagebox.showinfo("Import terminé", f"Importation terminée depuis : {dossier}")
        load_data(0)

    def delete_duplicates():
        try:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM effluents
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM effluents
                    GROUP BY protocol_id, rack, pos, measurement_datetime
                )
            """)
            conn.commit()
            messagebox.showinfo("Doublons", "Les doublons ont été supprimés.")
            load_data(current_page.get())
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def prev_page():
        p = current_page.get()
        if p > 0:
            load_data(p - 1)

    def next_page():
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM effluents")
        total_rows = cur.fetchone()[0]
        total_pages = (total_rows - 1) // PAGE_SIZE
        p = current_page.get()
        if p < total_pages:
            load_data(p + 1)

    btn_import.config(command=import_files)
    btn_delete_dupes.config(command=delete_duplicates)

    # Boutons pagination
    pag_frame = tk.Frame(frame_right)
    pag_frame.pack(pady=5)
    btn_prev = tk.Button(pag_frame, text="◀ Page précédente", command=prev_page)
    btn_next = tk.Button(pag_frame, text="Page suivante ▶", command=next_page)
    btn_prev.pack(side="left", padx=5)
    btn_next.pack(side="left", padx=5)

    # Chargement initial
    load_data(0)
