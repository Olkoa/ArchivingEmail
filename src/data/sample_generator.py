"""
Sample email generator for the Okloa project.

This script generates realistic sample mailboxes for development and testing purposes.
It creates three mailboxes, each containing sent and received emails with realistic content.
"""

import os
import random
import json
import pandas as pd
import mailbox
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Any, Tuple
import re


# Define agent personas
AGENTS = [
    {
        "name": "Marie Durand",
        "email": "marie.durand@archives-vaucluse.fr",
        "role": "Conservateur en chef",
        "department": "Direction",
        "signature": "\n\nCordialement,\nMarie Durand\nConservateur en chef\nArchives départementales du Vaucluse\nTél: 04.90.86.16.18"
    },
    {
        "name": "Thomas Berger",
        "email": "thomas.berger@archives-vaucluse.fr",
        "role": "Responsable numérisation",
        "department": "Service Numérique",
        "signature": "\n\nBien cordialement,\nThomas Berger\nResponsable numérisation\nArchives départementales du Vaucluse\nTél: 04.90.86.16.20"
    },
    {
        "name": "Sophie Martin",
        "email": "sophie.martin@archives-vaucluse.fr",
        "role": "Archiviste documentaliste",
        "department": "Service des archives contemporaines",
        "signature": "\n\nCordialement,\nSophie Martin\nArchiviste documentaliste\nService des archives contemporaines\nArchives départementales du Vaucluse\nTél: 04.90.86.16.22"
    }
]

# Define external contacts
CONTACTS = [
    {"name": "Pierre Dupont", "email": "pierre.dupont@mairie-avignon.fr", "organization": "Mairie d'Avignon"},
    {"name": "Jeanne Moreau", "email": "j.moreau@departement84.fr", "organization": "Conseil Départemental du Vaucluse"},
    {"name": "Marc Lambert", "email": "m.lambert@education.gouv.fr", "organization": "Académie d'Aix-Marseille"},
    {"name": "Lucie Bernard", "email": "l.bernard@culture.gouv.fr", "organization": "DRAC PACA"},
    {"name": "Antoine Richard", "email": "a.richard@musee-calvet.org", "organization": "Musée Calvet"},
    {"name": "Christine Fabre", "email": "c.fabre@bibliotheque.avignon.fr", "organization": "Bibliothèque municipale d'Avignon"},
    {"name": "Paul Mercier", "email": "p.mercier@siaf.culture.gouv.fr", "organization": "Service Interministériel des Archives de France"},
    {"name": "Sylvie Petit", "email": "s.petit@region-sud.fr", "organization": "Région Sud PACA"}
]

