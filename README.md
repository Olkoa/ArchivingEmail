## 1. Contexte et objectifs
### 1.1 Contexte

Le projet s'inscrit dans une collaboration entre La Plateforme et Olkoa, avec les Archives départementales du Vaucluse comme partenaire fournisseur de corpus. Il vise à explorer l'application de technologies d'IA pour améliorer l'exploitation des messageries électroniques archivées.

## 1.2 Objectifs généraux

- Développer un prototype permettant d'explorer et de naviguer dans des corpus de messageries électroniques archivées au format PST
- Faciliter le travail des archivistes dans l'évaluation et le traitement des messageries
- Améliorer l'accessibilité du contenu informationnel pour les chercheurs en sciences humaines
- Tester et valider des approches d'IA adaptées aux spécificités des corpus de courriels en français

## 2. Architecture technique
### 2.1 Infrastructure

- Déploiement via Docker sur la plateforme Onyxia
- Architecture serveur/client permettant de gérer le volume de données et les calculs intensifs
- Possibilité d'utiliser des ressources GPU à la demande pour l'entraînement ou l'adaptation des modèles
- Toutes les données resteront dans l'environnement contrôlé pour respecter les exigences de confidentialité

### 2.2 Sécurité et protection des données

- Mise en place d'une authentification pour l'accès à l'application
- Traitement des données personnelles en conformité avec le RGPD
- Mise en œuvre de mécanismes de pseudonymisation si nécessaire
- Pas d'utilisation d'API externes pour éviter toute fuite de données

### 2.3 Stack technologique

- Backend: Python (FastAPI)
- Frontend: TBD (streamlit, ou plus avancé ?)
- Base de données: SQLite et Elasticsearch
- IA/ML : embeddings (notamment ColBERTv2), classifieurs (dérivés de BERT), peut-être LLM
- Visualisation : TBD

## 3. Fonctionnalités détaillées par sprint
### Sprint 1: Visualisation et exploration (Embeddings et Elasticsearch)
#### 3.1.1 Extraction et prétraitement des données

- Parser les fichiers PST pour extraire les courriels et leurs métadonnées
- Traiter les encodages et caractères spéciaux
- Extraction basique du contenu des pièces jointes (texte)
- Normalisation des adresses email et des noms pour l'analyse des correspondants

#### 3.1.2 Indexation et embeddings

- Indexation complète des courriels dans Elasticsearch
- Génération d'embeddings pour le contenu textuel des messages
- Création d'une structure de données pour représenter les relations entre messages
- Analyse des fils de discussion et reconstruction des conversations

#### 3.1.3 Interface de visualisation

- Vue d'ensemble du corpus (statistiques, chronologie, volume)
- Visualisation du réseau de communication (graphe des échanges)
- Vue thématique (clusters de sujets identifiés par les embeddings)
- Chronologie interactive des échanges

#### 3.1.4 Recherche avancée

- Interface de recherche full-text
- Recherche sémantique basée sur les embeddings
- Filtres multiples (date, expéditeur, destinataire, présence de pièces jointes...)
- Sauvegarde des recherches fréquentes

### Sprint 2: Interface conversationnelle (RAG)

### Sprint 3: Reconnaissance d'entités nommées (NER)

## 4. Méthodologie et organisation
### 4.1 Organisation des sprints

Durée: 3 sprints d'un mois chacun
Démarrage: 31 mars 2025
Revue de sprint: à la fin de chaque période d'un mois

### 4.2 Équipe

La Plateforme :

Joël Gombin (chef de projet)
Hedi Zarrouck et Julien Ract-Mugnerot


Olkoa:

Céline Guyon

Utilisateurs finaux:

Archivistes des Archives départementales du Vaucluse pour les tests et retours 



### 4.3 Modalités de travail

Atelier de co-construction au début de chaque sprint (idéalement en présentiel)
Comité de suivi hebdomadaire en visioconférence
Environnement de développement partagé et versionné (GitHub ou équivalent)
Documentation continue du projet et de la méthodologie
Atelier de restitution/démo en fin de sprint

### 4.4 Livrables

Code : Dépôt GitHub avec documentation complète
Application : Déploiement Docker 
Documentation : README + code commenté

Journal du projet pouvant servir à une communication scientifique ultérieure


5. Risques et mitigation
5.1 Risques techniques

Complexité des formats PST: plan de test initial avec un petit échantillon représentatif
Performance avec des volumes importants: architecture évolutive et monitoring des performances
Qualité des modèles en français: adaptation ou fine-tuning des modèles existants

5.2 Risques organisationnels

Disponibilité des corpus: accord formel préalable avec les AD Vaucluse
Coordination entre équipes: définition claire des rôles et canaux de communication
Évolution des besoins: approche agile permettant des ajustements en cours de projet

5.3 Risques liés aux données

Confidentialité: mise en place de procédures strictes de gestion des accès
Données personnelles: mécanismes de pseudonymisation dès le début du projet
Qualité variable des corpus: stratégies de prétraitement adaptatives
