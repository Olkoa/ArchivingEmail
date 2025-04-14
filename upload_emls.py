import os
import zipfile
import boto3
import json
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

def setup_logging(log_file):
    """
    Configure la journalisation dans un fichier
    
    Args:
        log_file (str): Chemin du fichier de log
    """
    # Créer le dossier de logs s'il n'existe pas
    log_dir = Path(log_file).parent
    log_dir.mkdir(exist_ok=True)
    
    # Configurer le logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def load_env():
    """
    Charge les variables d'environnement depuis le fichier .env
    """
    # Essayer de charger depuis le dossier courant
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        logging.info("Variables d'environnement chargées depuis .env")
    else:
        logging.warning("Avertissement: Fichier .env non trouvé")

def parse_arguments():
    """
    Parse les arguments de la ligne de commande
    
    Returns:
        argparse.Namespace: Arguments parsés
    """
    parser = argparse.ArgumentParser(description='Dézippe des fichiers ZIP et upload les EML vers S3')
    
    parser.add_argument(
        '--source-dir',
        type=str,
        required=True,
        help='Chemin du dossier source contenant les fichiers ZIP'
    )
    
    parser.add_argument(
        '--bucket-name',
        type=str,
        required=True,
        help='Nom du bucket S3 de destination'
    )
    
    parser.add_argument(
        '--state-file',
        type=str,
        default='upload_state.json',
        help='Chemin du fichier d\'état (défaut: upload_state.json)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default='logs/upload.log',
        help='Chemin du fichier de log (défaut: logs/upload.log)'
    )
    
    parser.add_argument(
        '--aws-access-key-id',
        type=str,
        help='Clé d\'accès AWS (peut aussi être définie via AWS_ACCESS_KEY_ID)'
    )
    
    parser.add_argument(
        '--aws-secret-access-key',
        type=str,
        help='Clé secrète AWS (peut aussi être définie via AWS_SECRET_ACCESS_KEY)'
    )
    
    parser.add_argument(
        '--s3-endpoint-url',
        type=str,
        help='URL de l\'endpoint S3 (peut aussi être définie via S3_ENDPOINT_URL)'
    )
    
    parser.add_argument(
        '--s3-region-name',
        type=str,
        help='Nom de la région S3 (peut aussi être définie via S3_REGION_NAME)'
    )
    
    return parser.parse_args()

def check_credentials(aws_access_key_id, aws_secret_access_key):
    """
    Vérifie la présence des identifiants AWS
    
    Args:
        aws_access_key_id (str): Clé d'accès AWS
        aws_secret_access_key (str): Clé secrète AWS
        
    Returns:
        bool: True si les identifiants sont présents
    """
    if not aws_access_key_id or not aws_secret_access_key:
        logging.error("Les identifiants AWS sont manquants.")
        logging.info("Veuillez les spécifier soit:")
        logging.info("1. Dans un fichier .env:")
        logging.info("   AWS_ACCESS_KEY_ID=votre_cle")
        logging.info("   AWS_SECRET_ACCESS_KEY=votre_secret")
        logging.info("2. En ligne de commande:")
        logging.info("   --aws-access-key-id VOTRE_CLE")
        logging.info("   --aws-secret-access-key VOTRE_SECRET")
        logging.info("3. Via les variables d'environnement:")
        logging.info("   export AWS_ACCESS_KEY_ID=VOTRE_CLE")
        logging.info("   export AWS_SECRET_ACCESS_KEY=VOTRE_SECRET")
        return False
    return True

def load_state(state_file):
    """
    Charge l'état de progression depuis le fichier JSON
    
    Args:
        state_file (str): Chemin du fichier d'état
        
    Returns:
        dict: État de progression
    """
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Erreur lors du chargement de l'état : {e}")
    return {
        "last_zip_processed": None,
        "processed_emls": [],
        "last_run": None
    }

def save_state(state_file, state):
    """
    Sauvegarde l'état de progression dans le fichier JSON
    
    Args:
        state_file (str): Chemin du fichier d'état
        state (dict): État de progression à sauvegarder
    """
    try:
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde de l'état : {e}")

def unzip_all_folders(source_dir, state_file):
    """
    Dézippe tous les fichiers ZIP trouvés dans le dossier source
    
    Args:
        source_dir (str): Chemin du dossier source contenant les ZIP
        state_file (str): Chemin du fichier d'état
    """
    # Charger l'état
    state = load_state(state_file)
    
    # Convertir le chemin en objet Path
    source_path = Path(source_dir)
    
    # Trier les fichiers ZIP par nom pour un traitement cohérent
    zip_files = sorted(source_path.glob('**/*.zip'))
    
    # Trouver l'index du dernier fichier traité
    start_index = 0
    if state["last_zip_processed"]:
        try:
            start_index = zip_files.index(Path(state["last_zip_processed"])) + 1
        except ValueError:
            pass
    
    logging.info(f"Début du dézippage de {len(zip_files[start_index:])} fichiers ZIP")
    
    # Parcourir les fichiers ZIP à partir du dernier traité
    for zip_file in tqdm(zip_files[start_index:], desc="Dézippage des fichiers"):
        try:
            # Créer le dossier de destination (même nom que le zip sans extension)
            dest_folder = zip_file.parent / zip_file.stem
            dest_folder.mkdir(exist_ok=True)
            
            # Dézipper le fichier
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(dest_folder)
                
            logging.info(f"Dézippé : {zip_file}")
            
            # Mettre à jour l'état
            state["last_zip_processed"] = str(zip_file)
            state["last_run"] = datetime.now().isoformat()
            save_state(state_file, state)
            
        except Exception as e:
            logging.error(f"Erreur lors du dézippage de {zip_file}: {e}")

