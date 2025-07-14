from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import mysql.connector
from typing import List, Dict
import tiktoken 
import json
from pathlib import Path
import sys
import re



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
        "viewabsence", "viewavertissement", "viewblame", "viewgetblame", "viewgetretard",
        "viewgetretards", "viewretard", "viewstatmoyenneglobal",
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
        "viewcantineparjour", "viewcantineparjourenseignant","viewetatcantineparjour",
         "cantine", "menu_cantine", "menu_cantine_jour", "suivicantineparjour",
        "cantineparjour", "cantineparjourenseignant","nvetatcantineparjourglobale",
    ],
    "PERSONNEL_ENSEIGNEMENT": [
        "viewenseignant", "viewgetmatiereclasseenseignant", "viewmatiereenseignant","viewrepartitionenseignant", "viewrepartitionsurveillant",
        "educycleens", "edumatiere","teamsteacherrostarview",
        "enseignant_double", "enseignant_motif", "enseignant_paiement", "enseignants_presence", "grade",
        "matiere", "naturematiere", "matiereexamenbloque", "matieresection", "qualite", "personnesupp",
        "teamsteacher", "teamsteacherrostar", "teamspasswordteacher", "disponibiliteenseignant",
        "enseigantmatiere", "enseingant", "surveillant","personne"
    ],
    "FINANCES_PAIEMENTS": [
        "viewetatdepaiementuniform", "viewextras", "viewgetclub", "viewgetpaiementextra",
        "viewgetpaiementscolaire", "viewgetpaiementscolairedetaillee", "viewrchequeecheancier",
        "viewreglementecheanciernonvalide", "viewtranchepaiement", "viewuniformcommande",
        "caissemotif", "configuration", "infosfornisseur", "inscriptionelevecourete", "modalite", "banquebordereau",
        "modalitepaiement", "modereglement", "paiementcourete", "paiementmotif", "reglementfornisseur",
        "situationeleve", "banque", "banquebordereaudetails", "banqueversement", "caisse", "caisse_log",
        "caissedetails", "uniformcommande", "modalitetranche", "paiement", "paiementdetailscourete",
        "paiementextra", "paiementextradetails", "reglementeleve", "reglementeleve_echeancier",
        "uniformcommandedetails", "uniformmodel"
    ],
    "EMPLOIS_DU_TEMPS": [
        "viewemploi", "viewemploi_enligne", "viewemploiexameneleve", "groupe", "groupecourete",
        "homeworkclasse", "jour", "periodeexamen", "matiere", "repartitionexamen", "repartitionexamencopie",
        "repartitionsemaine", "salle", "seance", "sectioncourete", "semaine", "trimestre", "typepre", "jourfr"
    ],
    "GENERAL_ADMINISTRATION_CONFIG": [
        "viewcasiervide", "viewgetinscicasier", "viewstatistiquelocalite", "actualite1", "actualites",
        "anneescolaire", "civilite", "codepostal", "configaffichage", "configmatiereclsstat",
        "configmatierenivstat", "diplome", "dre", "educlasse", "edusection", "eduniveau", "gouvernorat",
        "localite", "extracasier", "extraclub", "extravaucher", "motifdoc", "motifsms", "motiftelechargement",
        "notifications", "notificationcompagne", "pays", "niveau", "privilege", "reclamation", "rubrique",
        "smscampagnes", "smslog", "suggestion", "telechargement", "test", "test2", "tokenfirebases",
        "typeetablissement", "typemessagerie", "typesms", "uniformcouleur", "uniformgenre",
        "uniformtaille", "user", "useradmin", "utilisateur", "actionfonctionalitepriv", "classe",
        "delegation", "dre", "etablissement", "fonctionaliteprivelge", "personne", "section", "utilisateur"
    ]
}