# Email subjects and content templates for different types of exchanges
EMAIL_TEMPLATES = [
    # Administrative emails
    {
        "category": "administrative",
        "subjects": [
            "Réunion de service - {date}",
            "Ordre du jour - Comité technique du {date}",
            "Planification des congés d'été {year}",
            "Note de service: Procédures d'archivage électronique",
            "Modification des horaires d'ouverture",
            "Rapport d'activité {year-1} - Demande de contribution",
            "Budget prévisionnel {year+1} - Préparation",
            "Formation SIAF - Inscription avant le {date+15j}"
        ],
        "content_templates": [
            "Bonjour {recipient_first_name},\n\nJe vous informe qu'une réunion de service aura lieu le {date+7j} à 10h00 dans la salle de conférence. \n\nL'ordre du jour portera sur:\n- Bilan des activités du trimestre\n- Projets en cours et à venir\n- Questions diverses\n\nMerci de confirmer votre présence.\n{signature}",
            
            "Cher(e) collègue,\n\nVeuillez trouver ci-joint l'ordre du jour du prochain comité technique prévu le {date+10j}.\n\nJe vous rappelle que les documents préparatoires doivent être transmis au plus tard 3 jours avant la réunion.\n{signature}",
            
            "Bonjour à tous,\n\nAfin de planifier au mieux les effectifs pour la période estivale, merci de communiquer vos souhaits de congés d'été d'ici le {date+14j}.\n\nUn tableau partagé a été créé sur le serveur commun dans le dossier \"RH/Congés/{year}\".\n{signature}",
            
            "Bonjour {recipient_first_name},\n\nSuite à notre échange, pourriez-vous me transmettre votre contribution au rapport d'activité {year-1} concernant les projets menés par votre service?\n\nJ'aurais besoin de ces éléments avant le {date+7j} pour finaliser le document.\n\nMerci par avance.\n{signature}"
        ]
    },
    # Project-related emails
    {
        "category": "project",
        "subjects": [
            "Projet de numérisation - Fonds {random_project}",
            "Restauration des registres paroissiaux - Suivi",
            "Exposition \"{random_exhibition}\" - Préparation",
            "Partenariat avec {random_contact_org} - Proposition",
            "Médiation numérique - Nouveau projet",
            "Demande de devis - Prestation de numérisation",
            "Journées du Patrimoine {year} - Organisation",
            "Archivage électronique - Phase test"
        ],
        "content_templates": [
            "Bonjour {recipient_first_name},\n\nConcernant le projet de numérisation du fonds {random_project}, nous avons reçu le devis de la société prestataire. Le montant s'élève à {random_price} euros pour environ {random_number} documents.\n\nPouvons-nous en discuter lors de notre prochaine réunion?\n{signature}",
            
            "Cher(e) {recipient_name},\n\nJ'ai le plaisir de vous informer que la restauration des registres paroissiaux de la commune de {random_town} est maintenant terminée. Les documents sont à nouveau disponibles pour consultation.\n\nUn rapport détaillé de l'intervention a été déposé sur le serveur commun.\n{signature}",
            
            "Bonjour,\n\nDans le cadre de la préparation de l'exposition \"{random_exhibition}\" prévue pour {date+3mois}, pouvez-vous me confirmer la liste des documents que vous souhaitez présenter?\n\nNous devons finaliser la scénographie avec le graphiste d'ici deux semaines.\n{signature}",
            
            "Bonjour,\n\nSuite à notre réunion de la semaine dernière concernant le projet d'archivage électronique, vous trouverez en pièce jointe le compte-rendu ainsi que le calendrier prévisionnel des prochaines étapes.\n\nLa phase de test débutera le {date+1mois} avec les services pilotes.\n{signature}"
        ]
    },
    # Research assistance emails
    {
        "category": "research",
        "subjects": [
            "Recherche généalogique - Famille {random_name}",
            "Demande de consultation - Série {random_series}",
            "Renseignements sur le fonds {random_project}",
            "Reproduction de documents - Demande #{random_id}",
            "Recherche historique - {random_town} au XIXe siècle",
            "Assistance documentaire - Thèse universitaire",
            "Demande d'information - Archives communales",
            "Consultation à distance - Procédure"
        ],
        "content_templates": [
            "Bonjour {recipient_first_name},\n\nJe vous transmets la demande de M./Mme {random_contact_name} concernant des recherches généalogiques sur la famille {random_name} de {random_town}.\n\nLes actes recherchés concernent la période {random_year_past}-{random_year_past+30}. Pouvez-vous vérifier si nous disposons de ces archives?\n{signature}",
            
            "Cher(e) {recipient_name},\n\nNous avons reçu une demande de consultation pour les documents de la série {random_series}. Le chercheur souhaite consulter ces archives le {date+5j}.\n\nPourriez-vous vérifier la disponibilité de ces documents et préparer leur mise à disposition en salle de lecture?\n{signature}",
            
            "Bonjour,\n\nUn étudiant en histoire de l'Université d'Avignon travaille sur {random_town} au XIXe siècle et souhaite consulter nos fonds. Pourriez-vous lui suggérer des sources pertinentes à explorer dans nos collections?\n\nIl sera présent en salle de lecture jeudi prochain.\n{signature}",
            
            "Bonjour {recipient_first_name},\n\nSuite à la demande de reproduction #{random_id}, je vous confirme que les documents demandés ont été numérisés et sont prêts à être envoyés au demandeur.\n\nLe montant total s'élève à {random_price} euros pour {random_number} pages.\n{signature}"
        ]
    },
    # Technical emails
    {
        "category": "technical",
        "subjects": [
            "Problème d'accès au serveur - Urgence",
            "Mise à jour du logiciel de gestion d'archives",
            "Sauvegardes - Incident système",
            "Installation des nouveaux postes informatiques",
            "Migration des données - Planning",
            "Maintenance réseau - Interruption de service",
            "Problème d'impression - Service numérisation",
            "Mise en place du nouveau site web"
        ],
        "content_templates": [
            "Bonjour,\n\nNous rencontrons actuellement un problème d'accès au serveur de fichiers. Le service informatique a été alerté et travaille à la résolution du problème.\n\nEn attendant, veuillez sauvegarder vos documents localement et éviter de lancer des opérations importantes sur le réseau.\n{signature}",
            
            "Cher(e)s collègues,\n\nLa mise à jour du logiciel de gestion d'archives est programmée pour le {date+7j}. Le système sera inaccessible de 18h à 20h.\n\nUne formation sur les nouvelles fonctionnalités sera organisée la semaine suivante. Merci de vous inscrire via le lien partagé.\n{signature}",
            
            "Bonjour {recipient_first_name},\n\nSuite à l'incident système survenu hier, les sauvegardes ont été restaurées avec succès. Les fichiers sont à nouveau accessibles.\n\nMerci de vérifier que vous retrouvez bien tous vos documents et de me signaler toute anomalie.\n{signature}",
            
            "Bonjour,\n\nJe vous informe que la migration des données vers le nouveau système est planifiée pour le weekend du {date+14j}.\n\nMerci de finaliser vos saisies en cours avant cette date et d'exporter les rapports importants.\n\nUne documentation détaillée sur le nouveau système sera distribuée prochainement.\n{signature}"
        ]
    }
]