def upload_eml_to_s3(source_dir, bucket_name, state_file, 
                    aws_access_key_id=None, aws_secret_access_key=None,
                    endpoint_url=None, region_name=None):
    """
    Upload tous les fichiers EML trouvés vers S3
    
    Args:
        source_dir (str): Chemin du dossier source contenant les EML
        bucket_name (str): Nom du bucket S3
        state_file (str): Chemin du fichier d'état
        aws_access_key_id (str): Clé d'accès AWS (optionnel)
        aws_secret_access_key (str): Clé secrète AWS (optionnel)
        endpoint_url (str): URL de l'endpoint S3 personnalisé (optionnel)
        region_name (str): Nom de la région S3 (optionnel)
    """
    # Vérifier les identifiants
    if not check_credentials(aws_access_key_id, aws_secret_access_key):
        return
    
    # Charger l'état
    state = load_state(state_file)
    
    # Configuration du client S3
    s3_config = {
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
    }
    
    # Ajouter l'endpoint personnalisé si spécifié
    if endpoint_url:
        s3_config['endpoint_url'] = endpoint_url
    
    # Ajouter la région si spécifiée
    if region_name:
        s3_config['region_name'] = region_name
    
    try:
        # Initialiser le client S3
        s3_client = boto3.client('s3', **s3_config)
        
        # Vérifier l'accès au bucket
        s3_client.head_bucket(Bucket=bucket_name)
        
    except Exception as e:
        logging.error(f"Erreur lors de la connexion à S3: {e}")
        logging.info("Veuillez vérifier:")
        logging.info("1. Les identifiants AWS sont corrects")
        logging.info("2. Le bucket existe et est accessible")
        logging.info("3. L'endpoint S3 est correct (si utilisé)")
        return
    
    # Convertir le chemin en objet Path
    source_path = Path(source_dir)
    
    # Compter le nombre total de fichiers EML à traiter
    eml_files = list(source_path.glob('**/*.eml'))
    total_files = len(eml_files)
    logging.info(f"Début de l'upload de {total_files} fichiers EML")
    
    # Parcourir tous les fichiers EML
    for eml_file in tqdm(eml_files, desc="Upload des fichiers EML"):
        # Vérifier si le fichier a déjà été traité
        if str(eml_file) in state["processed_emls"]:
            logging.info(f"Déjà traité : {eml_file}")
            continue
            
        try:
            # Créer le chemin S3 en préservant la structure des dossiers
            s3_key = str(eml_file.relative_to(source_path))
            
            # Upload le fichier
            s3_client.upload_file(
                str(eml_file),
                bucket_name,
                s3_key
            )
            
            logging.info(f"Uploadé : {eml_file} -> s3://{bucket_name}/{s3_key}")
            
            # Mettre à jour l'état
            state["processed_emls"].append(str(eml_file))
            state["last_run"] = datetime.now().isoformat()
            save_state(state_file, state)
            
        except Exception as e:
            logging.error(f"Erreur lors de l'upload de {eml_file}: {e}")

def main():
    # Parser les arguments
    args = parse_arguments()
    
    # Configurer le logging
    logger = setup_logging(args.log_file)
    
    # Charger les variables d'environnement depuis .env
    load_env()
    
    # Récupérer les identifiants (priorité aux arguments CLI)
    aws_access_key_id = args.aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = args.aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
    s3_endpoint_url = args.s3_endpoint_url or os.getenv("S3_ENDPOINT_URL")
    s3_region_name = args.s3_region_name or os.getenv("S3_REGION_NAME")
    
    logging.info("Début du traitement...")
    logging.info(f"Source directory: {args.source_dir}")
    logging.info(f"Bucket name: {args.bucket_name}")
    logging.info(f"State file: {args.state_file}")
    logging.info(f"Log file: {args.log_file}")
    logging.info(f"S3 endpoint: {s3_endpoint_url or 'AWS S3 par défaut'}")
    logging.info(f"S3 region: {s3_region_name or 'région par défaut'}")
    
    # Charger l'état actuel
    state = load_state(args.state_file)
    if state["last_run"]:
        logging.info(f"Dernière exécution : {state['last_run']}")
    
    # Étape 1 : Dézipper tous les dossiers
    logging.info("\nDézippage des dossiers...")
    unzip_all_folders(args.source_dir, args.state_file)
    
    # Étape 2 : Upload des fichiers EML vers S3
    logging.info("\nUpload des fichiers EML vers S3...")
    upload_eml_to_s3(
        args.source_dir,
        args.bucket_name,
        args.state_file,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        endpoint_url=s3_endpoint_url,
        region_name=s3_region_name
    )
    
    logging.info("\nTraitement terminé!")

if __name__ == "__main__":
    main()