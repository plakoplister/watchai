"""
WATCHAI Logger System
Module de logging pour tracer les connexions et l'utilisation de la webapp
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import streamlit as st
import hashlib
import socket

class WatchAILogger:
    def __init__(self, logs_dir="./logs"):
        """Initialise le système de logging WATCHAI"""
        self.logs_dir = Path(logs_dir)
        try:
            self.logs_dir.mkdir(exist_ok=True)
        except (PermissionError, OSError):
            # Fallback to current directory if can't create logs dir
            self.logs_dir = Path(".")

        # Fichiers de logs
        self.access_log_file = self.logs_dir / "access.log"
        self.session_log_file = self.logs_dir / "sessions.json"
        self.activity_log_file = self.logs_dir / "activity.log"

        # Configuration du logger principal
        self.setup_logging()

        # Initialiser le fichier de sessions s'il n'existe pas
        try:
            if not self.session_log_file.exists():
                with open(self.session_log_file, 'w', encoding='utf-8') as f:
                    json.dump({"sessions": []}, f, indent=2)
        except (PermissionError, OSError):
            # Ignorer si impossible de créer le fichier
            pass

    def setup_logging(self):
        """Configure le logging system"""
        try:
            # Logger pour les accès
            self.access_logger = logging.getLogger('watchai_access')
            self.access_logger.setLevel(logging.INFO)

            # Handler pour fichier d'accès
            access_handler = logging.FileHandler(self.access_log_file, encoding='utf-8')
            access_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            access_handler.setFormatter(access_formatter)

            # Éviter les doublons
            if not self.access_logger.handlers:
                self.access_logger.addHandler(access_handler)

            # Logger pour l'activité
            self.activity_logger = logging.getLogger('watchai_activity')
            self.activity_logger.setLevel(logging.INFO)

            # Handler pour fichier d'activité
            activity_handler = logging.FileHandler(self.activity_log_file, encoding='utf-8')
            activity_handler.setFormatter(access_formatter)

            if not self.activity_logger.handlers:
                self.activity_logger.addHandler(activity_handler)

        except (PermissionError, OSError):
            # Fallback to console logging if file logging fails
            self.access_logger = logging.getLogger('watchai_access_console')
            self.activity_logger = logging.getLogger('watchai_activity_console')
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
            console_handler.setFormatter(console_formatter)

            if not self.access_logger.handlers:
                self.access_logger.addHandler(console_handler)
            if not self.activity_logger.handlers:
                self.activity_logger.addHandler(console_handler)

    def get_client_info(self):
        """Récupère les informations du client"""
        try:
            # Informations de la session Streamlit
            session_info = st.session_state.get('session_info', {})

            # Tentative de récupération de l'IP (limitée dans Streamlit Cloud)
            client_ip = "unknown"
            try:
                client_ip = st.get_option("server.address") or "localhost"
            except:
                pass

            # User agent approximatif basé sur les headers disponibles
            user_agent = "Streamlit Client"

            # ID de session unique basé sur le timestamp et des données Streamlit
            session_data = str(datetime.now()) + str(hash(str(st.session_state)))
            session_id = hashlib.md5(session_data.encode()).hexdigest()[:12]

            return {
                "session_id": session_id,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "timestamp": datetime.now().isoformat(),
                "hostname": socket.gethostname()
            }
        except Exception as e:
            return {
                "session_id": "error",
                "client_ip": "unknown",
                "user_agent": "unknown",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "hostname": socket.gethostname()
            }

    def log_access(self, page="webapp_volumes_reels", action="page_load"):
        """Log un accès à la webapp"""
        client_info = self.get_client_info()

        log_message = (
            f"ACCESS | Page: {page} | Action: {action} | "
            f"Session: {client_info['session_id']} | "
            f"IP: {client_info['client_ip']} | "
            f"Host: {client_info['hostname']}"
        )

        self.access_logger.info(log_message)

        # Sauvegarder aussi dans le fichier JSON des sessions
        self.save_session_data(client_info, page, action)

    def log_activity(self, activity, details=""):
        """Log une activité utilisateur"""
        client_info = self.get_client_info()

        log_message = (
            f"ACTIVITY | {activity} | "
            f"Session: {client_info['session_id']} | "
            f"Details: {details} | "
            f"Host: {client_info['hostname']}"
        )

        self.activity_logger.info(log_message)

    def save_session_data(self, client_info, page, action):
        """Sauvegarde les données de session dans le fichier JSON"""
        try:
            # Lire les données existantes
            try:
                with open(self.session_log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {"sessions": []}

            # Ajouter la nouvelle session
            session_entry = {
                "timestamp": client_info['timestamp'],
                "session_id": client_info['session_id'],
                "client_ip": client_info['client_ip'],
                "hostname": client_info['hostname'],
                "page": page,
                "action": action,
                "user_agent": client_info['user_agent']
            }

            data["sessions"].append(session_entry)

            # Garder seulement les 1000 dernières sessions pour éviter un fichier trop volumineux
            if len(data["sessions"]) > 1000:
                data["sessions"] = data["sessions"][-1000:]

            # Sauvegarder
            with open(self.session_log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            # Log vers la console si le logger n'est pas disponible
            print(f"Erreur sauvegarde session: {str(e)}")

    def get_recent_sessions(self, limit=50):
        """Récupère les sessions récentes"""
        try:
            with open(self.session_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data["sessions"][-limit:] if data.get("sessions") else []
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            return []

    def get_session_stats(self):
        """Statistiques des sessions"""
        try:
            sessions = self.get_recent_sessions(1000)
            if not sessions:
                return {"total": 0, "today": 0, "unique_ips": 0}

            today = datetime.now().strftime("%Y-%m-%d")
            today_sessions = [s for s in sessions if s["timestamp"].startswith(today)]
            unique_ips = len(set(s["client_ip"] for s in sessions))

            return {
                "total": len(sessions),
                "today": len(today_sessions),
                "unique_ips": unique_ips,
                "last_access": sessions[-1]["timestamp"] if sessions else "N/A"
            }
        except:
            return {"total": 0, "today": 0, "unique_ips": 0, "last_access": "N/A"}

# Instance globale du logger
watchai_logger = WatchAILogger()