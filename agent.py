from together import Together
from langchain_community.utilities import SQLDatabase
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import mysql.connector
from typing import List, Dict
import tiktoken 
import json
from pathlib import Path
from datetime import datetime

load_dotenv()

concise_domain_descriptions = {
    "ELEVES_INSCRIPTIONS": "Ce domaine couvre des informations complètes sur les **élèves** (informations biographiques, photos, données médicales), leur **inscription** (statut, classe, année scolaire, modalités financières), les détails de la **pré-inscription** (archives, journaux, documents associés), les nationalités, les situations familiales et les données d'intégration avec des systèmes externes (par exemple, Teams pour les élèves).",
    "SUIVI_SCOLARITE": "Ce domaine assure le suivi des **performances et du comportement scolaire des élèves**. Il inclut les notes, les moyennes, les absences, les retards, les blâmes, les avertissements, les décisions des conseils de classe, les dossiers scolaires et les données statistiques. Il couvre également les justifications d'absence, les notifications SMS et les pièces jointes des devoirs.",
    "PARENTS": "Ce domaine détaille les informations sur les **parents** (profession, adresse, contact) et leurs **relations** avec les élèves. Il inclut les données historiques et archivées.",
    "CANTINE": "Ce domaine gère les **services de cantine** et les enregistrements, plannings et paiements associés pour les élèves et le personnel. Il inclut la gestion des menus et le suivi des règlements.",
    "PERSONNEL_ENSEIGNEMENT": "Ce domaine contient des informations détaillées sur le **personnel académique** (enseignants, surveillants), incluant les détails biographiques, les coordonnées, la situation familiale, les qualifications, les taux horaires, les disponibilités, les matières enseignées, les emplois du temps, les paiements du personnel et l'intégration Teams.",
    "FINANCES_PAIEMENTS": "Ce domaine assure la gestion complète des **paiements** (frais de scolarité, frais supplémentaires, cours d'été), des **règlements** (chèques, échéanciers), des relevés bancaires, des détails des tranches, des remises, des méthodes de paiement et des paiements aux fournisseurs. Il inclut également la gestion de la caisse et des transactions bancaires.",
    "EMPLOIS_DU_TEMPS": "Ce domaine gère les **emplois du temps des cours et des examens**, la répartition des devoirs, l'attribution des salles et les périodes académiques (trimestres, semaines, jours).",
    "GENERAL_ADMINISTRATION_CONFIG": "Ce domaine couvre les **informations administratives générales et de configuration**. Cela inclut les détails sur l'**établissement** (types, emplacement), les configurations système, les données géographiques (gouvernorats, délégations, DRE), la **gestion des personnes** (informations de base communes à tous les individus), la **gestion des utilisateurs** (rôles, privilèges, accès), les actualités, les notifications, les plaintes, les suggestions et les journaux de téléchargement."
}