# Random data generation helpers
RANDOM_PROJECTS = [
    "Cadastre napoléonien",
    "Archives notariales",
    "Registres d'état civil",
    "Délibérations municipales",
    "Fonds photographique Duval",
    "Archives hospitalières",
    "Collection cartographique",
    "Fonds de la préfecture",
    "Archives judiciaires"
]

RANDOM_EXHIBITIONS = [
    "Vaucluse à travers les âges",
    "Trésors d'archives",
    "La vie quotidienne en Provence",
    "Guerres et paix en Vaucluse",
    "Patrimoine industriel local",
    "Les femmes dans l'histoire du département",
    "Chroniques villageoises",
    "Révolution et Empire en Vaucluse"
]

RANDOM_TOWNS = [
    "Avignon", "Carpentras", "Orange", "Apt", "Cavaillon", 
    "Bollène", "Sorgues", "Le Pontet", "Valréas", "Pertuis",
    "L'Isle-sur-la-Sorgue", "Monteux", "Vedène", "Pernes-les-Fontaines"
]

RANDOM_SERIES = ["E", "F", "J", "L", "M", "O", "P", "R", "S", "T", "X", "Z"]

RANDOM_SURNAMES = [
    "Martin", "Bernard", "Thomas", "Petit", "Robert", 
    "Richard", "Durand", "Dubois", "Moreau", "Laurent",
    "Simon", "Michel", "Lefebvre", "Leroy", "Roux",
    "David", "Bertrand", "Morel", "Fournier", "Girard"
]


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    """Generate a random date between start_date and end_date."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


def format_template(template: str, data: Dict[str, Any]) -> str:
    """Format template with variables."""
    # Process special date formats like {date+7j}
    date_patterns = re.findall(r'{date\+(\d+)j}', template)
    for days in date_patterns:
        days_int = int(days)
        future_date = (data['date'] + timedelta(days=days_int)).strftime('%d/%m/%Y')
        template = template.replace(f'{{date+{days}j}}', future_date)
    
    # Process special date formats like {date+3mois}
    month_patterns = re.findall(r'{date\+(\d+)mois}', template)
    for months in month_patterns:
        months_int = int(months)
        future_date = (data['date'] + timedelta(days=months_int*30)).strftime('%B %Y')
        template = template.replace(f'{{date+{months}mois}}', future_date)
    
    # Process year patterns
    if '{year}' in template:
        template = template.replace('{year}', str(data['date'].year))
    if '{year+1}' in template:
        template = template.replace('{year+1}', str(data['date'].year + 1))
    if '{year-1}' in template:
        template = template.replace('{year-1}', str(data['date'].year - 1))
    
    # Simple date formatting
    if '{date}' in template:
        template = template.replace('{date}', data['date'].strftime('%d/%m/%Y'))
    
    # Process other random variables
    if '{random_project}' in template:
        template = template.replace('{random_project}', random.choice(RANDOM_PROJECTS))
    if '{random_exhibition}' in template:
        template = template.replace('{random_exhibition}', random.choice(RANDOM_EXHIBITIONS))
    if '{random_town}' in template:
        template = template.replace('{random_town}', random.choice(RANDOM_TOWNS))
    if '{random_name}' in template:
        template = template.replace('{random_name}', random.choice(RANDOM_SURNAMES))
    if '{random_series}' in template:
        template = template.replace('{random_series}', random.choice(RANDOM_SERIES))
    if '{random_contact_name}' in template:
        contact = random.choice(CONTACTS)
        template = template.replace('{random_contact_name}', contact['name'])
    if '{random_contact_org}' in template:
        contact = random.choice(CONTACTS)
        template = template.replace('{random_contact_org}', contact['organization'])
    if '{random_price}' in template:
        template = template.replace('{random_price}', str(random.randint(50, 1000)))
    if '{random_number}' in template:
        template = template.replace('{random_number}', str(random.randint(10, 500)))
    if '{random_id}' in template:
        template = template.replace('{random_id}', f"REP-{random.randint(1000, 9999)}")
    # Process year past+X patterns
    if '{random_year_past}' in template:
        random_year = random.randint(1800, 1900)
        template = template.replace('{random_year_past}', str(random_year))
        # Replace any patterns like {random_year_past+30}
        year_plus_patterns = re.findall(r'{random_year_past\+(\d+)}', template)
        for years in year_plus_patterns:
            years_int = int(years)
            template = template.replace(f'{{random_year_past+{years}}}', str(random_year + years_int))
    
    # Regular formatting
    return template.format(**data)


def generate_email(sender: Dict[str, str], recipient: Dict[str, str], 
                  date: datetime, category: str = None) -> Tuple[str, str, str]:
    """
    Generate a realistic email between sender and recipient.
    
    Args:
        sender: Sender information dictionary
        recipient: Recipient information dictionary
        date: Date of the email
        category: Optional category to filter templates
        
    Returns:
        Tuple containing (subject, body, direction)
    """
    # Select random category if not specified
    if not category:
        category = random.choice([t["category"] for t in EMAIL_TEMPLATES])
    
    # Get templates for the category
    templates = next((t for t in EMAIL_TEMPLATES if t["category"] == category), 
                     random.choice(EMAIL_TEMPLATES))
    
    # Select random subject and content template
    subject_template = random.choice(templates["subjects"])
    content_template = random.choice(templates["content_templates"])
    
    # Prepare data for template formatting
    data = {
        "date": date,
        "sender_name": sender["name"],
        "sender_first_name": sender["name"].split()[0],
        "recipient_name": recipient["name"],
        "recipient_first_name": recipient["name"].split()[0],
        "signature": sender.get("signature", "")
    }
    
    # Format subject and content
    subject = format_template(subject_template, data)
    body = format_template(content_template, data)
    
    # Determine email direction (internal emails can be both sent and received)
    if sender["email"].endswith("@archives-vaucluse.fr"):
        direction = "sent"
    else:
        direction = "received"
    
    return subject, body, direction


def create_email_message(from_addr: str, to_addr: str, subject: str, 
                         body: str, date: datetime) -> EmailMessage:
    """
    Create an email.message.EmailMessage object.
    
    Args:
        from_addr: Sender email address
        to_addr: Recipient email address
        subject: Email subject
        body: Email body
        date: Email date
        
    Returns:
        EmailMessage object
    """
    msg = EmailMessage()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg['Date'] = formatdate(date.timestamp())
    msg['Message-ID'] = make_msgid(domain="archives-vaucluse.fr")
    msg.set_content(body)
    
    return msg


def generate_mailbox(agent: Dict[str, str], num_sent: int = 5, 
                    num_received: int = 5, start_date: datetime = None, 
                    end_date: datetime = None) -> List[Tuple[EmailMessage, str]]:
    """
    Generate a mailbox for an agent with sent and received emails.
    
    Args:
        agent: Agent information dictionary
        num_sent: Number of sent emails to generate
        num_received: Number of received emails to generate
        start_date: Start date for email generation
        end_date: End date for email generation
        
    Returns:
        List of (EmailMessage, direction) tuples
    """
    if not start_date:
        start_date = datetime(2023, 1, 1, tzinfo=pytz.UTC)
    if not end_date:
        end_date = datetime(2023, 12, 31, tzinfo=pytz.UTC)
    
    emails = []
    
    # Generate sent emails
    for _ in range(num_sent):
        recipient = random.choice(CONTACTS)
        date = random_date(start_date, end_date)
        try:
            subject, body, _ = generate_email(agent, recipient, date)
        except Exception as e:
            print(f"Error generating sent email: {e}")
            # Use some default values
            subject = "Default sent email subject"
            body = "Default sent email body"
            
        msg = create_email_message(
            f"{agent['name']} <{agent['email']}>",
            f"{recipient['name']} <{recipient['email']}>",
            subject, 
            body,
            date
        )
        
        emails.append((msg, "sent"))
    
    # Generate received emails
    for _ in range(num_received):
        sender = random.choice(CONTACTS)
        date = random_date(start_date, end_date)
        try:
            subject, body, _ = generate_email(sender, agent, date)
        except Exception as e:
            print(f"Error generating email: {e}")
            # Use some default values
            subject = "Default subject"
            body = "Default body text"
            
        msg = create_email_message(
            f"{sender['name']} <{sender['email']}>",
            f"{agent['name']} <{agent['email']}>",
            subject, 
            body,
            date
        )
        
        emails.append((msg, "received"))
    
    # Sort by date
    emails.sort(key=lambda x: x[0]['Date'])
    
    return emails


def save_as_mbox(mailbox_name: str, emails: List[Tuple[EmailMessage, str]], 
                output_dir: str) -> str:
    """
    Save emails to an mbox file.
    
    Args:
        mailbox_name: Name for the mailbox
        emails: List of (EmailMessage, direction) tuples
        output_dir: Output directory
        
    Returns:
        Path to the created mbox file
    """
    # Create output directory if it doesn't exist
    mailbox_dir = os.path.join(output_dir, mailbox_name)
    os.makedirs(mailbox_dir, exist_ok=True)
    
    # Create mbox file
    mbox_path = os.path.join(mailbox_dir, "emails.mbox")
    mbox_file = mailbox.mbox(mbox_path)
    
    # Add messages to mbox
    for msg, _ in emails:
        mbox_file.add(msg)
    
    mbox_file.flush()
    
    # Create metadata file for easy reference
    metadata = [
        {
            "id": idx,
            "date": msg["Date"],
            "from": msg["From"],
            "to": msg["To"],
            "subject": msg["Subject"],
            "direction": direction
        }
        for idx, (msg, direction) in enumerate(emails)
    ]
    
    metadata_path = os.path.join(mailbox_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return mbox_path


def save_as_eml(mailbox_name: str, emails: List[Tuple[EmailMessage, str]], 
               output_dir: str) -> str:
    """
    Save emails as individual .eml files.
    
    Args:
        mailbox_name: Name for the mailbox
        emails: List of (EmailMessage, direction) tuples
        output_dir: Output directory
        
    Returns:
        Path to the created eml directory
    """
    # Create output directories
    mailbox_dir = os.path.join(output_dir, mailbox_name)
    eml_dir = os.path.join(mailbox_dir, "eml")
    os.makedirs(eml_dir, exist_ok=True)
    
    # Save individual .eml files
    for idx, (msg, direction) in enumerate(emails):
        # Create subdirectories for sent and received
        subdir = os.path.join(eml_dir, direction)
        os.makedirs(subdir, exist_ok=True)
        
        # Save as .eml file
        eml_path = os.path.join(subdir, f"{idx:04d}.eml")
        with open(eml_path, 'wb') as f:
            f.write(msg.as_bytes())
    
    # Create metadata file for easy reference
    metadata = [
        {
            "id": idx,
            "date": msg["Date"],
            "from": msg["From"],
            "to": msg["To"],
            "subject": msg["Subject"],
            "direction": direction,
            "path": f"eml/{direction}/{idx:04d}.eml"
        }
        for idx, (msg, direction) in enumerate(emails)
    ]
    
    metadata_path = os.path.join(mailbox_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return eml_dir


def generate_test_mailboxes(output_dir: str,
                           num_sent: int = 5, num_received: int = 5,
                           format_type: str = "mbox") -> None:
    """
    Generate test mailbox data for the three agents.
    
    Args:
        output_dir: Directory where the test mailboxes should be created
        num_sent: Number of sent emails per agent
        num_received: Number of received emails per agent
        format_type: Format to save emails ('mbox' or 'eml')
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate mailboxes for each agent
    for idx, agent in enumerate(AGENTS):
        mailbox_name = f"mailbox_{idx+1}"
        
        # Generate emails for this agent
        emails = generate_mailbox(
            agent, 
            num_sent=num_sent, 
            num_received=num_received,
            start_date=datetime(2023, 1, 1, tzinfo=pytz.UTC),
            end_date=datetime(2023, 12, 31, tzinfo=pytz.UTC)
        )
        
        # Save in the requested format
        if format_type.lower() == "mbox":
            save_as_mbox(mailbox_name, emails, output_dir)
        elif format_type.lower() == "eml":
            save_as_eml(mailbox_name, emails, output_dir)
        else:
            print(f"Unknown format type: {format_type}")
            return
        
        print(f"Generated {len(emails)} emails for {agent['name']} ({mailbox_name})")


if __name__ == "__main__":
    # Example usage
    import os
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "data", "raw"))
    generate_test_mailboxes(output_dir=output_dir, num_sent=5, num_received=5, format_type="mbox")
    print("Sample mailboxes generated successfully")