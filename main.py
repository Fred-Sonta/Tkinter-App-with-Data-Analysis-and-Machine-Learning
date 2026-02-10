import customtkinter as ctk
import os
import sys
from PIL import Image
from tkinter import messagebox, simpledialog

# Import du Core
from core.data_manager import DataManager
from core.scoring_model import ScoringModel

# Import des Vues
from gui.dashboard_view import DashboardView
from gui.clients_view import ClientManagerView
from gui.analytics_view import AnalyticsView
from gui.import_view import ImportView
from gui.transactions_view import TransactionsView

# --- CONFIGURATION DU THÈME  ---
ctk.set_appearance_mode("Light") 
ctk.set_default_color_theme("blue") 

# Palette de couleurs 
COLOR_BG = "#F5F5F7"       # Gris fond d'écran
COLOR_CARD = "#FFFFFF"     # Blanc pur pour les cartes
COLOR_TEXT_MAIN = "#1D1D1F" # Gris anthracite (Titres)
COLOR_TEXT_SUB = "#86868b"  # Gris moyen (Sous-titres)
COLOR_ACCENT = "#007AFF"    # Bleu Apple (Boutons)
COLOR_BORDER = "#E5E5EA"    # Gris très clair pour les bordures

# --- Helpers ---
def load_image(filename, size):
    path = os.path.join("assets", filename)
    if os.path.exists(path):
        return ctk.CTkImage(light_image=Image.open(path), dark_image=Image.open(path), size=size)
    print(f"Warning: Image {filename} not found.")
    return None

