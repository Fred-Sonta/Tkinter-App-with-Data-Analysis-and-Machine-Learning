import customtkinter as ctk
from tkinter import filedialog
import threading
import time
from core.data_cleaner import DataCleaner

class ImportView(ctk.CTkFrame):
    """
    Console ETL (Extract Transform Load) - Version Connectée.
    Pilote le module DataCleaner avec un retour visuel temps réel.
    """
    def __init__(self, master, data_manager, **kwargs):
        super().__init__(master, **kwargs)
        self.data_manager = data_manager
        self.file_path = None
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. HEADER
        self.create_header()

        # 2. WORKSPACE
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(1, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)

        self.create_control_panel()
        self.create_terminal()

    def create_header(self):
        header = ctk.CTkFrame(self, height=60, fg_color="#FFFFFF", border_width=1, border_color="#E5E5EA", corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(header, text="📡 Centre d'Importation & Nettoyage", font=("Roboto Medium", 18), text_color="#1C1C1E").pack(side="left", padx=20)
        
        self.step_labels = []
        steps = ["1. SÉLECTION", "2. AUDIT", "3. NETTOYAGE", "4. INJECTION BDD"]
        
        steps_frame = ctk.CTkFrame(header, fg_color="transparent")
        steps_frame.pack(side="right", padx=20)
        
        for step in steps:
            lbl = ctk.CTkLabel(steps_frame, text=step, font=("Roboto", 11, "bold"), text_color="#8E8E93")
            lbl.pack(side="left", padx=10)
            self.step_labels.append(lbl)

    def create_control_panel(self):
        panel = ctk.CTkFrame(self.main_area, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#E5E5EA")
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Zone Drop
        self.btn_select = ctk.CTkButton(panel, text="📂\n\nSÉLECTIONNER FICHIER (CSV/XLSX)", 
                                        font=("Roboto Medium", 14), fg_color="transparent", border_width=2, 
                                        border_color="#E5E5EA", text_color="#8E8E93",
                                        hover_color="#F5F5F5",
                                        command=self.select_file)
        self.btn_select.pack(fill="x", padx=20, pady=20, ipady=30)
        
        self.lbl_file = ctk.CTkLabel(panel, text="Aucun fichier", text_color="#8E8E93")
        self.lbl_file.pack(pady=(0, 20))

        # Boutons Processus
        self.btn_audit = ctk.CTkButton(panel, text="🔍 Lancer l'Audit", state="disabled", fg_color="#FFFFFF", border_width=1, border_color="#E5E5EA", text_color="#1C1C1E", command=self.run_audit)
        self.btn_audit.pack(fill="x", padx=20, pady=10)
        
        self.btn_clean = ctk.CTkButton(panel, text="✨ Nettoyer & Injecter", state="disabled", fg_color="#FFFFFF", border_width=1, border_color="#E5E5EA", text_color="#1C1C1E", command=self.run_clean)
        self.btn_clean.pack(fill="x", padx=20, pady=10)

        # Rapport rapide
        self.audit_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.audit_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.lbl_audit_res = ctk.CTkLabel(self.audit_frame, text="", justify="left", font=("Consolas", 12), text_color="#1C1C1E")
        self.lbl_audit_res.pack(anchor="w")

    def create_terminal(self):
        term_frame = ctk.CTkFrame(self.main_area, corner_radius=10, fg_color="#1C1C1E")
        term_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        top = ctk.CTkFrame(term_frame, height=25, fg_color="#333333", corner_radius=5)
        top.pack(fill="x")
        ctk.CTkLabel(top, text=" TERMINAL SYSTEME", font=("Consolas", 10, "bold"), text_color="white").pack(side="left", padx=10)

        self.console = ctk.CTkTextbox(term_frame, font=("Consolas", 11), text_color="#00FF00", fg_color="#1C1C1E")
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        self.log("System Ready...")

    def log(self, msg, type="INFO"):
        color = "#00FF00"
        if type == "ERROR": color = "#FF3B30"
        if type == "WARN": color = "#FF9500"
        self.console.insert("end", f"[{time.strftime('%H:%M:%S')}] [{type}] {msg}\n")
        self.console.see("end")

    def update_step(self, idx):
        for i, lbl in enumerate(self.step_labels):
            color = "#0A84FF" if i == idx else ("#34C759" if i < idx else "gray60")
            lbl.configure(text_color=color)

    # --- LOGIQUE ETL CONNECTÉE ---

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Data Files", "*.csv *.xlsx")])
        if path:
            self.file_path = path
            self.lbl_file.configure(text=f"📄 {path.split('/')[-1]}")
            self.log(f"Cible : {path}")
            self.btn_audit.configure(state="normal")
            self.update_step(0)

    def run_audit(self):
        self.update_step(1)
        self.log("Démarrage Audit...", "WARN")
        # Thread pour ne pas geler l'UI
        threading.Thread(target=self._thread_audit).start()

    def _thread_audit(self):
        # Utilisation du VRAI DataCleaner
        cleaner = DataCleaner(self.data_manager)
        df, report = cleaner.audit_file(self.file_path)
        
        if df is None:
            self.log(f"Echec lecture : {report}", "ERROR")
            return

        self.log(f"Lecture OK : {report['total_rows']} lignes.")
        self.log(f"Doublons détectés : {report['doublons']}", "WARN" if report['doublons'] > 0 else "INFO")
        
        # Affichage rapport visuel
        txt = f"Lignes: {report['total_rows']}\nDoublons: {report['doublons']}\nColonnes: {len(report['colonnes_detectees'])}"
        if report['statut'] == "CRITIQUE":
             self.log(f"Audit Critique : {report['message']}", "ERROR")
        else:
             self.btn_clean.configure(state="normal")
             self.log("Audit terminé. Prêt pour injection.", "SUCCESS")
        
        self.lbl_audit_res.configure(text=txt)

    def run_clean(self):
        self.update_step(2)
        self.log("Nettoyage & Injection...", "WARN")
        threading.Thread(target=self._thread_clean).start()

    def _thread_clean(self):
        cleaner = DataCleaner(self.data_manager)
        # On relit (ou on pourrait passer le DF, mais plus simple de relire pour thread safety)
        df, _ = cleaner.audit_file(self.file_path)
        
        self.log("Application filtre IQR (Outliers)...")
        self.log("Imputation valeurs manquantes...")
        
        # Injection
        self.update_step(3)
        count = cleaner.clean_and_inject(df)
        
        self.log(f"COMMIT BDD : {count} clients insérés.", "SUCCESS")
        self.update_step(4)