# === Configuration MySQL ===
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
    input_variables=["input", "table_info", "relevant_domain_descriptions", "relations","result"],
    template=f"""
[SYSTEM] Vous êtes un assistant SQL expert pour une base de données scolaire.
Votre rôle est de traduire des questions en français en requêtes SQL MySQL.

Voici la structure détaillée des tables pertinentes pour votre tâche (nom des tables, colonnes et leurs types) :
{{table_info}}

---
**Description des domaines pertinents pour cette question :**
{{relevant_domain_descriptions}}

---
**Informations Clés et Relations Fréquemment Utilisées pour une meilleure performance :**
{{relations}}

---
**Informations Clés et Relations Fréquemment Utilisées pour une meilleure performance :**
Pour optimiser la génération de requêtes et la pertinence, voici un résumé des entités et de leurs liens principaux :

-   **Entités Centrales (Personnes & Inscriptions) :**
    -   **`personne`**: Contient les informations de base (NomFr, PrenomFr, Cin, Email, Tel1) pour toutes les entités (élèves, parents, enseignants, utilisateurs, surveillants).
        -   Lié à : `eleve.IdPersonne`, `parent.Personne`, `enseingant.idPersonne`, `utilisateur.Personne`, `surveillant.idPersonne`, `renseignementmedicaux.idPersonne`.
    -   **`eleve`**: Informations spécifiques à l'élève.
        -   Lié à : `personne.id` via `IdPersonne`, `renseignementmedicaux.idEleve`.
    -   **`inscriptioneleve`**: **Table principale pour les inscriptions des élèves.** Relie un `Eleve` à une `Classe` pour une `AnneeScolaire`. La colonne `Annuler`  indique si l'inscription est annulée (1 pour annulé, 0 sinon).
        -   Lié à : `eleve.id` via `Eleve`, `classe.id` via `Classe`, `anneescolaire.id` via `AnneeScolaire`.
    -   **`parent`**: Informations sur les parents  lié à : `personne.id` via `Personne`.
    -   **`parenteleve`**: Table de liaison entre `parent` et `eleve` pour définir la relation parent-enfant (ex: Type='Pere', 'Mere').

-   **Structure Scolaire :**
    -   **`anneescolaire`**: Gère les années scolaires. La colonne `AnneeScolaire`  stocke l'année au format 'YYYY/YYYY' (ex: '2023/2024').tu peut accepter la format `YYYY-YYYY` ou `YYYY/YYYY` .
    -   **`classe`**: Définit les classes (groupes d'élèves).
        -   Lié à : `anneescolaire.id` via `ID_ANNEE_SCO`, `niveau.id` via `IDNIV`, `etablissement.id` via `CODEETAB`. Contient des noms de classe comme `NOMCLASSEFR`.
    -   **`niveau`**: Contient les niveaux scolaires (ex: "4ème").
        -   **Important : Le nom du niveau est stocké dans la colonne NOMNIVFR de la table `niveau` .**
        -   Lié à : `classe.id` via `IDNIV`, `section.IdNiv`.
    -   **`section`**: Définit les sections au sein des niveaux (ex: "4 ème Maths", "2 ème Sciences").
        -   Lié à : `niveau.id` via `IdNiv`.
    -   **`etablissement`**: Gère les établissements scolaires.
    -   **`jourfr`**: Table des jours, utile pour les plannings ou les disponibilités.

-   **Personnel & Matières :**
    -   **`enseingant`**: Informations sur les enseignants, lié à `personne` via `idPersonne`.
    -   **`enseigantmatiere`**: Associe les enseignants aux matières pour une année scolaire.
    -   **`disponibiliteenseignant`**: Gère les plages de disponibilité des enseignants.
    -   **`surveillant`**: Informations sur les surveillants, lié à `personne` via `idPersonne`.
    -   **`utilisateur`**: Gère les utilisateurs du système, lié à `personne` via `Personne` (implicite si `personne.id` est utilisé pour `utilisateur.id`).

-   **Incidents & Suivi des Élèves :**
    -   **`absence`**, **`avertissement`**, **`blame`**: Ces tables enregistrent différents types d'incidents/comportements. Elles sont toutes liées à `inscriptioneleve.id` via leur colonne `Inscription` et souvent à `Enseignant` et `Matiere`.
    -   **`renseignementmedicaux`**: Contient des informations médicales détaillées pour une `personne` ou un `eleve`.

-   **Gestion Administrative/Financière :**
    -   **`banque`**: Informations sur les banques, liées à `localite` et `personne`.
    -   **`banquebordereaudetails`**, **`banqueversement`**: Tables liées aux bordereaux et versements bancaires.
    -   **`caisse`**, **`caisse_log`**, **`caissedetails`**: Gèrent les opérations de caisse et les logs associés, liées à `utilisateur` et `personne`, ainsi qu'où règlements et versements.
    -   **`cantineparjour`**, **`cantineparjourenseignant`**: Gèrent les paiements de cantine pour élèves et enseignants.
    -   **`modalitetranche`**: Définit les modalités de paiement et les tranches tarifaires (HT, TTC, TVA, Remise) pour chaque `Modalite` et `AnneeScolaire`.
    -   **`paiement`**: Enregistre les paiements scolaires principaux (lié à `inscriptioneleve` et `paiementmotif`). Contient le `MontantRestant` et si le paiement est `Annuler`.
    -   **`paiementdetailscourete`**: Détails des paiements pour des cours d'été (lié à `paiementcourete`, non détaillé ici).
    -   **`paiementextra`**: Enregistre les paiements pour des activités extrascolaires (clubs, casiers, etc.). Lié à `inscriptioneleve`, `paiementmotif`, `personne`, `anneescolaire`, `classe`, `modalite`.
    -   **`paiementextradetails`**: Détails spécifiques des paiements extrascolaires.
    -   **`reglementeleve`**: Enregistre les règlements effectués par les élèves (ou leurs parents), lié à `modereglement`, `paiement`, `paiementextra` et `personne`. Contient les détails du mode de paiement (`NumCheque`, `Proprietaire`, `Banque`), l'état d'annulation (`Annule`), et le type de règlement (`TypeReglement`).
    -   **`reglementeleve_echeancier`**: Gère les échéanciers de paiement pour les règlements des élèves.

-   **Pré-inscription :**
    -   **`personnepreinscription`**: Informations de base pour les personnes en phase de pré-inscription, similaire à `personne` mais pour le processus de pré-inscription.
    -   **`preinscription`**: Enregistre les demandes de pré-inscription des élèves. Contient les détails de l'élève, l'établissement, le niveau et la section souhaités et précédents, les moyennes scolaires et la décision finale.
        -   Lié à : `eleve.id` via `Eleve`, `personne.id` via `Personne`, `niveau.id` via `Niveau` et `NiveauPrecedent`, `section.id` via `Section` et `SectionPrecedent`.
    -   **`preinscriptionpreinscription`**: Semble être une duplication ou une table liée à `preinscription` avec un nom similaire, il est important de noter sa dépendance à `personnepreinscription` et `elevepreinscription`.
    -   **`fichierpreinscriptionpreinscription`**: Contient les fichiers associés aux pré-inscriptions.
    -   ** Si un éleve est nouvellement  inscris a l'ecole  alors TypeInscris est 'N' si il va faire un renouvellement a son inscris alors TypeInscris='R'.

-   **Gestion des Uniformes :**
    -   **`uniformcommandedetails`**: Détails des articles commandés pour les uniformes.
        -   Lié à : `uniformcommande.id`, `uniformmodel.id`, `uniformtaille.id` , `uniformcouleur.id`.
    -   **`uniformmodel`**: Définit les modèles d'uniformes (ex: "chemise", "pantalon") Lié à : `uniformgenre.id` .

-   **Privilèges et Fonctionnalités :**
    -   **`actionfonctionalitepriv`**: Actions associées aux fonctionnalités privilégiées.
    -   **`fonctionaliteprivelge`**: Définit les fonctionnalités privilégiées.

    **Utilisation des Fonctions d'Agrégation et de DISTINCT :**
+
+Les fonctions d'agrégation sont utilisées pour effectuer des calculs sur un ensemble de lignes et retourner une seule valeur.

 -   **`COUNT(colonne)`**: Compte le nombre de lignes (ou de valeurs non NULL dans une colonne).
     -   **`COUNT(*)`**: Compte toutes les lignes, y compris celles avec des valeurs NULL.
     -   **`COUNT(colonne)`**: Compte les lignes où `colonne` n'est pas NULL.
     -   **`COUNT(DISTINCT colonne)`**: Compte le nombre de **valeurs uniques** (distinctes) dans une colonne. **Utilisez `DISTINCT` avec `COUNT` lorsque la question demande le nombre de choses *différentes* ou *uniques* (par exemple, "nombre d'élèves", "nombre de matières distinctes").**
 -   **`SUM(colonne)`**: Calcule la somme totale des valeurs numériques d'une colonne.
 -   **`AVG(colonne)`**: Calcule la moyenne des valeurs numériques d'une colonne.
 -   **`MAX(colonne)`**: Trouve la valeur maximale dans une colonne.
 -   **`MIN(colonne)`**: Trouve la valeur minimale dans une colonne.

+**Règles Importantes pour les Agrégations :**
+-   Si vous utilisez une fonction d'agrégation avec des colonnes non agrégées dans votre `SELECT`, vous devez toujours utiliser une clause `GROUP BY` qui inclut toutes les colonnes non agrégées du `SELECT`.
+-   Considérez attentivement si `DISTINCT` est nécessaire pour `COUNT` afin d'éviter de compter des doublons (par exemple, un élève inscrit dans plusieurs classes si la requête ne le gère pas via `inscriptioneleve` directement).

+**Lexique et Mappage de Termes Courants :**
+Le modèle doit être tolérant aux petites fautes de frappe et aux variations de langage. Voici un guide pour mapper les termes courants de l'utilisateur aux éléments de la base de données :
+
+-   **"élèves", "étudiants", "effectif", "scolaires"** -> Faire référence principalement à la table `eleve` et potentiellement `inscriptioneleve` pour le contexte d'inscription. Utilisez `eleve.id` pour des décomptes distincts.
+-   **"moyenne", "score", "résultat"** -> Se référer à `dossierscolaire.moyenne_general` (pour la moyenne générale) ou `edumoymati.Moyenne` (pour la moyenne par matière).
+-   **"classe de X", "niveau X", "en Xème"** -> Utiliser `classe.NOMCLASSEFR` ou `niveau.NOMNIVFR`. Le nom du niveau est dans `niveau.NOMNIVFR`.
+-   **"enseignant", "prof", "formateur"** -> Table `enseingant`.
+-   **"parent", "tuteur légal", "représentant"** -> Table `parent` ou `representantlegal`.
+-   **"date de naissance", "anniversaire"** -> Colonne `DateNaissance` de la table `personne`.
+-   **"adresse", "lieu de résidence"** -> Colonnes d'adresse dans la table `personne`.
+-   **"absences", "retards", "blâmes", "avertissements"** -> Tables `absence`, `retard`, `blame`, `avertissement` respectivement.
+-   **"paiement", "frais", "scolarité", "règlement"** -> Tables `paiement`, `reglementeleve`, `paiementextra`.
+-   **"année scolaire", "saison scolaire"** -> Table `anneescolaire`, colonne `AnneeScolaire` (format 'YYYY/YYYY').
+-   **"matière", "cours", "discipline"** -> Table `matiere`, colonne `NomMatiereFr`.
+-   **"cantine", "repas"** -> Tables `cantine`, `menu_cantine`, `cantineparjour`.
+-   **"emplois du temps", "planning des cours"** -> Table `viewemploi`, `repartitionsemaine`.
+-   **"personnel", "employés"** -> Tables `personne`, `enseingant`, `surveillant`.


**Instructions pour la génération SQL :**
1.  Répondez UNIQUEMENT par une requête SQL MySQL valide et correcte.
2.  Ne mettez AUCUN texte explicatif ou commentaire avant ou après la requête SQL. La réponse doit être purement la requête.
3.  **Sécurité :** Générez des requêtes `SELECT` uniquement. Ne générez **JAMAIS** de requêtes `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE` ou toute autre commande de modification/suppression de données.
4.  **Gestion de l'Année Scolaire :** Si l'utilisateur mentionne une année au format 'YYYY-YYYY' (ex: '2023-2024'), interprétez-la comme équivalente à 'YYYY/YYYY' et utilisez ce format pour la comparaison sur la colonne `Annee` de `anneescolaire` ou pour trouver l'ID correspondant.
5.  **Robustesse aux Erreurs et Synonymes :** Le modèle doit être tolérant aux petites fautes de frappe et aux variations de langage. Il doit s'efforcer de comprendre l'intention de l'utilisateur même si les termes ne correspondent pas exactement aux noms de colonnes ou de tables. Par exemple, "eleves" ou "étudiants" devraient être mappés à la table `eleve`. "Moyenne" ou "résultat" devraient faire référence à `dossierscolaire.moyenne_general` ou `edumoymati`.


Question : {input}
Résultat SQL : 

Donne une réponse claire et naturelle en français basée sur ce résultat.
Présente la réponse sous forme de tableau ou liste avec des lignes "Année : Nombre".
N'affiche jamais la requête SQL.
    """,
)

