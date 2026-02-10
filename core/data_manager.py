import sqlite3
import csv
import pandas as pd # Ajout pour l'import massif optimisé

class DataManager:
    """
    Couche DONNÉES : Gère la base SQLite.
    """

    def __init__(self, db_name="clients.db"):
        self.db_name = db_name
        self.creer_tables()

    def connect(self):
        """Établit la connexion avec la BDD et active les clés étrangères."""
        conn = sqlite3.connect(self.db_name)
        # CRITIQUE : Permet d'accéder aux colonnes par leur nom (ex: row['nom'])
        # Indispensable pour l'interface graphique moderne.
        conn.row_factory = sqlite3.Row  
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def creer_tables(self):
        """Création de la structure BDD selon le PDF."""
        conn = self.connect()
        cur = conn.cursor()
        
        # 1. Table Clients
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
                id_client INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                age INTEGER,
                sexe TEXT,
                solde REAL,
                region TEXT,
                anciennete INTEGER,
                segment TEXT DEFAULT 'Standard',
                revenu REAL DEFAULT 0,
                score_initial REAL DEFAULT 500,
                date_creation DATE DEFAULT CURRENT_DATE
        )""")

        # 2. Table Scoring (Lien avec le module du Membre 2)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS scoring (
                id_score INTEGER PRIMARY KEY AUTOINCREMENT,
                id_client INTEGER,
                score_final REAL,
                niveau_risque TEXT,
                date_calcul DATE,
                FOREIGN KEY(id_client) REFERENCES clients(id_client) ON DELETE CASCADE
        )""")
        
        # 3. Table Transactions (Optionnelle dans le PDF mais requise pour ton IA)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
                id_trans INTEGER PRIMARY KEY AUTOINCREMENT,
                id_client INTEGER,
                montant REAL,
                date_trans DATE,
                FOREIGN KEY(id_client) REFERENCES clients(id_client) ON DELETE CASCADE
        )""")
        
        conn.commit()
        conn.close()

    # --- CRUD (Create, Read, Update, Delete) ---

    def get_all_clients(self):
        """Récupère tous les clients avec leur score associé (Jointure)."""
        conn = self.connect()
        # On fait un LEFT JOIN pour avoir le client même s'il n'a pas encore de score calculé
        query = """
        SELECT c.*, s.score_final as score, s.niveau_risque 
        FROM clients c 
        LEFT JOIN scoring s ON c.id_client = s.id_client
        ORDER BY c.id_client DESC
        """
        # Conversion explicite en liste de dictionnaires pour le GUI
        clients = [dict(row) for row in conn.execute(query).fetchall()]
        conn.close()
        return clients

    def filtrer_clients(self, region=None, risque=None, recherche=None):
        """
        Fonction de recherche avancée pour l'interface graphique.
        Remplace les fonctions 'clients_par_region' séparées.
        """
        conn = self.connect()
        query = """
        SELECT c.*, s.score_final as score, s.niveau_risque 
        FROM clients c 
        LEFT JOIN scoring s ON c.id_client = s.id_client
        WHERE 1=1
        """
        params = []
        
        if region and region != "Toutes":
            query += " AND c.region = ?"
            params.append(region)
        
        if risque and risque != "Tous":
            query += " AND s.niveau_risque = ?"
            params.append(risque)
            
        if recherche:
            query += " AND LOWER(c.nom) LIKE ?"
            params.append(f"%{recherche.lower()}%")

        clients = [dict(row) for row in conn.execute(query, params).fetchall()]
        conn.close()
        return clients

    def add_client(self, data):
        """Ajoute un client via un dictionnaire (depuis le formulaire GUI)."""
        conn = self.connect()
        try:
            conn.execute("""
                INSERT INTO clients (nom, age, region, revenu, segment, solde, sexe, anciennete)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (data['nom'], data['age'], data.get('region'), data.get('revenu', 0), 
                  data.get('segment', 'Standard'), data.get('solde', 0), 
                  data.get('sexe', 'M'), data.get('anciennete', 0)))
            conn.commit()
        except Exception as e:
            print(f"Erreur SQL lors de l'ajout: {e}")
        finally:
            conn.close()

    def update_client(self, id_client, data):
        """Met à jour un client dynamiquement."""
        conn = self.connect()
        # Construction dynamique de la requête SQL (Set nom=?, age=?...)
        fields = ", ".join([f"{k}=?" for k in data.keys()])
        values = list(data.values())
        values.append(id_client)
        
        try:
            conn.execute(f"UPDATE clients SET {fields} WHERE id_client=?", values)
            conn.commit()
        except Exception as e:
            print(f"Erreur SQL lors de la mise à jour: {e}")
        finally:
            conn.close()

    def delete_client(self, id_client):
        """Supprime un client (cascade sur score et transactions)."""
        conn = self.connect()
        conn.execute("DELETE FROM clients WHERE id_client=?", (id_client,))
        conn.commit()
        conn.close()
        
    # --- IMPORT / EXPORT (Gestion de fichiers) ---

    def import_dataframe(self, df):
        """
        Import optimisé pour le module de nettoyage (DataCleaner).
        Utilise Pandas pour insérer en masse au lieu de faire 1000 INSERT.
        """
        conn = self.connect()
        try:
            # if_exists='append' : ajoute à la suite sans supprimer l'existant
            df.to_sql('clients', conn, if_exists='append', index=False)
            conn.commit()
        except Exception as e:
            print(f"Erreur lors de l'import Pandas: {e}")
        finally:
            conn.close()

    def exporter_csv(self, filepath="export_clients.csv"):
        """Export simple pour l'utilisateur."""
        clients = self.get_all_clients()
        if not clients:
            return
            
        keys = clients[0].keys()
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(clients)

    # Fonction d'Export CSV Amélioré

    def export_data_to_csv(self, data_list, filename="export_clients.csv"):
        """
        Export Expert : Prend une liste de données (filtrées ou non) 
        et génère un CSV propre avec encodage UTF-8 (compatible Excel).
        """
        if not data_list:
            return False
            
        try:
            # Conversion en Pandas DataFrame pour un export robuste
            df = pd.DataFrame(data_list)
            
            # Renommage des colonnes pour une meilleure lisibilité
            mapping = {
                "id_client": "ID", "nom": "Nom Complet", "age": "Âge", 
                "region": "Région", "solde": "Solde (€)", 
                "score": "Score Crédit", "niveau_risque": "Risque"
            }
            df = df.rename(columns=mapping)
            
            # Export
            df.to_csv(filename, index=False, sep=';', encoding='utf-8-sig') # sep=';' pour Excel FR
            return True
        except Exception as e:
            print(f"Erreur Export: {e}")
            return False        

    def clear_all(self):
        """
        Supprime toutes les données des tables (utilisé pour recharger une nouvelle dataset).
        Cette méthode supprime explicitement les enregistrements puis exécute VACUUM.
        """
        conn = self.connect()
        cur = conn.cursor()
        try:
            # Suppression explicite. ON DELETE CASCADE gère les dépendances.
            cur.execute("DELETE FROM scoring")
            cur.execute("DELETE FROM transactions")
            cur.execute("DELETE FROM clients")
            conn.commit()
            cur.execute("VACUUM")
            conn.commit()
        except Exception as e:
            print(f"Erreur lors du vidage de la BDD: {e}")
        finally:
            conn.close()

    # --- GESTION DES TRANSACTIONS  ---

    def get_all_transactions(self, search_query=None):
        """
        Récupère l'historique complet avec le NOM du client (Jointure).
        Trié par date décroissante (le plus récent en haut).
        """
        conn = self.connect()
        query = """
            SELECT t.id_trans, t.montant, t.date_trans, c.nom, c.id_client
            FROM transactions t
            JOIN clients c ON t.id_client = c.id_client
            WHERE 1=1
        """
        params = []
        
        if search_query:
            query += " AND LOWER(c.nom) LIKE ?"
            params.append(f"%{search_query.lower()}%")
            
        query += " ORDER BY t.date_trans DESC, t.id_trans DESC"
        
        txs = [dict(row) for row in conn.execute(query, params).fetchall()]
        conn.close()
        return txs

    def add_transaction(self, id_client, montant, date_trans):
        """
        Ajoute une transaction ET met à jour le solde du client (Trigger logiciel).
        """
        conn = self.connect()
        try:
            # 1. Enregistrer la transaction
            conn.execute("""
                INSERT INTO transactions (id_client, montant, date_trans)
                VALUES (?, ?, ?)
            """, (id_client, montant, date_trans))
            
            # 2. Mettre à jour le solde du client (Cohérence des données)
            # Solde = Solde Actuel + Montant (Si montant négatif, le solde baisse)
            conn.execute("""
                UPDATE clients 
                SET solde = solde + ? 
                WHERE id_client = ?
            """, (montant, id_client))
            
            conn.commit()
            print(f"Transaction de {montant}€ enregistrée pour client {id_client}.")
        except Exception as e:
            print(f"Erreur Transaction: {e}")
            conn.rollback() # Annule tout si erreur
        finally:
            conn.close()