domain_to_tables_mapping = {
    "ELEVES_INSCRIPTIONS": [
        "eleveinscri", "getallelevefordescipline", "geteleveinscrisansreglement",
        "pbiviewinscritscolaire", "teamstudentenrollementview", "vieweleveparclasse", "viewelevereinscri",
        "viewgeteleveinscri", "viewgeteleveinscridup", "viewnouveaueleve", "viewtouslesinscri",
        "documentelevepreinscri", "edueleve", "eduinscription", "eleve_archive", "elevepreinscription",
        "elevepreinscriptionlog", "nationalite", "preinscription_archive", "preinscriptionlog",
        "situationfamilliale", "representantlegal", "stagiaires_int", "teamsstudent", "teamsstudentenrollement",
        "teamspasswordstudent", "eleve", "fichierpreinscriptionpreinscription", "inscriptioneleve",
        "personnepreinscription", "preinscription", "preinscriptionpreinscription", "renseignementmedicaux","personne"
    ],
    "SUIVI_SCOLARITE": [
        #"viewabsence", "viewavertissement", "viewblame", "viewgetblame", "viewgetretard",
        #"viewgetretards", "viewretard", "viewstatmoyenneglobal",
        "dossierscolaire", "eduattestation","edumoymati", "edumoymaticopie", "edumoymatisave", "edunoteelev", "decision", "discipline",
        "eduperiexam", "eduprix", "eduresultat", "eduresultatcopie", "eduresultatcopie11", "edutypeepre","noteeleveview", 
        "justificationeleve", "logsms", "noteseleve", "noteeleveparmatiere", "piecejoint", "retard",
        "statarithconcours", "statconcoursglobal", "suivihomework", "absence", "avertissement", "blame"
    ],
    "PARENTS": [
        "parenteleveannee4", "viewgeteleveparent", "viewgeteleveparentdup", "viewgetparent",
        "parent_archive", "parent_ise", "parenteleve_archive", "parentelevepreinscription",
        "personne_archive", "personnepreinscriptionlog", "parent", "parenteleve","personne"
    ],
    "CANTINE": [
        #"viewcantineparjour", "viewcantineparjourenseignant","viewetatcantineparjour",
         "cantine", "menu_cantine", "menu_cantine_jour", "suivicantineparjour",
        "cantineparjour", "cantineparjourenseignant","nvetatcantineparjourglobale",
    ],
    "PERSONNEL_ENSEIGNEMENT": [
        #"viewenseignant", "viewgetmatiereclasseenseignant", "viewmatiereenseignant","viewrepartitionenseignant", "viewrepartitionsurveillant",
        "educycleens", "edumatiere","teamsteacherrostarview",
        "enseignant_double", "enseignant_motif", "enseignant_paiement", "enseignants_presence", "grade",
        "matiere", "naturematiere", "matiereexamenbloque", "matieresection", "qualite", "personnesupp",
        "teamsteacher", "teamsteacherrostar", "teamspasswordteacher", "disponibiliteenseignant",
        "enseigantmatiere", "enseingant", "surveillant","personne"
    ],
    "FINANCES_PAIEMENTS": [
        #"viewetatdepaiementuniform", "viewextras", "viewgetclub", "viewgetpaiementextra",
        #"viewgetpaiementscolaire", "viewgetpaiementscolairedetaillee", "viewrchequeecheancier",
        #"viewreglementecheanciernonvalide", "viewtranchepaiement", "viewuniformcommande",
        "caissemotif", "configuration", "infosfornisseur", "inscriptionelevecourete", "modalite", "banquebordereau",
        "modalitepaiement", "modereglement", "paiementcourete", "paiementmotif", "reglementfornisseur",
        "situationeleve", "banque", "banquebordereaudetails", "banqueversement", "caisse", "caisse_log",
        "caissedetails", "uniformcommande", "modalitetranche", "paiement", "paiementdetailscourete",
        "paiementextra", "paiementextradetails", "reglementeleve", "reglementeleve_echeancier",
        "uniformcommandedetails", "uniformmodel"
    ],
    "EMPLOIS_DU_TEMPS": [
        #"viewemploi", "viewemploi_enligne", "viewemploiexameneleve", 
        "groupe", "groupecourete","homeworkclasse", "jour", "periodeexamen", "matiere", "repartitionexamen", "repartitionexamencopie",
        "repartitionsemaine", "salle", "seance", "sectioncourete", "semaine", "trimestre", "typepre", "jourfr"
    ],
    "GENERAL_ADMINISTRATION_CONFIG": [
        #"viewcasiervide", "viewgetinscicasier", "viewstatistiquelocalite",
        "actualite1", "actualites","anneescolaire", "civilite", "codepostal", "configaffichage", "configmatiereclsstat",
        "configmatierenivstat", "diplome", "dre", "educlasse", "edusection", "eduniveau", "gouvernorat",
        "localite", "extracasier", "extraclub", "extravaucher", "motifdoc", "motifsms", "motiftelechargement",
        "notifications", "notificationcompagne", "pays", "niveau", "privilege", "reclamation", "rubrique",
        "smscampagnes", "smslog", "suggestion", "telechargement", "test", "test2", "tokenfirebases",
        "typeetablissement", "typemessagerie", "typesms", "uniformcouleur", "uniformgenre",
        "uniformtaille", "user", "useradmin", "utilisateur", "actionfonctionalitepriv", "classe",
        "delegation", "dre", "etablissement", "fonctionaliteprivelge", "personne", "section", "utilisateur"
    ]
}


