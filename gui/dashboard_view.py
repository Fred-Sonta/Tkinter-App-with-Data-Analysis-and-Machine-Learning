import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from core.statistics import StatEngine

class DashboardView(ctk.CTkFrame):
    """
    Vue Dashboard Exécutif.
    Affiche les KPIs et graphiques compacts sans défilement.
    """
    def __init__(self, master, data_manager, **kwargs):
        super().__init__(master, **kwargs)
        self.data_manager = data_manager
        # Connexion au Moteur Statistique
        self.stats = StatEngine(self.data_manager)
        # Conteneurs pour les frames de graphiques (permet actualisation)
        self.chart_frames = {}
        
        # Grille Principale (2 colonnes, 4 lignes)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # KPI
        self.grid_rowconfigure(2, weight=4) # Graphes Haut
        self.grid_rowconfigure(3, weight=4) # Graphes Bas
        self.grid_columnconfigure((0, 1), weight=1)

        # 1. HEADER
        self.create_header()

        # 2. KPI CONTAINER
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        self.kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Chargement Initial
        self.load_kpis()
        
        # 3. GRAPHIQUES
        self.plot_histogram(row=2, col=0)
        self.plot_donut(row=2, col=1)
        self.plot_trend(row=3, col=0)
        self.plot_scatter(row=3, col=1)

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(header, text="🚀 Tableau de Bord Exécutif", font=("Roboto Medium", 20), text_color="#1C1C1E").pack(side="left")
        ctk.CTkLabel(header, text="● LIVE DATA", text_color="#34C759", font=("Roboto Medium", 10)).pack(side="right")

    def load_kpis(self):
        # Récupération données réelles via StatEngine
        kpis = self.stats.get_kpis()
        
        # Nettoyage
        for w in self.kpi_frame.winfo_children(): w.destroy()
            
        self.create_kpi_card(0, "Clients Totaux", str(kpis['total_clients']), "#0A84FF")
        self.create_kpi_card(1, "Encours Global", kpis['total_encours'], "#34C759")
        self.create_kpi_card(2, "Score Moyen", str(kpis['score_moyen']), "#FF9500")
        self.create_kpi_card(3, "Anomalies", str(kpis['anomalies']), "#FF3B30")
        # Actualiser graphiques avec les données fraîches
        self.refresh_plots()

    def create_kpi_card(self, col, title, value, color):
        card = ctk.CTkFrame(self.kpi_frame, fg_color="#FFFFFF", border_width=1, border_color="#E5E5EA", corner_radius=8)
        card.grid(row=0, column=col, padx=5, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(card, text=title.upper(), font=("Roboto", 10, "bold"), text_color="#8E8E93").pack(pady=(10, 0))
        ctk.CTkLabel(card, text=value, font=("Roboto Medium", 22), text_color="#1C1C1E").pack(pady=5)
        ctk.CTkFrame(card, height=3, fg_color=color).pack(fill="x", side="bottom")

    # --- FACTORY GRAPHIQUES ---

    def create_chart_frame(self, title, row, col):
        # Si un ancien frame existe pour ce titre, le détruire pour éviter les duplications
        if title in self.chart_frames:
            try:
                self.chart_frames[title].destroy()
            except Exception:
                pass

        frame = ctk.CTkFrame(self, fg_color="#FFFFFF", border_width=1, border_color="#E5E5EA", corner_radius=10)
        frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        self.chart_frames[title] = frame

        header = ctk.CTkFrame(frame, fg_color="transparent", height=20)
        header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header, text=title, font=("Roboto", 12, "bold"), text_color="#1C1C1E").pack(side="left")

        return frame

    def setup_fig(self, fig, ax):
        # Thème Blanc "Apple"
        bg = "#FFFFFF"
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        
        # Suppression bordures
        for spine in ax.spines.values(): spine.set_visible(False)
        
        # Textes
        ax.tick_params(colors="#8E8E93", labelsize=7)
        ax.xaxis.label.set_color("#8E8E93")
        ax.yaxis.label.set_color("#8E8E93")
        ax.grid(color="#E5E5EA", linestyle=":", linewidth=0.5, alpha=0.5)

    # --- PLOTS (Données Réelles) ---

    def plot_histogram(self, row, col):
        frame = self.create_chart_frame("Distribution Âge", row, col)
        data = self.stats.get_age_dist() 
        
        fig, ax = plt.subplots(figsize=(4, 2.5), dpi=100)
        self.setup_fig(fig, ax)
        
        if data:
            ax.hist(data, bins=10, color="#0A84FF", alpha=0.8, rwidth=0.9, edgecolor=None)
        
        plt.tight_layout()
        self.embed(fig, frame)

    def plot_donut(self, row, col):
        frame = self.create_chart_frame("Segmentation", row, col)
        labels, sizes = self.stats.get_segment_dist() 
        
        fig, ax = plt.subplots(figsize=(4, 2.5), dpi=100)
        fig.patch.set_facecolor("#FFFFFF")
        
        if sizes:
            colors = ['#0A84FF', '#FF9500', '#34C759', '#FF3B30']
            ax.pie(sizes, labels=labels, autopct='%1.0f%%', startangle=90, colors=colors,
                   textprops={'color':"#1C1C1E", 'fontsize': 7}, pctdistance=0.8)
            # Trou central
            fig.gca().add_artist(plt.Circle((0,0), 0.60, fc='#FFFFFF'))
        
        plt.tight_layout()
        self.embed(fig, frame)

    def plot_trend(self, row, col):
        frame = self.create_chart_frame("Tendance Solde (Ancienneté)", row, col)
        x, y = self.stats.get_time_series() 
        
        fig, ax = plt.subplots(figsize=(4, 2.5), dpi=100)
        self.setup_fig(fig, ax)
        
        if x:
            ax.plot(x, y, color="#34C759", linewidth=2)
            ax.fill_between(x, y, color="#34C759", alpha=0.1)
        
        plt.tight_layout()
        self.embed(fig, frame)

    def plot_scatter(self, row, col):
        frame = self.create_chart_frame("Corrélation Âge/Solde", row, col)
        x, y = self.stats.get_scatter_data() 
        
        fig, ax = plt.subplots(figsize=(4, 2.5), dpi=100)
        self.setup_fig(fig, ax)
        
        if x:
            ax.scatter(x, y, color="#FF9500", alpha=0.6, s=15, edgecolors='none')
        
        plt.tight_layout()
        self.embed(fig, frame)

    def embed(self, fig, parent):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    def refresh_plots(self):
        """Reconstruit les 4 graphiques avec les données actuelles."""
        # Appel aux factories de plots — les frames existants seront détruits dans create_chart_frame
        self.plot_histogram(row=2, col=0)
        self.plot_donut(row=2, col=1)
        self.plot_trend(row=3, col=0)
        self.plot_scatter(row=3, col=1)

        