class WelcomeView(ctk.CTkFrame):
    """
    Page d'Accueil 'One-Screen' - Design Apple Épuré.
    Tout est visible sans défilement.
    """
    def __init__(self, master, switch_callback, quit_callback, **kwargs):
        super().__init__(master, fg_color=COLOR_BG, **kwargs)
        
        # Grille Principale : 2 Lignes.
        # Ligne 0 : Hero Section (Texte + Image) 
        # Ligne 1 : Features (Cartes) 
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=3) 
        self.grid_rowconfigure(1, weight=2) 

        # --- 1. HERO SECTION (Haut) ---
        self.create_hero_section(switch_callback)

        # --- 2. FEATURES SECTION (Bas) ---
        self.create_features_section()

        # --- 3. PETIT FOOTER (Flottant en bas à droite) ---
        self.btn_quit = ctk.CTkButton(self, text="Fermer l'application", 
                                      fg_color="transparent", text_color="#EA180D",
                                      hover_color="#E5E5EA", height=25,
                                      font=("Roboto", 11), command=quit_callback)
        self.btn_quit.place(relx=0.98, rely=0.98, anchor="se")

    def create_hero_section(self, switch_callback):
        hero_frame = ctk.CTkFrame(self, fg_color="transparent")
        hero_frame.grid(row=0, column=0, sticky="nsew", padx=60, pady=(60, 20))
        hero_frame.grid_columnconfigure(0, weight=4) # Colonne Texte (40%)
        hero_frame.grid_columnconfigure(1, weight=6) # Colonne Image (60%)
        hero_frame.grid_rowconfigure(0, weight=1)

        # A. Bloc Texte (Gauche)
        text_container = ctk.CTkFrame(hero_frame, fg_color="transparent")
        text_container.grid(row=0, column=0, sticky="w")

        # Logo
        logo = load_image("logo.jpg", (64, 64))
        if logo:
            ctk.CTkLabel(text_container, text="", image=logo).pack(anchor="w", pady=(0, 20))

        # Titre Géant
        ctk.CTkLabel(text_container, text="Tk-Finance", 
                     font=("Roboto Medium", 54), text_color=COLOR_TEXT_MAIN).pack(anchor="w")
        
        # Slogan
        ctk.CTkLabel(text_container, text="L'intelligence financière,\nsimplement.", 
                     font=("Roboto", 24), text_color=COLOR_TEXT_SUB, justify="left").pack(anchor="w", pady=(5, 30))

        # Pitch court
        pitch = "Importez vos données, détectez les fraudes et visualisez\nvos KPIs en un seul clic. Une solution tout-en-un pour\nles analystes exigeants."
        ctk.CTkLabel(text_container, text=pitch, font=("Roboto", 14), 
                     text_color="#515154", justify="left").pack(anchor="w", pady=(0, 30))

        # Bouton CTA (Call to Action)
        btn = ctk.CTkButton(text_container, text="Commencer l'Importation  →", 
                            font=("Roboto Medium", 16), height=50, width=240, corner_radius=25,
                            fg_color=COLOR_ACCENT, hover_color="#0062CC",
                            command=lambda: switch_callback("import"))
        btn.pack(anchor="w")

        # B. Bloc Image (Droite)
        img_container = ctk.CTkFrame(hero_frame, fg_color="transparent")
        img_container.grid(row=0, column=1, sticky="nsew", padx=(40, 0))
        
        # On essaie de charger la bannière en grand
        banner = load_image("banner.jpg", (700, 400)) 
        if banner:
            lbl_img = ctk.CTkLabel(img_container, text="", image=banner)
            lbl_img.pack(expand=True, fill="both") # Centré
        else:
            # Fallback élégant
            fb = ctk.CTkFrame(img_container, fg_color="#E1E1E6", corner_radius=20)
            fb.pack(expand=True, fill="both")
            ctk.CTkLabel(fb, text="[Image Hero]", text_color="gray").place(relx=0.5, rely=0.5, anchor="center")

    def create_features_section(self):
        feat_frame = ctk.CTkFrame(self, fg_color="transparent")
        feat_frame.grid(row=1, column=0, sticky="nsew", padx=60, pady=(0, 60))
        feat_frame.grid_columnconfigure((0, 1, 2), weight=1) # 3 Colonnes égales

        # Carte 1 : Database
        self.add_feature_card(feat_frame, 0, "db.png", "Centralisation", 
                              "🪄Import et nettoyage automatique de vos fichiers clients.")
        
        # Carte 2 : Analytics
        self.add_feature_card(feat_frame, 1, "stat.png", "Analytique", 
                              "📊Tableaux de bord et rapports financiers en temps réel.")
        
        # Carte 3 : IA
        self.add_feature_card(feat_frame, 2, "ai.png", "Sécurité I.A.", 
                              "🤖Détection proactive des anomalies et scoring risque.")
    def add_feature_card(self, parent, col, icon_name, title, desc):
        # Carte blanche avec bordure subtile
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=16, 
                            border_width=1, border_color=COLOR_BORDER)
        card.grid(row=0, column=col, sticky="nsew", padx=15, pady=10)
        
        # Contenu centré
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(expand=True, fill="x", padx=20, pady=20)

        # Icone
        icon = load_image(icon_name, (42, 42))
        if icon:
            ctk.CTkLabel(inner, text="", image=icon).pack(anchor="w", pady=(0, 15))
        else:
            ctk.CTkLabel(inner, text="⚡", font=("Arial", 28), text_color=COLOR_ACCENT).pack(anchor="w", pady=(0, 15))

        # Titre
        ctk.CTkLabel(inner, text=title, font=("Roboto Medium", 18), text_color=COLOR_TEXT_MAIN).pack(anchor="w", pady=(0, 5))
        
        # Description
        ctk.CTkLabel(inner, text=desc, font=("Roboto", 13), text_color=COLOR_TEXT_SUB, 
                     wraplength=220, justify="left").pack(anchor="w")


class TkFinanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Tk-Finance - Manager 2026")
        self.geometry("1280x800")
        
        try:
            self.iconbitmap("assets/logo.jpg")
        except: pass

        # 1. Backend
        self.db = DataManager()
        self.scorer = ScoringModel(self.db)

        # 2. Layout Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (Adaptée au thème clair) ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#FFFFFF") # Blanc sidebar
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)
        
        # Logo Sidebar
        logo_mini = load_image("logo.jpg", (32, 32))
        if logo_mini:
            ctk.CTkLabel(self.sidebar, text="", image=logo_mini).grid(row=0, column=0, pady=(40, 10))
            
        ctk.CTkLabel(self.sidebar, text="Tk-Finance", font=("Roboto Medium", 18), text_color=COLOR_TEXT_MAIN).grid(row=1, column=0, pady=(0, 30))

        # Boutons Menu
        self.btn_home = self.create_nav_btn("🏠 Accueil", "welcome", 2)
        self.btn_import = self.create_nav_btn("📡 Import / ETL", "import", 3)
        self.btn_dash = self.create_nav_btn("📊 Dashboard", "dashboard", 4)
        self.btn_trans = self.create_nav_btn("💳 Transactions", "transactions", 5)
        self.btn_clients = self.create_nav_btn("👥 Clients", "clients", 6)
        self.btn_ana = self.create_nav_btn("📈 Analyses", "analytics", 7)

        # Bouton sécurisé pour vider la BDD 
        self.btn_clear_db = ctk.CTkButton(self.sidebar, text="⚠️ Vider BDD", fg_color="transparent",
                         text_color="#EA180D", hover_color="#FDECEA",
                         anchor="w", height=40, font=("Roboto Medium", 13),
                         command=self.action_clear_db)
        self.btn_clear_db.grid(row=9, column=0, sticky="ew", padx=15, pady=(10,20))

        # --- VUES ---
        self.welcome_view = WelcomeView(self, self.show_view, self.quit_app)
        self.import_view = ImportView(self, self.db)
        self.dashboard_view = DashboardView(self, self.db)
        self.clients_view = ClientManagerView(self, self.db)
        self.analytics_view = AnalyticsView(self, self.db)
        self.transactions_view = TransactionsView(self, self.db)

        self.show_view("welcome")

    def create_nav_btn(self, text, name, row):
        # Boutons adaptés au thème clair (Gris foncé texte, Hover gris clair)
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", 
                            text_color="#515154", 
                            hover_color="#F5F5F7", 
                            anchor="w", height=45, font=("Roboto Medium", 13),
                            command=lambda: self.show_view(name))
        btn.grid(row=row, column=0, sticky="ew", padx=15, pady=2)
        return btn

    def show_view(self, name):
        # 1. Cacher tout
        for v in [self.welcome_view, self.import_view, self.dashboard_view, 
                  self.transactions_view, self.clients_view, self.analytics_view]:
            v.grid_forget()
        
        # 2. Reset boutons (Style actif vs inactif)
        for b in [self.btn_home, self.btn_import, self.btn_dash, 
                  self.btn_trans, self.btn_clients, self.btn_ana]:
            b.configure(fg_color="transparent", text_color="#515154")

        # 3. Affichage
        btn_active_color = "#E5F1FF" 
        text_active_color = "#007AFF" 

        if name == "welcome":
            self.welcome_view.grid(row=0, column=1, sticky="nsew")
            self.btn_home.configure(fg_color=btn_active_color, text_color=text_active_color)
        
        elif name == "import":
            self.import_view.grid(row=0, column=1, sticky="nsew")
            self.btn_import.configure(fg_color=btn_active_color, text_color=text_active_color)
            
        elif name == "dashboard":
            self.scorer.calculate_all_scores() 
            self.dashboard_view.load_kpis()
            self.dashboard_view.grid(row=0, column=1, sticky="nsew")
            self.btn_dash.configure(fg_color=btn_active_color, text_color=text_active_color)

        elif name == "transactions":
            self.transactions_view.refresh_list()
            self.transactions_view.grid(row=0, column=1, sticky="nsew")
            self.btn_trans.configure(fg_color=btn_active_color, text_color=text_active_color)
            
        elif name == "clients":
            self.clients_view.refresh_list()
            self.clients_view.grid(row=0, column=1, sticky="nsew")
            self.btn_clients.configure(fg_color=btn_active_color, text_color=text_active_color)
            
        elif name == "analytics":
            try: self.analytics_view.refresh() # Si méthode existe
            except: pass
            self.analytics_view.grid(row=0, column=1, sticky="nsew")
            self.btn_ana.configure(fg_color=btn_active_color, text_color=text_active_color)

    def quit_app(self):
        self.destroy()
        sys.exit()

    def action_clear_db(self):
        """
        Action sécurisée déclenchée par le bouton 'Vider BDD'.
        """
        # 1) Demande une confirmation oui/non
        ok = messagebox.askyesno("Confirmer effacement", 
                                 "Vous êtes sur le point de supprimer TOUTES les données de la base.\nCette action est irréversible. Continuer ?")
        if not ok:
            return

        # 2) Demande la phrase de confirmation (sécurité additionnelle)
        confirm_phrase = simpledialog.askstring("Confirmation requise", 
                                                "Tapez YES pour valider l'effacement:", parent=self)
        if not confirm_phrase or confirm_phrase.strip().upper() != "YES":
            messagebox.showwarning("Annulé", "Phrase incorrecte — opération annulée.")
            return

        # 3) Exécution et retour utilisateur
        try:
            self.db.clear_all()
            messagebox.showinfo("Terminé", "La base de données a été vidée avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de vider la BDD : {e}")

if __name__ == "__main__":
    app = TkFinanceApp()
    app.mainloop()

