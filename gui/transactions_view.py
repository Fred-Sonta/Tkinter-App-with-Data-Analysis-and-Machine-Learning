import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

class TransactionDialog(ctk.CTkToplevel):
    """Fenêtre pour ajouter une opération financière"""
    def __init__(self, parent, client_list):
        super().__init__(parent)
        self.title("Nouvelle Transaction")
        self.geometry("400x450")
        self.resizable(False, False)
        self.grab_set()
        
        self.client_map = {f"{c['id_client']} - {c['nom']}": c['id_client'] for c in client_list}
        self.result = None

        # Titre
        ctk.CTkLabel(self, text="Enregistrer Opération", font=("Roboto Medium", 20)).pack(pady=20)

        # 1. Sélection Client
        ctk.CTkLabel(self, text="Client concerné", text_color="gray").pack(anchor="w", padx=40)
        self.combo_client = ctk.CTkOptionMenu(self, values=list(self.client_map.keys()))
        self.combo_client.pack(fill="x", padx=40, pady=(5, 15))

        # 2. Type d'opération (Visuel seulement, influe sur le signe)
        self.type_var = ctk.StringVar(value="Depot")
        ctk.CTkLabel(self, text="Type de mouvement", text_color="gray").pack(anchor="w", padx=40)
        seg = ctk.CTkSegmentedButton(self, values=["Dépôt (+)", "Retrait (-)"], 
                                     variable=self.type_var, command=self.update_color)
        seg.pack(fill="x", padx=40, pady=(5, 15))
        seg.set("Dépôt (+)")

        # 3. Montant
        ctk.CTkLabel(self, text="Montant (€)", text_color="gray").pack(anchor="w", padx=40)
        self.entry_montant = ctk.CTkEntry(self, placeholder_text="Ex: 500.00")
        self.entry_montant.pack(fill="x", padx=40, pady=(5, 15))

        # 4. Date (Auto par défaut)
        ctk.CTkLabel(self, text="Date (AAAA-MM-JJ)", text_color="gray").pack(anchor="w", padx=40)
        self.entry_date = ctk.CTkEntry(self)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.pack(fill="x", padx=40, pady=(5, 20))

        # Bouton Valider
        self.btn_save = ctk.CTkButton(self, text="Valider Transaction", fg_color="#34C759", command=self.on_save)
        self.btn_save.pack(pady=10)

    def update_color(self, value):
        if "Retrait" in value:
            self.btn_save.configure(fg_color="#FF3B30") # Rouge
        else:
            self.btn_save.configure(fg_color="#34C759") # Vert

    def on_save(self):
        try:
            montant = float(self.entry_montant.get())
            if montant <= 0: raise ValueError("Le montant doit être positif")
            
            # Appliquer le signe selon le type
            final_montant = montant if "Dépôt" in self.type_var.get() else -montant
            
            client_str = self.combo_client.get()
            id_client = self.client_map[client_str]
            date_trans = self.entry_date.get()

            self.result = {
                "id_client": id_client,
                "montant": final_montant,
                "date": date_trans
            }
            self.destroy()
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide.")