class SQLAssistant:
    def __init__(self):
        self.llms = {
            "gpt-3.5-turbo": ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1, request_timeout=120.0),
            "gpt-4": ChatOpenAI(model="gpt-4", temperature=0.1, request_timeout=120.0),
        }
        print("✅ Modèles GPT-3.5 et GPT-4 initialisés.")

        self.db = SQLDatabase.from_uri(
            f"mysql+mysqlconnector://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}",
            sample_rows_in_table_info=0,
            engine_args={"pool_timeout": 30, "pool_recycle": 3600}
        )
        print("✅ SQLDatabase initialisé avec toutes les tables pour introspection.")

        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")  # encodage fixé à 3.5
        self.input_cost_per_1k_tokens = 0.0005
        self.output_cost_per_1k_tokens = 0.0015
        print(f"💰 Coût par 1K tokens (Input/Output) : ${self.input_cost_per_1k_tokens}/ ${self.output_cost_per_1k_tokens}")
        
        self.cache_file_path = "question_cache_Hybride.json"
        self.cache_data = self.load_cache()
        self.relations_description = self.load_relations()

    def select_llm(self, question: str, force_gpt4: bool = False) -> ChatOpenAI:
        if force_gpt4 or self.is_query_complex(question):
            return self.llms["gpt-4"]
        return self.llms["gpt-3.5-turbo"]

    def is_query_complex(self, question: str) -> bool:
        keywords = ["tendance", "évolution", "statistique", "corrélation", "variation", "répartition", "top", "analyse"]
        long_question = len(question.split()) > 20
        has_advanced_keywords = any(word in question.lower() for word in keywords)
        return long_question or has_advanced_keywords

    def load_relations(self, filepath="prompt_relations.txt") -> str:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"❌ Fichier de relations non trouvé : {filepath}")
            return ""

    def count_tokens(self, text: str) -> int:
        return len(self.enc.encode(text))

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> tuple[int, float]:
        total_tokens = prompt_tokens + completion_tokens
        cost = (prompt_tokens / 1000 * self.input_cost_per_1k_tokens) + \
               (completion_tokens / 1000 * self.output_cost_per_1k_tokens)
        return total_tokens, cost

    def get_relevant_domains(self, query: str, domain_descriptions: Dict[str, str]) -> List[str]:
        domain_desc_str = "\n".join([f"- {name}: {desc}" for name, desc in domain_descriptions.items()])
        domain_prompt_content = f"""
        Based on the following user question, identify ALL relevant domains from the list below.
        Return only the names of the relevant domains, separated by commas. If no domain is relevant, return 'None'.

        User Question: {query}

        Available Domains and Descriptions:
        {domain_desc_str}

        Relevant Domains (comma-separated):
        """

        prompt_tokens_domain = self.count_tokens(domain_prompt_content)

        try:
            llm_model = self.select_llm(query)
            print(f"🧠 Modèle utilisé pour détection domaines : {llm_model.model_name}")
            response = llm_model.invoke(domain_prompt_content)
            domain_names = response.content.strip()
            completion_tokens_domain = self.count_tokens(domain_names)

            _, _ = self.calculate_cost(prompt_tokens_domain, completion_tokens_domain)

            if domain_names.lower() == 'none' or not domain_names:
                return []
            return [d.strip() for d in domain_names.split(',')]
        except Exception as e:
            print(f"❌ Erreur lors de l'identification des domaines: {e}")
            return []

    def get_tables_from_domains(self, domains: List[str], domain_to_tables_map: Dict[str, List[str]]) -> List[str]:
        tables = []
        for domain in domains:
            tables.extend(domain_to_tables_map.get(domain, []))
        return sorted(list(set(tables)))

    def ask_question(self, question: str) -> tuple[str, str, float, int]:
        total_interaction_cost = 0.0
        total_interaction_tokens = 0

        if question in self.cache_data:
            cached = self.cache_data[question]
            print("💡 Réponse chargée depuis le cache.")
            return cached["sql"], cached["response"], 0.0, 0

        try:
            print("Identifying relevant domains...")
            relevant_domains = self.get_relevant_domains(question, concise_domain_descriptions)
            print(f"✅ Domaines pertinents : {relevant_domains}")

            if not relevant_domains:
                return "NO_SQL_GENERATED", "Aucun domaine pertinent trouvé.", 0.0, 0

            relevant_tables = self.get_tables_from_domains(relevant_domains, domain_to_tables_mapping)

            if not relevant_tables:
                return "NO_SQL_GENERATED", "Aucune table correspondante trouvée.", 0.0, 0

            MAX_TABLES = 6
            filtered_tables = relevant_tables[:MAX_TABLES]
            print(f"📉 Tables utilisées pour GPT : {filtered_tables}")
            raw_table_info = self.db.get_table_info(table_names=filtered_tables)
            filtered_table_info = self.compress_table_info(raw_table_info)


            relevant_domain_desc_for_prompt = ""
            for domain_name in relevant_domains:
                if domain_name in concise_domain_descriptions:
                    relevant_domain_desc_for_prompt += f"- **{domain_name}**: {concise_domain_descriptions[domain_name]}\n"

            sql_prompt_content = PROMPT_TEMPLATE.format(
                input=question,
                table_info=filtered_table_info,
                relevant_domain_descriptions=relevant_domain_desc_for_prompt,
                relations=self.relations_description
            )
            prompt_tokens_sql = self.count_tokens(sql_prompt_content)

            # ✨ Essai initial avec le modèle sélectionné (3.5 ou 4)
            llm_model = self.select_llm(question)
            print(f"🧠 Modèle initial : {llm_model.model_name}")

            try:
                sql_query_response = llm_model.invoke(sql_prompt_content)
                sql_query = sql_query_response.content.strip()
            except Exception as e:
                print(f"⚠️ Erreur avec {llm_model.model_name} : {e}")
                if llm_model.model_name == "gpt-3.5-turbo":
                    print("🔁 Fallback vers GPT-4...")
                    llm_model = self.llms["gpt-4"]
                    sql_query_response = llm_model.invoke(sql_prompt_content)
                    sql_query = sql_query_response.content.strip()
                else:
                    raise e

            completion_tokens_sql = self.count_tokens(sql_query)

            sql_tokens, sql_cost = self.calculate_cost(prompt_tokens_sql, completion_tokens_sql)
            total_interaction_tokens += sql_tokens
            total_interaction_cost += sql_cost

            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            # if not sql_query.lower().startswith('select'):
            #     return "SECURITY_VIOLATION", "❌ Requête bloquée : uniquement SELECT autorisé.", total_interaction_cost, total_interaction_tokens

            result = self.db.run(sql_query)

            response_prompt_content = f"""
            Question : {question}
            Résultat SQL : {result}

            Donne une réponse claire et naturelle en français basée sur ce résultat.
            N'affiche jamais la requête SQL.
            """
            prompt_tokens_nl = self.count_tokens(response_prompt_content)

            print(f"🧠 Modèle utilisé pour génération NL : {llm_model.model_name}")
            try:
                nl_response_obj = llm_model.invoke(response_prompt_content)
                nl_response = nl_response_obj.content.strip()
            except Exception as e:
                print(f"⚠️ Erreur GPT-NL avec {llm_model.model_name} : {e}")
                if llm_model.model_name == "gpt-3.5-turbo":
                    print("🔁 Fallback NL vers GPT-4...")
                    llm_model = self.llms["gpt-4"]
                    nl_response_obj = llm_model.invoke(response_prompt_content)
                    nl_response = nl_response_obj.content.strip()
                else:
                    raise e

            completion_tokens_nl = self.count_tokens(nl_response)

            nl_tokens, nl_cost = self.calculate_cost(prompt_tokens_nl, completion_tokens_nl)
            total_interaction_tokens += nl_tokens
            total_interaction_cost += nl_cost

            self.cache_data[question] = {
                "sql": sql_query,
                "response": nl_response
            }
            self.save_cache()
            print(f"✅ Modèle final utilisé : {llm_model.model_name}")
            return sql_query, nl_response, total_interaction_cost, total_interaction_tokens

        except Exception as e:
            error_msg = f"❌ Erreur : {str(e)}"
            print(error_msg)
            return "ERROR_SQL_GENERATION", error_msg, total_interaction_cost, total_interaction_tokens

    def compress_table_info(self, raw_table_info: str, keep_keywords=None) -> str:
        if keep_keywords is None:
            keep_keywords = ["nom", "prenom", "date", "classe", "niveau", "email", "tel", "id", "type", "annee"]
        
        lines = raw_table_info.splitlines()
        filtered_lines = [line for line in lines if any(k in line.lower() for k in keep_keywords)]
        
        # Si le filtrage est trop sévère, on renvoie les 20 premières lignes pour éviter un crash
        if len(filtered_lines) < 5:
            return "\n".join(lines[:20])
        return "\n".join(filtered_lines)

    
    def load_cache(self) -> Dict[str, Dict[str, str]]:
        try:
            if Path(self.cache_file_path).exists():
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return {}
                    return json.loads(content)
        except Exception as e:
            print(f"⚠️ Erreur de lecture du cache : {e}")
        return {}

    def save_cache(self):
        try:
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Cache sauvegardé.")
        except Exception as e:
            print(f"❌ Erreur de sauvegarde cache : {e}")

    def get_cached_response(self, question: str) -> tuple[str, str] | None:
        return self.cache_data.get(question)

def main():
    print("\n" + "=" * 60)
    print("🧠 Assistant IA Scolaire - Interrogation Libre")
    print("=" * 60 + "\n")

    force_gpt4 = "--gpt4" in sys.argv
    if force_gpt4:
        print("⚠️  GPT-4 forcé pour toutes les requêtes.\n")

    assistant = SQLAssistant()

    print("💬 Tape ta question (ou 'quit' / 'exit' pour quitter) :\n")

    while True:
        try:
            question = input("🧠 Question : ").strip()
            if question.lower() in ['quit', 'exit']:
                print("👋 Fin de session. À bientôt !")
                break

            print("⏳ Traitement en cours...\n")
            sql, response, cost, tokens = assistant.ask_question(question)

            print(f"💻 Requête SQL générée :\n{sql}\n")
            print(f"📘 Réponse naturelle :\n{response}\n")
            print(f"💲 Coût total de l'interaction : {cost:.6f} $")
            print(f"📝 Nombre total de tokens utilisés : {tokens}")
            print("-" * 60)

        except KeyboardInterrupt:
            print("\n👋 Interruption. À bientôt !")
            break
        except Exception as e:
            print(f"❌ Erreur inattendue : {e}")
            continue
        
if __name__ == "__main__":
    main()