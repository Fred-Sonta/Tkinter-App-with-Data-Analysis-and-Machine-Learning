import customtkinter as ctk
from tkinter import messagebox
from core.anomaly import AnomalyDetector

# --- CLASSE FORMULAIRE (POP-UP) ---
class ClientFormDialog(ctk.CTkToplevel):
    """
    Fenêtre modale pour Ajouter ou Modifier un client.
    """
    def __init__(self, parent, title, client_data=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x600")
        self.resizable(False, False)
        self.result = None 
        
        # Rend la fenêtre modale 
        self.grab_set()
        self.focus_force()

        # Conteneur principal avec marges
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Titre
        ctk.CTkLabel(main_frame, text=title, font=("Roboto Medium", 22)).pack(pady=(0, 20))

        # Champs de saisie
        self.entry_nom = self.create_field(main_frame, "Nom Complet", client_data.get('nom', '') if client_data else '')
        self.entry_age = self.create_field(main_frame, "Âge", client_data.get('age', '') if client_data else '')
        
        # Région
        self.create_label(main_frame, "Région")
        self.combo_region = ctk.CTkOptionMenu(main_frame, values=["Abidjan", "Bouaké", "Yamoussoukro", "San-Pédro", "Korhogo", "Daloa", "Man"])
        if client_data and client_data['region']: self.combo_region.set(client_data['region'])
        self.combo_region.pack(fill="x", pady=(5, 15))

        # Revenu
        self.entry_revenu = self.create_field(main_frame, "Revenu Mensuel (€)", client_data.get('revenu', 0) if client_data else '')
        
        # Solde (Ajouté car critique pour le scoring)
        self.entry_solde = self.create_field(main_frame, "Solde Actuel (€)", client_data.get('solde', 0) if client_data else '')

        # Segment
        self.create_label(main_frame, "Segment Client")
        self.seg_segment = ctk.CTkSegmentedButton(main_frame, values=["Standard", "VIP", "Nouveau"])
        self.seg_segment.set(client_data.get('segment', 'Standard') if client_data else 'Standard')
        self.seg_segment.pack(fill="x", pady=(5, 20))

        # Boutons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")
        
        ctk.CTkButton(btn_frame, text="Annuler", fg_color="transparent", border_width=1, 
                      text_color=("gray10", "gray90"), command=self.destroy).pack(side="left", expand=True, padx=5)
        
        ctk.CTkButton(btn_frame, text="Enregistrer", fg_color="#007AFF", # Bleu Apple
                      command=self.on_save).pack(side="right", expand=True, padx=5)

    def create_label(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Roboto", 12, "bold"), text_color=("gray50", "gray70")).pack(anchor="w")

    def create_field(self, parent, label, value):
        self.create_label(parent, label)
        entry = ctk.CTkEntry(parent, height=35)
        entry.insert(0, str(value))
        entry.pack(fill="x", pady=(5, 15))
        return entry

    def on_save(self):
        # Validation
        try:
            age = int(self.entry_age.get())
            revenu = float(self.entry_revenu.get())
            solde = float(self.entry_solde.get())
            nom = self.entry_nom.get().strip()
            
            if not nom: raise ValueError("Le nom est vide")
            
            self.result = {
                "nom": nom,
                "age": age,
                "region": self.combo_region.get(),
                "revenu": revenu,
                "solde": solde,
                "segment": self.seg_segment.get(),
                "sexe": "M" 
            }
            self.destroy()
        except ValueError:
            messagebox.showerror("Erreur de Saisie", "Veuillez vérifier les champs numériques (Âge, Revenu, Solde).")


# --- VUE PRINCIPALE ---
class ClientManagerView(ctk.CTkFrame):
    def __init__(self, master, data_manager, **kwargs):
        super().__init__(master, **kwargs)
        self.data_manager = data_manager
        self.selected_client_id = None
        self.page_size = 10
        
        # Initialisation Moteur ML
        self.ai_engine = AnomalyDetector()
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) 

        # 1. TOOLBAR
        self.create_toolbar()
        # 2. FILTRES
        self.create_filters()
        # 3. HEADER TABLEAU
        self.create_grid_header()
        # 4. GRILLE (SCROLLABLE)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Chargement initial
        self.refresh_list()

    def create_toolbar(self):
        toolbar = ctk.CTkFrame(self, height=60, fg_color="#FFFFFF", border_width=1, border_color="#E5E5EA", corner_radius=10) # Fond style iOS
        toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(toolbar, text="Gestion Clients", font=("Roboto Medium", 20), text_color="#1C1C1E").pack(side="left", padx=20)

        # Boutons Actions
        self.btn_export = self.add_tool_btn(toolbar, "⬇️ Export CSV", "transparent", self.action_export, border=True)
        self.btn_delete = self.add_tool_btn(toolbar, "🗑️ Supprimer", "#FF3B30", self.action_delete, state="disabled")
        self.btn_edit = self.add_tool_btn(toolbar, "✏️ Modifier", "#A8D0E9", self.action_edit, state="disabled")
        self.btn_add = self.add_tool_btn(toolbar, "+ Nouveau", "#34C759", self.action_add)

    def add_tool_btn(self, parent, text, color, command, state="normal", border=False):
        btn = ctk.CTkButton(parent, text=text, fg_color=color, command=command, state=state, width=120, height=35)
        if border:
            btn.configure(border_width=1, border_color="gray50", text_color=("black", "white"))
        btn.pack(side="right", padx=10)
        return btn

    def create_filters(self):
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        
        # Région
        ctk.CTkLabel(filter_frame, text="Région:", text_color="#1C1C1E").pack(side="left", padx=(0, 5))
        self.filter_region = ctk.CTkOptionMenu(filter_frame, values=["Toutes", "Abidjan", "Bouaké", "San-Pédro", "Yamoussoukro"], width=130, command=self.apply_filters_event)
        self.filter_region.pack(side="left")

        # Risque
        ctk.CTkLabel(filter_frame, text="Risque:", text_color="#1C1C1E").pack(side="left", padx=(20, 5))
        self.filter_risk = ctk.CTkSegmentedButton(filter_frame, values=["Tous", "Faible", "Moyen", "Élevé"], command=self.apply_filters_event)
        self.filter_risk.set("Tous")
        self.filter_risk.pack(side="left")

        # Recherche
        self.entry_search = ctk.CTkEntry(filter_frame, placeholder_text="🔍 Rechercher (Nom)...", width=250)
        self.entry_search.pack(side="right")
        self.entry_search.bind("<Return>", self.apply_filters_event) 
        
        ctk.CTkButton(filter_frame, text="Go", width=50, command=self.apply_filters).pack(side="right", padx=5)

        # Sélecteur du nombre de lignes à afficher (Pagination simple)
        ctk.CTkLabel(filter_frame, text="Lignes:", text_color="#1C1C1E").pack(side="right", padx=(10,5))
        self.page_size_menu = ctk.CTkOptionMenu(filter_frame, values=["10", "15", "20", "30"], width=80, command=self.on_pagesize_change)
        self.page_size_menu.set(str(self.page_size))
        self.page_size_menu.pack(side="right")

    def create_grid_header(self):
        header = ctk.CTkFrame(self, height=40, fg_color="#F5F5F5", corner_radius=5, border_width=1, border_color="#E5E5EA")
        header.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 5))
        header.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
        
        cols = ["ID", "NOM COMPLET", "ÂGE", "RÉGION", "REVENU", "RISQUE", "SCORE"]
        for i, col in enumerate(cols):
            ctk.CTkLabel(header, text=col, font=("Roboto", 11, "bold"), text_color="#1C1C1E").grid(row=0, column=i, sticky="w", padx=10, pady=10)

    # --- LOGIQUE MÉTIER ---

    def refresh_list(self, clients=None):
        """Recharge la liste (soit tout, soit filtré)"""
        if clients is None:
            clients = self.data_manager.get_all_clients()
        
        # Entraînement rapide de l'IA sur les données actuelles
        self.ai_engine.train_model(clients)

        # Nettoyage affichage
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.selected_client_id = None
        self.update_buttons()

        # Appliquer limitation du nombre de lignes (pagination simple)
        try:
            limit = int(self.page_size)
        except Exception:
            limit = 10

        for idx, client in enumerate(clients[:limit]):
            self.create_row(client, idx)

    def create_row(self, client, index):
        bg_color = "#FFFFFF" if index % 2 == 0 else "#F9F9FB"
        
        # Détection Fraude IA
        is_anomaly, _ = self.ai_engine.predict_risk(client)
        border_color = "#FF3B30" if is_anomaly else "transparent"
        border_width = 2 if is_anomaly else 0

        row = ctk.CTkFrame(self.scroll_frame, corner_radius=5, fg_color=bg_color, border_width=1, border_color="#E5E5EA")
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        # Interaction
        row.bind("<Button-1>", lambda e, cid=client['id_client'], r=row: self.on_select(cid, r))

        values = [
            str(client['id_client']),
            client['nom'],
            f"{client['age']} ans" if client['age'] else "N/A",
            client['region'] if client['region'] else "-",
            f"{client['revenu']:.2f} €" if client['revenu'] else "0 €",
            client['niveau_risque'] if client['niveau_risque'] else "N/A", 
            str(int(client['score'])) if client['score'] else "-"
        ]

        for i, val in enumerate(values):
            lbl = ctk.CTkLabel(row, text=val, font=("Roboto", 12), text_color="#1C1C1E")
            lbl.grid(row=0, column=i, sticky="w", padx=10, pady=10)
            lbl.bind("<Button-1>", lambda e, cid=client['id_client'], r=row: self.on_select(cid, r))
            
            # Couleur rouge pour risque élevé ou solde négatif
            if (i == 4 and client.get('solde', 0) < 0) or (i == 5 and val == "Élevé"):
                lbl.configure(text_color="#FF453A")

    def on_select(self, cid, row_widget):
        for widget in self.scroll_frame.winfo_children():
            widget.configure(fg_color="#FFFFFF") 
        
        row_widget.configure(fg_color="#E0F2FE") 
        self.selected_client_id = cid
        self.update_buttons()

    def update_buttons(self):
        state = "normal" if self.selected_client_id else "disabled"
        self.btn_edit.configure(state=state)
        self.btn_delete.configure(state=state)

    # --- ACTIONS RÉELLES ---

    def apply_filters_event(self, event):
        self.apply_filters()

    def on_pagesize_change(self, value):
        """Callback when page size OptionMenu changes."""
        try:
            self.page_size = int(value)
        except Exception:
            self.page_size = 10
        # Re-apply current filters to refresh the view with the new page size
        self.apply_filters()

    def apply_filters(self):
        # Appel au Backend DataManager
        results = self.data_manager.filtrer_clients(
            region=self.filter_region.get(),
            risque=self.filter_risk.get(),
            recherche=self.entry_search.get()
        )
        self.refresh_list(results)

    def action_add(self):
        dialog = ClientFormDialog(self, "Nouveau Client")
        self.wait_window(dialog)
        if dialog.result:
            self.data_manager.add_client(dialog.result) # INSERT SQL
            self.refresh_list() # Relecture SQL
            messagebox.showinfo("Succès", "Client ajouté avec succès.")

    def action_edit(self):
        if not self.selected_client_id: return
        # Récupérer données fraîches
        clients = self.data_manager.get_all_clients()
        client = next((c for c in clients if c['id_client'] == self.selected_client_id), None)
        
        if client:
            # Conversion Row -> Dict pour l'édition
            c_dict = dict(client)
            dialog = ClientFormDialog(self, "Modifier Client", client_data=c_dict)
            self.wait_window(dialog)
            if dialog.result:
                self.data_manager.update_client(self.selected_client_id, dialog.result) # UPDATE SQL
                self.refresh_list()

    def action_delete(self):
        if not self.selected_client_id: return
        if messagebox.askyesno("Confirmation", "Supprimer définitivement ce client ?"):
            self.data_manager.delete_client(self.selected_client_id) # DELETE SQL
            self.refresh_list()

    # Méthode d'Export CSV

    def action_export(self):
        # 1. On récupère les filtres actuels pour savoir quoi exporter
        current_region = self.filter_region.get()
        current_risk = self.filter_risk.get()
        current_search = self.entry_search.get()

        # 2. On demande au DataManager les données correspondantes
        data_to_export = self.data_manager.filtrer_clients(
            region=current_region, 
            risque=current_risk, 
            recherche=current_search
        )

        if not data_to_export:
            messagebox.showwarning("Export vide", "Aucune donnée à exporter avec les filtres actuels.")
            return

        # 3. Boite de dialogue "Enregistrer sous"
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(defaultextension=".csv", 
                                                filetypes=[("Fichier CSV", "*.csv")],
                                                initialfile="Clients_Filtrés.csv")
        
        if filename:
            success = self.data_manager.export_data_to_csv(data_to_export, filename)
            if success:
                messagebox.showinfo("Export Réussi", f"Fichier généré :\n{filename}")
            else:
                messagebox.showerror("Erreur", "Échec de l'exportation.")
