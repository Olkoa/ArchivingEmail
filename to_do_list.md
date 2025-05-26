# Tasks to execute at some point

- rebuild db en local

## Urgent

- faire cette requête claude

olkoa/src/rag/colbert_rag.py

can you check this file and tell me if replacing "emails_index" with f"{ACTIVE_PROJECT}_emails_index" everywhere would allow me to store and identify multiple indexes from colbert ragatouille or not ?

- Rajouter des critères pertinents pour décompter reçu vs envoyé.

- fix de l'app après modif 1 destinataire par ligne

- Pour faire une vrai création de projet et la transformation pst eml, penser à faire/lire ça: https://stackoverflow.com/questions/89228/how-do-i-execute-a-program-or-call-a-system-command


- Transformer l'app en traitement de mbox/pst à df de duckdb à df **en cours**

-  Extrait des mails envoyés depuis sa boîtes quand printés, problème de structure ? Trop de champs sans adresse, on met par défaut céline en envoyeur ?
['AAF - Céline Guyon <MAILER-DAEMON>']
address_str aaf_ca2019@listes.archivistes.org
['aaf_ca2019@listes.archivistes.org']
NO ADRESSSSS
NO ADRESSSSS
NO ADRESSSSS
address_str AAF - Céline Guyon <MAILER-DAEMON>
['AAF - Céline Guyon <MAILER-DAEMON>']
address_str "Henri Zuber"
['"Henri Zuber"']
NO ADRESSSSS
NO ADRESSSSS
NO ADRESSSSS
### Tâches

- demander à hedi ajouter options TOP 10, 50 et 100 avec un slider sur le graph

- restructured db

- désactiver la transformation des adresses mails qui retire les points ou laisser la gestion du + uniquement.

- explorer la raison de ce warning
Warning: Error in relationship creation: Constraint Error: Violates foreign key constraint because key "email_id: d775662b-63da-4d5c-bfbf-debc42be77a4" is still referenced by a foreign key in a different table. If this is an unexpected constraint violation, please refer to our foreign key limitations in the documentation
Continuing with database optimization...

- enlever le côté cliquable des mails affichés qui s'ouvrent directement sur outlook sur le pc

- mettre en place des tests à lister ici sur la partie gestion de projets
  - mail adresse invalide
  - rahouter input date plus accessible que celui en place
  - test de création de projet sans données
  - test de pas remplir Position orga ou Entity

- Mettre l'app en français

- demander quelles normes suivre pour l'affichage des dates pour des archivistes ?

- check 200m limit

- set un projet comme actif depuis le fichier constants.py ?

--------------------------------------------------------------------------------------
### Pistes d'améliorations post restitution

--------------------------------------------------------------------------------------
### Clarté du code

--------------------------------------------------------------------------------------
### Documentation

--------------------------------------------------------------------------------------
### robustesse

--------------------------------------------------------------------------------------
### amélioration des performances du code


----------------------------------------------------------------------------------------
jina colbert v2