class TransactionsView(ctk.CTkFrame):
    """
    Vue 'Livre de Comptes'.
    Affiche l'historique et permet d'ajouter des mouvements.
    """
    def __init__(self, master, data_manager, **kwargs):
        super().__init__(master, **kwargs)
        self.data_manager = data_manager
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. HEADER & KPI RAPIDES
        self.create_header()

        # 2. BARRE D'OUTILS (Recherche + Ajout)
        self.create_toolbar()

        # 3. TABLEAU DES TRANSACTIONS
        # En-têtes
        self.header_frame = ctk.CTkFrame(self, height=40, fg_color="#F5F5F5", border_width=1, border_color="#E5E5EA")
        self.header_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.header_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        cols = ["DATE", "CLIENT", "MONTANT", "TYPE"]
        for i, col in enumerate(cols):
            ctk.CTkLabel(self.header_frame, text=col, font=("Roboto", 11, "bold"), text_color="#1C1C1E").grid(row=0, column=i, sticky="w", padx=10, pady=5)

        # Liste scrollable
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

        self.refresh_list()

    def create_header(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Historique des Transactions", font=("Roboto Medium", 22), text_color="#1C1C1E").pack(side="left")
        
        # Petit résumé total 
        self.lbl_volume = ctk.CTkLabel(frame, text="Volume: 0 €", font=("Consolas", 14), text_color="#0A84FF")
        self.lbl_volume.pack(side="right")

    def create_toolbar(self):
        # On insère la toolbar DANS le header frame ou juste en dessous. 
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="e", padx=20, pady=20) 
        
        # Recherche
        self.entry_search = ctk.CTkEntry(toolbar, placeholder_text="🔍 Filtrer par client...", width=200)
        self.entry_search.pack(side="left", padx=10)
        self.entry_search.bind("<Return>", lambda e: self.refresh_list())
        
        # Bouton Nouveau
        ctk.CTkButton(toolbar, text="+ Nouvelle Opération", fg_color="#0A84FF", 
                      command=self.action_add).pack(side="left")

    def refresh_list(self):
        # Nettoyage
        for w in self.scroll_frame.winfo_children(): w.destroy()
        
        # Récupération Data
        search = self.entry_search.get()
        txs = self.data_manager.get_all_transactions(search)
        
        total_vol = 0
        
        for idx, tx in enumerate(txs):
            self.create_row(tx, idx)
            total_vol += abs(tx['montant']) # Volume absolu échangé
            
        self.lbl_volume.configure(text=f"Volume Échangé: {total_vol:,.2f} €")

    def create_row(self, tx, idx):
        bg = "#FFFFFF" if idx % 2 == 0 else "#F9F9FB"
        row = ctk.CTkFrame(self.scroll_frame, fg_color=bg, corner_radius=5, border_width=1, border_color="#E5E5EA")
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Formatage
        date_obj = datetime.strptime(tx['date_trans'], "%Y-%m-%d") if tx['date_trans'] else datetime.now()
        date_str = date_obj.strftime("%d/%m/%Y")
        
        montant = tx['montant']
        color = "#34C759" if montant >= 0 else "#FF3B30" # Vert ou Rouge
        type_op = "DÉPÔT" if montant >= 0 else "RETRAIT"
        signe = "+" if montant >= 0 else ""
        
        # Cellules
        ctk.CTkLabel(row, text=date_str, text_color="#1C1C1E").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        ctk.CTkLabel(row, text=tx['nom'], font=("Roboto", 12, "bold"), text_color="#1C1C1E").grid(row=0, column=1, sticky="w", padx=10)
        ctk.CTkLabel(row, text=f"{signe}{montant:.2f} €", text_color=color, font=("Consolas", 12, "bold")).grid(row=0, column=2, sticky="w", padx=10)
        
        # Badge Type
        badge_bg = "#E8F5E9" if montant >= 0 else "#FFEBEE"
        badge = ctk.CTkLabel(row, text=type_op, font=("Roboto", 10), text_color=color, 
                             fg_color=badge_bg, corner_radius=5)
        badge.grid(row=0, column=3, sticky="w", padx=10)

    def action_add(self):
        # On a besoin de la liste des clients pour le menu déroulant
        clients = self.data_manager.get_all_clients()
        if not clients:
            messagebox.showwarning("Attention", "Aucun client dans la base. Importez ou créez des clients d'abord.")
            return

        dialog = TransactionDialog(self, clients)
        self.wait_window(dialog)
        
        if dialog.result:
            self.data_manager.add_transaction(
                dialog.result['id_client'], 
                dialog.result['montant'], 
                dialog.result['date']
            )
            self.refresh_list() # Rafraîchir l'affichage
            messagebox.showinfo("Succès", "Opération enregistrée et solde mis à jour.")


            