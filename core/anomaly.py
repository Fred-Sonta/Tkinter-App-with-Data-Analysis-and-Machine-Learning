import numpy as np
import pandas as pd
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False # Si sklearn non installé

class AnomalyDetector:
    """
    Module ML de Détection d'Anomalies (Fonctionnalité F).
    Utilise l'algorithme Isolation Forest (Apprentissage non supervisé).
    """

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False

    def train_model(self, clients_data):
        """
        Entraîne le modèle sur l'ensemble des données actuelles.
        """
        if not SKLEARN_AVAILABLE or not clients_data:
            return

        # Conversion en DataFrame
        df = pd.DataFrame(clients_data)
        
        # Sélection des features numériques pertinentes pour la fraude
        features = ['solde', 'age', 'revenu', 'score']
        # On ne garde que les colonnes qui existent vraiment
        available_features = [f for f in features if f in df.columns]
        
        if len(available_features) < 2:
            return 
        # Préparation des données (Gestion des NaN par 0)
        X = df[available_features].fillna(0)
        
        # Normalisation (Important pour l'Isolation Forest)
        X_scaled = self.scaler.fit_transform(X)
        
        # Initialisation et Entraînement
        # contamination=0.05 signifie qu'on estime qu'il y a 5% d'anomalies max
        self.model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        self.model.fit(X_scaled)
        
        self.is_trained = True
        self.features_used = available_features # On mémorise les colonnes utilisées

    def predict_risk(self, client):
        """
        Analyse un client spécifique.
        Retourne : (Est_Anomalie (bool), Score_Anomalie (float))
        """
        # --- MODE DÉGRADÉ (Si pas d'IA ou pas assez de données) ---
        if not self.is_trained:
            # Règles manuelles basiques
            score = 0
            if client.get('solde', 0) < 0: score -= 1
            if client.get('age', 30) > 100: score -= 1
            if client.get('score', 500) < 300: score -= 1
            return (score < -1, score)

        # --- MODE Machine Learning ---
        try:
            # On reconstruit le vecteur du client avec les mêmes colonnes que l'entraînement
            vector = []
            for feat in self.features_used:
                val = client.get(feat, 0)
                # Sécurité si la valeur est None
                vector.append(val if val is not None else 0)
            
            X_client = np.array([vector])
            X_scaled = self.scaler.transform(X_client)
            
            # Prédiction : -1 = Anomalie, 1 = Normal
            pred = self.model.predict(X_scaled)[0]
            # Score de décision (plus c'est bas, plus c'est anormal)
            decision_score = self.model.decision_function(X_scaled)[0]
            
            return (pred == -1, decision_score)
            
        except Exception as e:
            print(f"Erreur Prédiction IA: {e}")
            return (False, 0)
        
