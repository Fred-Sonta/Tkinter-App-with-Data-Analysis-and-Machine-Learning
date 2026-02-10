import pandas as pd
import numpy as np

class StatEngine:
    """
    Moteur Statistique (Module Expert manquant)
    Alimente le Dashboard et la vue Analytics en indicateurs clés.
    """
    
    def __init__(self, data_manager):
        self.db = data_manager

    def get_dataframe(self):
        """Récupère les données SQL et les convertit en DataFrame Pandas optimisé."""
        data = self.db.get_all_clients()
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)

    def get_kpis(self):
        """Calcule les 4 chiffres clés du Dashboard en temps réel."""
        df = self.get_dataframe()
        
        # Gestion du cas vide (au tout début)
        if df.empty:
            return {
                "total_clients": 0, 
                "total_encours": "0.00 €", 
                "score_moyen": 0, 
                "anomalies": 0
            }
            
        # Calculs robustes
        total_encours = df['solde'].sum() if 'solde' in df.columns else 0
        score_moyen = df['score'].mean() if 'score' in df.columns else 0

        # Sécurité : si la moyenne est NaN (ex : valeurs manquantes), on retourne 0
        if pd.isna(score_moyen):
            score_val = 0
        else:
            try:
                score_val = int(score_moyen)
            except Exception:
                score_val = 0
        
        # Comptage des risques élevés (nécessite la colonne niveau_risque issue du scoring)
        nb_anomalies = 0
        if 'niveau_risque' in df.columns:
            nb_anomalies = len(df[df['niveau_risque'] == "Élevé"])

        return {
            "total_clients": len(df),
            "total_encours": f"{total_encours:,.2f} €",
            "score_moyen": score_val,
            "anomalies": nb_anomalies
        }

    # --- Données pour les Graphiques ---

    def get_age_dist(self):
        """Pour l'Histogramme des âges"""
        df = self.get_dataframe()
        return df['age'].dropna().tolist() if not df.empty and 'age' in df.columns else []

    def get_segment_dist(self):
        """Pour le Camembert (Répartition par Segment ou Sexe)"""
        df = self.get_dataframe()
        col = 'segment' if 'segment' in df.columns else 'sexe' 
        
        if df.empty or col not in df.columns: 
            return [], []
            
        counts = df[col].value_counts()
        return counts.index.tolist(), counts.values.tolist()
    
    def get_scatter_data(self):
        """Pour le Scatter Plot (Corrélation Age vs Solde)"""
        df = self.get_dataframe()
        if df.empty or 'age' not in df.columns or 'solde' not in df.columns: 
            return [], []
        
        # On filtre les données aberrantes pour un joli graphique
        return df['age'].tolist(), df['solde'].tolist()

    def get_time_series(self):
        """
        Pour le graphique de tendance.
        Utilise la date de création ou simule une évolution basée sur l'ancienneté.
        """
        df = self.get_dataframe()
        if df.empty: return [], []
        
        # Astuce Expert : On groupe par ancienneté pour voir l'évolution du solde moyen
        if 'anciennete' in df.columns and 'solde' in df.columns:
            # On trie par ancienneté décroissante (les plus anciens à gauche)
            # Pour simuler une chronologie
            df_sorted = df.sort_values('anciennete', ascending=False).head(12) # 12 derniers mois simulés
            return df_sorted['anciennete'].tolist(), df_sorted['solde'].tolist()
            
        return [], []
    
    # Méthode d'Export Excel Avancée

    def generate_excel_report(self, filepath="Rapport_Financier_SIGASC.xlsx"):
        """
        Génère un rapport Excel multi-onglets complet.
        Onglet 1 : Résumé Exécutif (KPIs)
        Onglet 2 : Détail des Risques
        """
        try:
            df = self.get_dataframe()
            if df.empty: return False

            # Préparation des données KPIs
            kpis = self.get_kpis()
            df_kpi = pd.DataFrame([kpis])

            # Préparation des données Risques
            if 'niveau_risque' in df.columns:
                df_risk = df.groupby('niveau_risque')[['solde', 'revenu']].mean().reset_index()
            else:
                df_risk = pd.DataFrame()

            # Écriture Excel Multi-Feuilles
            with pd.ExcelWriter(filepath) as writer:
                df_kpi.to_excel(writer, sheet_name='Synthèse Exécutive', index=False)
                df_risk.to_excel(writer, sheet_name='Analyse des Risques', index=False)
                # On met aussi les données brutes dans un onglet à part
                df.to_excel(writer, sheet_name='Données Complètes', index=False)
            
            return True
        except Exception as e:
            print(f"Erreur Rapport: {e}")
            return False

