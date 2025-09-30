"""
Script de synchronisation automatique des données WATCHAI
Synchronise les données entre la base locale et le service cloud
"""

import shutil
import os
from pathlib import Path
from datetime import datetime
import logging

# Configuration des chemins
LOCAL_DB_PATH = Path("../Master_Data/DB_Shipping_Master.xlsx")
WEBAPP_DB_PATH = Path("DB_Shipping_Master.xlsx")
BACKUP_DIR = Path("backups")

def setup_logging():
    """Configure le système de logging pour la synchronisation"""
    log_dir = Path("logs")
    try:
        log_dir.mkdir(exist_ok=True)
    except (PermissionError, OSError):
        log_dir = Path(".")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "db_sync.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def create_backup():
    """Crée une sauvegarde de la base actuelle"""
    try:
        BACKUP_DIR.mkdir(exist_ok=True)

        if WEBAPP_DB_PATH.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = BACKUP_DIR / f"DB_Shipping_Master_backup_{timestamp}.xlsx"
            shutil.copy2(WEBAPP_DB_PATH, backup_file)
            logging.info(f"Sauvegarde créée: {backup_file}")
            return backup_file
    except Exception as e:
        logging.error(f"Erreur lors de la création de la sauvegarde: {e}")
    return None

def sync_database():
    """Synchronise la base de données locale vers le webapp"""
    try:
        # Vérifier l'existence du fichier source
        if not LOCAL_DB_PATH.exists():
            logging.error(f"Fichier source introuvable: {LOCAL_DB_PATH}")
            return False

        # Créer une sauvegarde avant synchronisation
        backup_file = create_backup()

        # Obtenir les dates de modification
        local_mtime = LOCAL_DB_PATH.stat().st_mtime
        webapp_mtime = WEBAPP_DB_PATH.stat().st_mtime if WEBAPP_DB_PATH.exists() else 0

        # Vérifier si la synchronisation est nécessaire
        if local_mtime <= webapp_mtime:
            logging.info("La base webapp est déjà à jour")
            return True

        # Copier le fichier
        shutil.copy2(LOCAL_DB_PATH, WEBAPP_DB_PATH)

        local_time = datetime.fromtimestamp(local_mtime).strftime("%Y-%m-%d %H:%M:%S")
        webapp_time = datetime.fromtimestamp(WEBAPP_DB_PATH.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        logging.info(f"Synchronisation réussie!")
        logging.info(f"Fichier source (local): {LOCAL_DB_PATH} - Modifié: {local_time}")
        logging.info(f"Fichier destination (webapp): {WEBAPP_DB_PATH} - Modifié: {webapp_time}")

        return True

    except Exception as e:
        logging.error(f"Erreur lors de la synchronisation: {e}")
        return False

def auto_sync_check():
    """Vérifie automatiquement si une synchronisation est nécessaire"""
    # DÉSACTIVÉ - Une seule source de données maintenant dans Master_Data/
    # La webapp accède directement à ../Master_Data/DB_Shipping_Master.xlsx
    return True

def cleanup_old_backups(max_backups=10):
    """Nettoie les anciennes sauvegardes"""
    try:
        if not BACKUP_DIR.exists():
            return

        backup_files = list(BACKUP_DIR.glob("DB_Shipping_Master_backup_*.xlsx"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if len(backup_files) > max_backups:
            for backup_file in backup_files[max_backups:]:
                backup_file.unlink()
                logging.info(f"Ancienne sauvegarde supprimée: {backup_file}")

    except Exception as e:
        logging.error(f"Erreur lors du nettoyage des sauvegardes: {e}")

if __name__ == "__main__":
    setup_logging()
    logging.info("=== Démarrage de la synchronisation WATCHAI ===")

    success = sync_database()
    if success:
        cleanup_old_backups()
        logging.info("=== Synchronisation terminée avec succès ===")
    else:
        logging.error("=== Synchronisation échouée ===")