mysql_config = {
    'host': os.getenv('MYSQL_HOST'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

# Test de connexion
try:
    conn = mysql.connector.connect(**mysql_config)
    print("✅ Connexion MySQL réussie.")
    conn.close()
except Exception as e:
    print(f"❌ ERREUR de connexion MySQL: {e}")
    exit(1)

# === Prompt Template ===
PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["input", "table_info", "relevant_domain_descriptions", "relations"],
    template=f"""
[SYSTEM] Vous êtes un assistant SQL expert pour une base de données scolaire.
Votre rôle est de traduire des questions en français en requêtes SQL MySQL.

ATTENTION: 
1.la trimestre 3 est d id 33, trimestre 2 est d id 32 , trimestre 1 est d id 31.
2. lorsque on veut avoir l id d un eleve  on fait cette jointure : 
id_inscription IN (
        SELECT id
        FROM inscriptioneleve
        WHERE Eleve IN (
            SELECT id
            FROM eleve
            WHERE IdPersonne = "numéro de id "
        )
3. lorsque on veut savoir l id de la séance on fait la jointure suivante : s.id=e.SeanceDebut  avec s pour la seance et e pour Emploidutemps 
4.lorsque on demande l etat de paiement on ne mais pas p.Annuler=0 avec p paiement ni CASE
        WHEN p.Annuler = 1 THEN 'Annulé'
        ELSE 'Actif'
    END AS statut_paiement.
5. lorsque on veut savoir le paiement extra d un eleve on extrait le motif_paiement, le totalTTC  et le reste en faisant  la jointure entre le paiementextra et paiementextradetails d'une coté et paiementextra et paiementmotif d'une autre coté .
6. lorsque on demande les détails de paiement scolaire on extrait le mode de reglement ,numéro de chèque , montant et la date de l'opération. 
7.lorsque on demande l'mploi du temps d'un classe précie avec un jour précie on extrait le nom , le prénom de l'enseignant ,le nom de la matière , le nom de la salle , le debut et la fin de séance et le libelle de groupe (par classe...)
9.Les coordonées de debut et de la fin de séance se trouve dans le table emploidutemps sous forme d'id ,les covertir en heures a l'aide de table seance . 
10. la semaine A est d'id 2 , la semaine B est d'id 3 , Sans semaine d'id 1.
11. les colonnes principale  du table personne sont : id, NomFr, PrenomFr, NomAr , PrenomAr, Cin,AdresseFr, AdresseAr,Tel1,Tel2,Nationalite,Localite,Civilite.
12.pour les nom de jour en français on a une colone libelleJourFr avec mercredi c est ecrite Mercredi . 
13.utiliser des JOINs explicites . exemple au lieu de :WHERE
    e.Classe = (SELECT id FROM classe WHERE CODECLASSEFR = '7B2')
    AND e.Jour = (SELECT id FROM jour WHERE libelleJourFr = 'Mercredi')
    ecrire:
 JOIN
     jour j ON e.Jour = j.id AND j.libelleJourFr = 'Mercredi'
JOIN
     classe c ON e.Classe = c.id AND c.CODECLASSEFR = '7B2'
14. les résultats des trimestres se trouve dans le table Eduresultatcopie .
15. l id de l eleve est liée par l id de la personne par Idpersonne 
Voici la structure détaillée des tables pertinentes pour votre tâche (nom des tables, colonnes et leurs types) :
{{table_info}}

---
**Description des domaines pertinents pour cette question :**
{{relevant_domain_descriptions}}

---
**Informations Clés et Relations Fréquemment Utilisées pour une meilleure performance :**
{{relations}}

---
**Instructions pour la génération SQL :**
1.  Répondez UNIQUEMENT par une requête SQL MySQL valide et correcte.
2.  Ne mettez AUCUN texte explicatif ou commentaire avant ou après la requête SQL. La réponse doit être purement la requête.
3.  **Sécurité :** Générez des requêtes `SELECT` uniquement. Ne générez **JAMAIS** de requêtes `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE` ou toute autre commande de modification/suppression de données.
4.  **Gestion de l'Année Scolaire :** Si l'utilisateur mentionne une année au format 'YYYY-YYYY' (ex: '2023-2024'), interprétez-la comme équivalente à 'YYYY/YYYY' et utilisez ce format pour la comparaison sur la colonne `Annee` de `anneescolaire` ou pour trouver l'ID correspondant.
5.  **Robustesse aux Erreurs et Synonymes :** Le modèle doit être tolérant aux petites fautes de frappe et aux variations de langage. Il doit s'efforcer de comprendre l'intention de l'utilisateur même si les termes ne correspondent pas exactement aux noms de colonnes ou de tables. Par exemple, "eleves" ou "étudiants" devraient être mappés à la table `eleve`. "Moyenne" ou "résultat" devraient faire référence à `dossierscolaire.moyenne_general` ou `edumoymati`.


Question : {{input}}
Requête SQL :
"""
)

class SQLAssistant:
    def __init__(self):
        self.llm_client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        print("✅ LLM DeepSeek-V3 (via Together.ai) initialisé")
        
        self.db = SQLDatabase.from_uri(
            f"mysql+mysqlconnector://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}",
            sample_rows_in_table_info=0,
            engine_args={"pool_timeout": 30, "pool_recycle": 3600}
        )
        print("✅ SQLDatabase initialisé avec toutes les tables pour introspection.")

            
        self.input_cost_per_1k_tokens = 0.00125 
        self.output_cost_per_1k_tokens = 0.00125
        
        # Initialisation du cache
        self.cache_file_path = "question_cache2.json"
        self.cache_data = self.load_cache()
        self.relations_description = self.load_relations()

    def ask_llm(self, prompt: str) -> str:
        try:
            response = self.llm_client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Erreur LLM: {str(e)}")
            return ""
    
    def load_relations(self) -> str:
            return """
            [Relations principales]          
        - absence liée à inscriptioneleve.
        - actionfonctionalitepriv liée à fonctionaliteprivelge.
        - avertissement liée à inscriptioneleve.
        - banque liée à localite, personne.
        - banquebordereaudetails liée à banquebordereau, reglementeleve.
        - banqueversement liée à banquebordereau.
        - blame liée à inscriptioneleve.
        - caisse liée à utilisateur.
        - caisse_log liée à personne, utilisateur.
        - caissedetails liée à banqueversement, caisse, cantineparjour, paiementdetailscourete, personne, reglementeleve, utilisateur.
        - cantineparjour liée à utilisateur.
        - cantineparjourenseignant liée à utilisateur.
        - classe liée à etablissement, niveau.
        - delegation liée à gouvernorat.
        - disponibiliteenseignant liée à enseingant, jour.
        - dre liée à gouvernorat.
        - eleve liée à personne.
        - enseigantmatiere liée à anneescolaire, matiere, personne.
        - enseingant liée à diplome, modalitepaiement, personne, qualite, situationfamilliale.
        - etablissement liée à dre, gouvernorat, typeetablissement.
        - fichierpreinscriptionpreinscription liée à preinscriptionpreinscription.
        - fonctionaliteprivelge liée à rubrique.
        - inscriptioneleve liée à anneescolaire, personne.
        - jourfr liée à anneescolaire.
        - modalitetranche liée à anneescolaire, modalite.
        - paiement liée à inscriptioneleve, paiementmotif.
        - paiementdetailscourete liée à paiementcourete.
        - paiementextra liée à anneescolaire, classe, inscriptioneleve, modalite, paiementmotif, personne.
        - paiementextradetails liée à paiementextra.
        - parent liée à personne.
        - parenteleve liée à eleve, parent.
        - personne liée à civilite, localite, nationalite.
        - personnepreinscription liée à civilite, localite.
        - preinscription liée à eleve, niveau, personne, section.
        - preinscriptionpreinscription liée à elevepreinscription, niveau, personnepreinscription, section.
        - reglementeleve liée à modereglement, paiement, paiementextradetails, personne, uniformcommande, utilisateur.
        - reglementeleve_echeancier liée à modereglement, paiementextradetails, personne, uniformcommande, utilisateur.
        - renseignementmedicaux liée à eleve, personne.
        - section liée à niveau.
        - surveillant liée à diplome, modalitepaiement, personne, qualite, situationfamilliale.
        - uniformcommandedetails liée à uniformcommande, uniformcouleur, uniformmodel, uniformtaille.
        - uniformmodel liée à uniformgenre.
        - utilisateur liée à grade."""

    def count_tokens(self, text: str) -> int:
        """Counts tokens for a given text using the encoder."""
        return len(self.enc.encode(text))

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> tuple[int, float]:
        """Calculates total tokens and estimated cost."""
        total_tokens = prompt_tokens + completion_tokens
        input_cost = (prompt_tokens / 1000) * self.input_cost_per_1k_tokens
        output_cost = (completion_tokens / 1000) * self.output_cost_per_1k_tokens
        total_cost = input_cost + output_cost
        return total_tokens, total_cost

    def get_relevant_domains(self, query: str, domain_descriptions: Dict[str, str]) -> List[str]:
        """Identifies relevant domains based on a user query using DeepSeek."""
        domain_desc_str = "\n".join([f"- {name}: {desc}" for name, desc in domain_descriptions.items()])
        domain_prompt_content = f"""
        Based on the following user question, identify ALL relevant domains from the list below.
        Return only the names of the relevant domains, separated by commas. If no domain is relevant, return 'None'.

        User Question: {query}

        Available Domains and Descriptions:
        {domain_desc_str}

        Relevant Domains (comma-separated):
        """
        
        try:
            response = self.ask_llm(domain_prompt_content)
            domain_names = response.strip()
            
            if domain_names.lower() == 'none' or not domain_names:
                return []
            return [d.strip() for d in domain_names.split(',')]
        except Exception as e:
            print(f"❌ Erreur lors de l'identification des domaines: {e}")
            return []

    def get_table_structure(self):
        """Méthode utilitaire pour inspecter les colonnes des tables concernées"""
        tables_to_check = ['eleve', 'personne', 'localite', 'delegation']
        for table in tables_to_check:
            try:
                result = self.db.run(f"DESCRIBE {table};")
                print(f"\nStructure de la table {table}:")
                print(result)
            except Exception as e:
                print(f"❌ Erreur lors de l'inspection de {table}: {str(e)}")
   
    def get_tables_from_domains(self, domains: List[str], domain_to_tables_map: Dict[str, List[str]]) -> List[str]:
        """Retrieves all tables associated with the given domains."""
        tables = []
        for domain in domains:
            tables.extend(domain_to_tables_map.get(domain, []))
        return sorted(list(set(tables)))

    def ask_question(self, question: str) -> tuple[str, str, float, int]:
        if not hasattr(self, 'cache_data'):
            self.cache_data = self.load_cache()
            
        if question in self.cache_data:
            cached = self.cache_data[question]
            print("💡 Réponse chargée depuis le cache")
            self.save_history(question, cached["sql"], cached["response"])  
            return cached["sql"], cached["response"], 0.0, 0
        
        try:
            # Générer la requête SQL
            prompt = PROMPT_TEMPLATE.format(
                input=question,
                table_info=self.db.get_table_info(),
                relevant_domain_descriptions="\n".join(concise_domain_descriptions.values()),
                relations=self.relations_description
            )
            
            sql_query = self.ask_llm(prompt).strip()
            print(f"🔍 Requête générée: {sql_query}")

            # Exécuter la requête avec gestion d'erreur améliorée
            try:
                result = self.db.run(sql_query)
                print(f"⚡ Résultat brut de la base de données:\n{result}")  
                    
            except Exception as db_error:
                print(f"❌ Erreur DB: {str(db_error)}")
                return sql_query, f"Erreur d'exécution: {str(db_error)}", 0.0, 0
            
            # Calculer les tokens et coûts
            prompt_tokens = self.count_tokens(prompt)
            completion_tokens = self.count_tokens(sql_query)
            total_tokens, total_cost = self.calculate_cost(prompt_tokens, completion_tokens)
            
            # Si résultat non vide
            if result and result.strip() not in ["[]", ""] and not ("0 rows" in result):
                # Formater le résultat directement
                lines = [line for line in result.split('\n') if line.strip()]
                if len(lines) > 1:  # Au moins une ligne de données
                    header = [h.strip() for h in lines[0].split('|')]
                    rows = []
                    for line in lines[1:]:
                        if line.strip():
                            row = [cell.strip() for cell in line.split('|')]
                            rows.append(row)
                    
                    # Construire la réponse formatée
                    formatted = f"Résultats pour: {question}\n\n"
                    formatted += f"{header[0]:<25} | {header[1]}\n"
                    formatted += "-"*50 + "\n"
                    for row in rows:
                        formatted += f"{row[0]:<25} | {row[1]}\n"
                    
                    # Mise en cache
                    self.cache_data[question] = {
                        "sql": sql_query,
                        "response": formatted
                    }
                    self.save_cache()
                    
                    return sql_query, formatted, total_cost, total_tokens

        except Exception as e:
            error_msg = f"❌ Erreur système: {str(e)}"
            return "", error_msg, 0.0, 0    
        
        
    def load_cache(self) -> dict:
        """Charge le cache depuis le fichier JSON"""
        try:
            if os.path.exists(self.cache_file_path):
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Erreur de chargement du cache: {e}")
        return {}

    def save_history(self, question: str, sql: str, response: str):
        """Sauvegarde l'historique des questions dans un fichier JSON"""
        history_file = "query_history.json"
        try:
            # Charger l'historique existant
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []
            
            # Ajouter la nouvelle entrée
            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "question": question,
                "sql_query": sql,
                "response": response
            }
            history.append(entry)
            
            # Sauvegarder
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde de l'historique: {e}")
            
    def save_cache(self):
        """Sauvegarde le cache dans le fichier JSON"""
        try:
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2)
        except Exception as e:
            print(f"❌ Erreur de sauvegarde du cache: {e}")
            

def main():
    print("\n" + "="*50)
    print("🔍 Assistant Scolaire - Interrogation libre")
    print("="*50 + "\n")

    assistant = SQLAssistant()

    print("Tapez votre question (ou 'quit' pour quitter) :\n")

    while True:
        question = input("🧠 Question : ").strip()
        if question.lower() in ['quit', 'exit']:
            print("👋 Fin de session.")
            break

        print("⏳ Traitement en cours...")
        generated_sql, reponse, total_cost, total_tokens = assistant.ask_question(question)
        print("-"*50)

if __name__ == "__main__":
    main()