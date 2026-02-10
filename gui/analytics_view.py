import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from core.statistics import StatEngine
from tkinter import filedialog, messagebox

class AnalyticsView(ctk.CTkScrollableFrame):
    """
    Vue Analytique Avancée.
    Tableaux croisés, Heatmaps et Storytelling statistique.
    """
    def __init__(self, master, data_manager, **kwargs):
        super().__init__(master, **kwargs)
        self.data_manager = data_manager
        self.stats = StatEngine(self.data_manager)
        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure((0, 1), weight=1)

        # Remove any existing children before building
        for w in self.winfo_children():
            w.destroy()

        self.create_header()

        # Sections
        self.create_section("📈 Résumés & Interprétations", 1)
        self.create_smart_stats(2)

        self.create_section("🌍 Démographie", 3)
        self.create_demo_charts(4)

        self.create_section("🧠 Analyse Croisée (Région vs Segment)", 5)
        self.create_advanced_charts(6)

    def refresh(self):
        """Public: rebuild the analytics UI to reflect current DB state."""
        # Recreate StatEngine to pick up new data source
        self.stats = StatEngine(self.data_manager)
        self.build_ui()

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        
        # Colonne Titre
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="Analyses Approfondies", font=("Roboto Medium", 26), text_color="#1C1C1E").pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Exploration statistique et corrélation des données.", text_color="#8E8E93").pack(anchor="w")

        # Colonne Bouton Rapport 
        self.btn_report = ctk.CTkButton(header, text="📄 Générer Rapport Financier", 
                                        fg_color="#34C759", hover_color="#2E7D32", 
                                        height=40, font=("Roboto Medium", 14),
                                        command=self.action_generate_report)
        self.btn_report.pack(side="right", padx=10)

    def action_generate_report(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", 
                                                filetypes=[("Excel Workbook", "*.xlsx")],
                                                initialfile="Rapport_Financier_2026.xlsx")
        if filename:
            success = self.stats.generate_excel_report(filename)
            if success:
                messagebox.showinfo("Rapport Généré", "Le rapport financier complet a été généré avec succès.\nIl contient 3 onglets d'analyse.")
            else:
                messagebox.showerror("Erreur", "Impossible de générer le rapport (Vérifiez que le fichier n'est pas déjà ouvert).")

    def create_section(self, title, row):
        lbl = ctk.CTkLabel(self, text=title, font=("Roboto Medium", 18), text_color="#0A84FF")
        lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(30, 10))
        ctk.CTkFrame(self, height=2, fg_color="#E5E5EA").grid(row=row, column=0, columnspan=2, sticky="ew", padx=20)

    def create_smart_stats(self, row):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10)
        frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Récupération données via Pandas (StatEngine)
        df = self.stats.get_dataframe()
        if df.empty: return

        # Calculs
        avg_score = df['score'].mean() if 'score' in df else 0
        var_score = df['score'].var() if 'score' in df else 0
        med_age = df['age'].median() if 'age' in df else 0

        # Cartes
        self.add_stat_card(frame, 0, "Score Moyen", f"{avg_score:.1f}", 
                           "Performance correcte" if avg_score > 500 else "Performance faible", "#0A84FF")
        self.add_stat_card(frame, 1, "Variance Score", f"{var_score:.0f}", 
                           "Forte disparité" if var_score > 15000 else "Clientèle homogène", "#FF9500")
        self.add_stat_card(frame, 2, "Âge Médian", f"{med_age:.0f} ans", 
                           "Cœur de cible jeune" if med_age < 35 else "Clientèle mature", "#34C759")

    def add_stat_card(self, parent, col, title, value, insight, color):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#E5E5EA")
        card.grid(row=0, column=col, sticky="nsew", padx=10)
        
        ctk.CTkLabel(card, text=title.upper(), font=("Roboto", 11, "bold"), text_color=color).pack(anchor="w", padx=15, pady=(15,5))
        ctk.CTkLabel(card, text=value, font=("Roboto Medium", 28), text_color="#1C1C1E").pack(anchor="w", padx=15)
        
        # Bulle Insight
        box = ctk.CTkFrame(card, fg_color="#F5F5F5", corner_radius=6)
        box.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(box, text=f"💡 {insight}", font=("Roboto", 11), text_color="#1C1C1E").pack(padx=10, pady=5, anchor="w")

    def create_demo_charts(self, row):
        # Sexe (Pie)
        f1 = self.create_chart_frame(row, 0, "Répartition Sexe")
        labels, sizes = self.stats.get_segment_dist() # Utilise get_segment_dist qui gère sexe/segment
        
        fig, ax = plt.subplots(figsize=(5, 3.5), dpi=100)
        self.setup_fig(fig, ax)
        if sizes:
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#0A84FF', '#FF3B30'], 
                   textprops={'color':"#1C1C1E"}, startangle=90)
        self.embed(fig, f1)

        # Région (Bar)
        f2 = self.create_chart_frame(row, 1, "Répartition Région")
        df = self.stats.get_dataframe()
        if not df.empty and 'region' in df:
            counts = df['region'].value_counts()
            fig, ax = plt.subplots(figsize=(5, 3.5), dpi=100)
            self.setup_fig(fig, ax)
            ax.bar(counts.index, counts.values, color="#34C759")
            plt.xticks(rotation=15, fontsize=8)
            self.embed(fig, f2)

    def create_advanced_charts(self, row):
        # Heatmap (Tableau croisé)
        f1 = self.create_chart_frame(row, 0, "Heatmap (Région vs Segment)")
        df = self.stats.get_dataframe()
        
        if not df.empty and 'region' in df and 'segment' in df:
            ct = pd.crosstab(df['region'], df['segment'])
            fig, ax = plt.subplots(figsize=(5, 3.5), dpi=100)
            self.setup_fig(fig, ax)
            ax.grid(False) # Pas de grille sur heatmap
            
            im = ax.imshow(ct.values, cmap="viridis", aspect='auto')
            
            # Labels axes
            ax.set_xticks(np.arange(len(ct.columns)))
            ax.set_yticks(np.arange(len(ct.index)))
            ax.set_xticklabels(ct.columns, color="#1C1C1E", fontsize=8)
            ax.set_yticklabels(ct.index, color="#1C1C1E", fontsize=8)
            
            # Annotations
            for i in range(len(ct.index)):
                for j in range(len(ct.columns)):
                    ax.text(j, i, ct.values[i, j], ha="center", va="center", color="white", fontweight="bold")
            
            self.embed(fig, f1)

        # Histogramme Ancienneté
        f2 = self.create_chart_frame(row, 1, "Fidélité (Ancienneté)")
        if not df.empty and 'anciennete' in df:
            fig, ax = plt.subplots(figsize=(5, 3.5), dpi=100)
            self.setup_fig(fig, ax)
            ax.hist(df['anciennete'], bins=10, color="#FF9500", alpha=0.8)
            ax.set_xlabel("Années d'ancienneté", color="#8E8E93")
            self.embed(fig, f2)

    # --- Utils ---
    def create_chart_frame(self, row, col, title):
        frame = ctk.CTkFrame(self, fg_color="#FFFFFF", border_width=1, border_color="#E5E5EA")
        frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(frame, text=title, font=("Roboto Medium", 13), text_color="#1C1C1E").pack(anchor="w", padx=15, pady=10)
        return frame

    def setup_fig(self, fig, ax):
        bg = "#FFFFFF"
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        for s in ax.spines.values(): s.set_visible(False)
        ax.tick_params(colors="#8E8E93")

    def embed(self, fig, parent):
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

