import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import simpledialog

def load(frame_left, frame_right, conn):
    cursor = conn.cursor()
    rows_map = {}
    data_items = []

    volume = tk.IntVar()
    date_prelevement = tk.StringVar()

    def get_selected_rowids():
        selection = listbox.curselection()
        return [rows_map[listbox.get(i)] for i in selection]

    def mettre_a_jour_tableau(event):
        for widget in frame_table.winfo_children():
            widget.destroy()
        data_items.clear()

        selection = listbox.curselection()
        if not selection:
            return

        colonnes = ["Zéro ?", "Protocol", "Tc", "I-123", "I-131", "F18", "Qui", "Volume", "Prélèvement"]
        for col, titre in enumerate(colonnes):
            label = tk.Label(frame_table, text=titre, borderwidth=1, relief="solid", padx=5, pady=3, bg="#ccc")
            label.grid(row=0, column=col, sticky="nsew")

        for i in selection:
            label_text = listbox.get(i)
            rowid = rows_map[label_text]
            cursor.execute("""
                SELECT protocol_id, tc99m_counts, i123_counts, i131_counts, f18_counts,
                       qui, volume, date_prelevement
                FROM effluents WHERE rowid = ?
            """, (rowid,))
            row = cursor.fetchone()
            if not row:
                continue

            var_zero = tk.BooleanVar()
            chk = tk.Checkbutton(frame_table, variable=var_zero)
            chk.grid(row=i + 1, column=0)

            valeurs = list(row)
            for j, val in enumerate(valeurs):
                label_cell = tk.Label(frame_table, text=str(val), borderwidth=1, relief="solid", padx=5, pady=3)
                label_cell.grid(row=i + 1, column=j + 1, sticky="nsew")

            data_items.append({
                "checkbox": var_zero,
                "widgets": frame_table.grid_slaves(row=i + 1),
                "values": valeurs
            })

    def calculer_bdf():
        zeros = []
        for item in data_items:
            if item["checkbox"].get():
                try:
                    values = [float(item["values"][1]), float(item["values"][2]),
                              float(item["values"][3]), float(item["values"][4])]
                    zeros.append(values)
                except:
                    continue

        if not zeros:
            return

        bdf = [sum(x)/len(x) for x in zip(*zeros)]
        seuils = [2 * x for x in bdf]

        for item in data_items:
            try:
                valeurs = [float(item["values"][1]), float(item["values"][2]),
                           float(item["values"][3]), float(item["values"][4])]
            except:
                continue

            widgets = item["widgets"]
            for col_index in range(4):
                valeur = valeurs[col_index]
                widget = [w for w in widgets if int(w.grid_info()['column']) == col_index + 2][0]
                if valeur > seuils[col_index]:
                    widget.configure(bg="#ffcccc")
                else:
                    widget.configure(bg="white")

        ligne = len(data_items) + 1
        tk.Label(frame_table, text="BDF", borderwidth=1, relief="solid", bg="#eee").grid(row=ligne, column=1)
        for j, val in enumerate(bdf):
            tk.Label(frame_table, text=f"{val:.2f}", borderwidth=1, relief="solid", bg="#eee").grid(row=ligne, column=j + 2)

    def rafraichir_listbox():
        listbox.delete(0, tk.END)
        rows_map.clear()

        cursor.execute("""
            SELECT rowid, run_id, protocol_id, rack, pos, measurement_datetime, qui, volume, date_prelevement
            FROM effluents
            ORDER BY measurement_datetime ASC
        """)
        for row in cursor.fetchall():
            rowid, run_id, protocol_id, rack, pos, dt, qui_val, vol, dp = row
            label = f"Run {run_id} | Protocol {protocol_id} | Rack {rack} | Pos {pos} | {dt}"
            if qui_val:
                label += f" | Qui: {qui_val}"
            if vol:
                label += f" | Vol: {vol}ml"
            if dp:
                label += f" | Prél.: {dp[:16]}"
            listbox.insert("end", label)
            rows_map[label] = rowid

    def fixer_qui():
        selection = listbox.curselection()
        if not selection:
            return
        qui = simpledialog.askstring("Saisie de l'opérateur", "Qui a effectué le prélèvement ?")
        if qui:
            for index in selection:
                rowid = rows_map[listbox.get(index)]
                cursor.execute("UPDATE effluents SET qui = ? WHERE rowid = ?", (qui, rowid))
            conn.commit()
            print(f"🧑‍🔬 Qui : {qui}")
            mettre_a_jour_tableau(None)  # <-- force rafraîchissement tableau

    def saisir_date_prelevement():
        import datetime

        def valider():
            date_str = entry.get().strip()
            try:
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                dt = dt.replace(second=0)
                date_sql = dt.strftime("%Y-%m-%d %H:%M:%S")
                date_prelevement.set(date_sql)

                rowids = get_selected_rowids()
                for rid in rowids:
                    cursor.execute("UPDATE effluents SET date_prelevement = ? WHERE rowid = ?", (date_sql, rid))
                conn.commit()
                print(f"📅 Date de prélèvement définie pour {len(rowids)} échantillons.")
                top.destroy()
                mettre_a_jour_tableau(None)  # <-- force rafraîchissement tableau
            except ValueError:
                lbl_info.config(text="❌ Format invalide (ex: 2025-07-03 09:30)", fg="red")

        top = tk.Toplevel()
        top.title("Date de prélèvement")
        tk.Label(top, text="Entrez la date (AAAA-MM-JJ HH:MM) :").pack(padx=10, pady=5)
        entry = tk.Entry(top, width=25)
        entry.pack(padx=10)
        lbl_info = tk.Label(top, text="", fg="gray")
        lbl_info.pack()
        tk.Button(top, text="Valider", command=valider).pack(pady=5)

    def fixer_volume(val):
        volume.set(val)
        rowids = get_selected_rowids()
        for rid in rowids:
            cursor.execute("UPDATE effluents SET volume = ? WHERE rowid = ?", (val, rid))
        conn.commit()
        print(f"💧 Volume de {val} ml défini pour {len(rowids)} échantillons.")
        mettre_a_jour_tableau(None)  # <-- force rafraîchissement tableau


    def saisir_volume_autre():
        val = simpledialog.askinteger("Volume personnalisé", "Entrez le volume (ml) :", minvalue=1)
        if val:
            fixer_volume(val)

    # --- Gauche : sélection des échantillons
    label = tk.Label(frame_left, text="Sélectionnez les échantillons à analyser :")
    label.pack(anchor="nw", pady=(0, 5))

    listbox = tk.Listbox(frame_left, selectmode="extended")
    listbox.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(frame_left, orient="vertical", command=listbox.yview)
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)

    btn_qui = tk.Button(frame_left, text="🧑‍🔬 Qui", command=fixer_qui)
    btn_qui.pack(pady=5)

    btn_date = tk.Button(frame_left, text="📅 Fixer date de prélèvement", command=saisir_date_prelevement)
    btn_date.pack(pady=5)

    frame_volume = tk.Frame(frame_left)
    tk.Label(frame_volume, text="Volume tubes :").pack(side="left", padx=5)
    for val in (2, 5, 20):
        tk.Button(frame_volume, text=f"{val} ml", command=lambda v=val: fixer_volume(v)).pack(side="left", padx=2)
    tk.Button(frame_volume, text="Autre", command=saisir_volume_autre).pack(side="left", padx=2)
    frame_volume.pack(pady=10)

    rafraichir_listbox()
    listbox.bind("<<ListboxSelect>>", mettre_a_jour_tableau)

    # --- Droite : tableau de mesures
    canvas = tk.Canvas(frame_right)
    scroll_y = tk.Scrollbar(frame_right, orient="vertical", command=canvas.yview)
    frame_table = tk.Frame(canvas)

    frame_table.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=frame_table, anchor="nw")
    canvas.configure(yscrollcommand=scroll_y.set)

    canvas.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")

    btn_calculer = tk.Button(frame_right, text="Calculer BDF et surligner", command=calculer_bdf)
    btn_calculer.pack(pady=10)
