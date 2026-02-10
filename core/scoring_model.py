import math
from datetime import datetime

class ScoringModel:
    """
    Module de Scoring (Version Expert)
    Calcule le Risque Client et met à jour la table 'scoring'.
    """

    def __init__(self, data_manager):
        self.db = data_manager
        
        # Paramètres du modèle (Code original Zanira)
        self.coef_age = 0.4
        self.coef_solde = 0.6
        self.coef_anciennete = 1.2
        self.age_ref = 60

    def calculate_all_scores(self):
        """
        Fonction principale appelée par le Dashboard.
        Récupère tous les clients, recalcule les scores et met à jour la BDD.
        """
        clients = self.db.get_all_clients()
        conn = self.db.connect()
        cursor = conn.cursor()
        
        count = 0
        for client in clients:
            # 1. Calcul mathématique
            score = self.compute_score(client)
            risk = self.classify_risk(score)
            
            # 2. Mise à jour BDD (Table 'scoring')
            # On vérifie d'abord si un score existe déjà pour ce client
            cursor.execute("SELECT id_score FROM scoring WHERE id_client = ?", (client['id_client'],))
            exists = cursor.fetchone()
            
            if exists:
                # Mise à jour
                cursor.execute("""
                    UPDATE scoring 
                    SET score_final = ?, niveau_risque = ?, date_calcul = CURRENT_DATE
                    WHERE id_client = ?
                """, (score, risk, client['id_client']))
            else:
                # Insertion
                cursor.execute("""
                    INSERT INTO scoring (id_client, score_final, niveau_risque, date_calcul)
                    VALUES (?, ?, ?, CURRENT_DATE)
                """, (client['id_client'], score, risk))
            
            count += 1
            
        conn.commit()
        conn.close()
        return count

    def compute_score(self, client):
        """Logique métier du score (Adaptée pour utiliser les dictionnaires)"""
        # Récupération sécurisée des valeurs (avec valeurs par défaut si NULL)
        score_initial = client['score_initial'] if client['score_initial'] else 500
        age = client['age'] if client['age'] else 30
        solde = client['solde'] if client['solde'] else 0
        anciennete = client['anciennete'] if client['anciennete'] else 0

        # Formule Membre 2
        points_age = self.coef_age * (self.age_ref - age)
        # Protection log math domain error si solde <= -1
        val_solde = max(solde, 0) 
        points_solde = self.coef_solde * math.log(1 + val_solde)
        points_anciennete = self.coef_anciennete * anciennete

        score = score_initial + points_age + points_solde + points_anciennete
        
        # Bornage entre 0 et 1000 (Standard Scoring type FICO)
        return max(0, min(1000, int(score)))

    def classify_risk(self, score):
        """Classification selon le PDF"""
        # Échelle inversée standard : Score haut = Risque faible
        if score >= 750:
            return "Faible"
        elif score >= 500:
            return "Moyen"
        else:
            return "Élevé"
        

