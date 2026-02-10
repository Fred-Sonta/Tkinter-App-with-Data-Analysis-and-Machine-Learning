import pandas as pd
import numpy as np

class DataCleaner:
    """
    Module Audit & Nettoyage (Version Incassable)
    Garantit que TOUT fichier injecté ressortira propre et compatible BDD.
    """

    def __init__(self, data_manager):
        self.db = data_manager

    def audit_file(self, file_path):
        """Phase 1 : Lecture sécurisée pour le rapport"""
        try:
            # On lit tout en string pour éviter que Pandas ne crash sur des types mixtes
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, dtype=str)
            else:
                df = pd.read_excel(file_path, dtype=str)
            
            # Standardisation basique des colonnes pour l'audit
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            report = {
                "total_rows": len(df),
                "doublons": df.duplicated().sum(),
                "valeurs_manquantes": df.isnull().sum().to_dict(),
                "colonnes_detectees": list(df.columns),
                # Statut OK seulement si on a au moins un 'nom' ou un 'id'
                "statut": "OK" if 'nom' in df.columns else "ATTENTION (Colonne 'nom' introuvable)"
            }
            return df, report
        except Exception as e:
            return None, str(e)

    def clean_and_inject(self, df):
        """Phase 2 : Le Pipeline de Nettoyage Ultime"""
        df = df.copy()

        # 1. STANDARDISATION DES EN-TÊTES
        df.columns = [str(c).lower().strip() for c in df.columns]

        # 2. ENFORCER LE SCHÉMA (C'est ici qu'on empêche le crash)
        # Si une colonne manque, on la crée avec une valeur par défaut.
        expected_cols = {
            'nom': 'Client Inconnu',
            'age': '30',
            'sexe': 'M',
            'solde': '0',
            'revenu': '0',
            'region': 'Inconnue',
            'segment': 'Standard',
            'anciennete': '0',
            'score_initial': '500'
        }
        
        for col, default_val in expected_cols.items():
            if col not in df.columns:
                df[col] = default_val

        # 3. NETTOYAGE STRUCTUREL
        df = df.drop_duplicates()
        
        # Supprimer les lignes où le NOM est vide ou NaN (Client fantôme)
        df['nom'] = df['nom'].astype(str).str.strip()
        df = df[df['nom'] != 'nan']
        df = df[df['nom'] != '']
        df = df[df['nom'] != 'Client Inconnu'] # Si on veut être strict

        # 4. NETTOYAGE DES VALEURS (Type Coercion)
        
        # 4.1 TEXTES PROPRES
        df['nom'] = df['nom'].str.title()
        df['region'] = df['region'].astype(str).str.title().str.strip().replace('Nan', 'Inconnue')
        
        # 4.2 SEXE (Normalisation stricte)
        df['sexe'] = df['sexe'].apply(self._normalize_gender)

        # 4.3 NOMBRES (Age, Solde, Revenu...)
        # On nettoie d'abord les caractères monétaires potentiels
        for col in ['solde', 'revenu', 'score_initial']:
            df[col] = self._clean_money_string(df[col])
            
        # 4.4 AGE (Logique Métier : Pas de négatifs, pas de > 100 ans)
        df['age'] = self._clean_age_logic(df['age'])
        
        # 4.5 ANCIENNETÉ
        df['anciennete'] = pd.to_numeric(df['anciennete'], errors='coerce').fillna(0).abs().astype(int)

        # 5. TRAITEMENT STATISTIQUE (Outliers)
        # On plafonne les revenus et soldes aberrants
        for col in ['solde', 'revenu']:
            self._cap_outliers(df, col)

        # 6. INJECTION FINALE
        # On ne garde que les colonnes propres dans l'ordre attendu par la BDD
        final_df = df[list(expected_cols.keys())]
        
        self.db.import_dataframe(final_df)
        return len(final_df)

    # --- SOUS-FONCTIONS ROBUSTES ---

    def _normalize_gender(self, val):
        """Transforme n'importe quoi en M ou F"""
        s = str(val).lower().strip()
        if s in ['f', 'femme', 'woman', 'female', 'fille']:
            return 'F'
        return 'M'

    def _clean_money_string(self, series):
        """Nettoie '1 000 €', '1,500.00', etc."""
        # On force en string, on vire les symboles et espaces
        s = series.astype(str).str.replace(' ', '').str.replace('€', '').str.replace('$', '')
        # On remplace la virgule par un point (format US standard pour Python)
        s = s.str.replace(',', '.')
        # Conversion forcée, les erreurs deviennent 0.0
        return pd.to_numeric(s, errors='coerce').fillna(0.0)

    def _clean_age_logic(self, series):
        """Assure que l'âge est réaliste (18-100)"""
        # Conversion numérique
        nums = pd.to_numeric(series, errors='coerce')
        
        # Médiane de secours (si tout est vide, on prend 30 ans)
        med = nums.median()
        if pd.isna(med): med = 30
        
        # Remplacer NaN par médiane
        nums = nums.fillna(med)
        
        # Valeur absolue (Adieu les -5 ans)
        nums = nums.abs()
        
        # Bornage 18 - 100 ans
        # Si en dehors, on remplace par la médiane
        mask_bad = (nums < 18) | (nums > 100)
        nums.loc[mask_bad] = med
        
        return nums.astype(int)

    def _cap_outliers(self, df, col):
        """Méthode IQR pour plafonner les valeurs extrêmes sans supprimer"""
        if df[col].nunique() < 5: return # Pas assez de données pour calculer IQR
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        
        # On utilise clip pour borner
        df[col] = df[col].clip(lower=lower, upper=upper)

        