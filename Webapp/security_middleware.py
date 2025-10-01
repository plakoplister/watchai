"""
WATCHAI Security Middleware
Rate limiting, Session timeout, and CAPTCHA protection
"""

import streamlit as st
from datetime import datetime, timedelta
import json
from pathlib import Path
import hashlib
import random
import string

class SecurityMiddleware:
    def __init__(self):
        self.security_log_file = Path("./logs/security.json")
        self.security_log_file.parent.mkdir(exist_ok=True)

        # Configuration
        self.RATE_LIMIT_REQUESTS = 100  # Max requêtes par heure
        self.RATE_LIMIT_WINDOW = 3600  # Fenêtre de 1 heure en secondes
        self.SESSION_TIMEOUT = 1800  # 30 minutes d'inactivité
        self.MAX_LOGIN_ATTEMPTS = 3  # Tentatives avant CAPTCHA
        self.CAPTCHA_LENGTH = 6

        # Initialiser le fichier de log si nécessaire
        if not self.security_log_file.exists():
            self._init_security_log()

    def _init_security_log(self):
        """Initialise le fichier de log de sécurité"""
        try:
            with open(self.security_log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "rate_limits": {},
                    "login_attempts": {},
                    "captcha_challenges": {},
                    "blocked_sessions": []
                }, f, indent=2)
        except:
            pass

    def _load_security_log(self):
        """Charge les données de sécurité"""
        try:
            with open(self.security_log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                "rate_limits": {},
                "login_attempts": {},
                "captcha_challenges": {},
                "blocked_sessions": []
            }

    def _save_security_log(self, data):
        """Sauvegarde les données de sécurité"""
        try:
            with open(self.security_log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def check_rate_limit(self, session_id):
        """
        Vérifie si l'utilisateur a dépassé la limite de requêtes
        Returns: (allowed: bool, remaining: int, reset_time: str)
        """
        data = self._load_security_log()
        rate_limits = data.get("rate_limits", {})

        now = datetime.now()
        current_time = now.timestamp()

        if session_id not in rate_limits:
            rate_limits[session_id] = {
                "requests": [],
                "first_request": now.isoformat()
            }

        # Nettoyer les anciennes requêtes hors de la fenêtre
        rate_limits[session_id]["requests"] = [
            req_time for req_time in rate_limits[session_id]["requests"]
            if current_time - req_time < self.RATE_LIMIT_WINDOW
        ]

        # Vérifier la limite
        request_count = len(rate_limits[session_id]["requests"])

        if request_count >= self.RATE_LIMIT_REQUESTS:
            # Calculer le temps de reset
            oldest_request = min(rate_limits[session_id]["requests"])
            reset_time = datetime.fromtimestamp(oldest_request + self.RATE_LIMIT_WINDOW)

            return False, 0, reset_time.strftime("%H:%M:%S")

        # Ajouter la requête actuelle
        rate_limits[session_id]["requests"].append(current_time)

        # Sauvegarder
        data["rate_limits"] = rate_limits
        self._save_security_log(data)

        remaining = self.RATE_LIMIT_REQUESTS - len(rate_limits[session_id]["requests"])
        return True, remaining, ""

    def check_session_timeout(self):
        """
        Vérifie si la session a expiré par inactivité
        Returns: bool (True si session valide, False si expirée)
        """
        if 'last_activity' not in st.session_state:
            st.session_state.last_activity = datetime.now()
            return True

        last_activity = st.session_state.last_activity
        now = datetime.now()

        # Vérifier si le timeout est dépassé
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)

        time_diff = (now - last_activity).total_seconds()

        if time_diff > self.SESSION_TIMEOUT:
            return False

        # Mettre à jour l'activité
        st.session_state.last_activity = now
        return True

    def track_login_attempt(self, username, success=True):
        """
        Enregistre une tentative de connexion
        Returns: (needs_captcha: bool, attempts: int)
        """
        data = self._load_security_log()
        login_attempts = data.get("login_attempts", {})

        now = datetime.now()
        current_time = now.timestamp()

        if username not in login_attempts:
            login_attempts[username] = {
                "failed_attempts": [],
                "last_success": None
            }

        if success:
            # Reset les tentatives échouées
            login_attempts[username]["failed_attempts"] = []
            login_attempts[username]["last_success"] = now.isoformat()
            needs_captcha = False
            attempts = 0
        else:
            # Nettoyer les tentatives de plus d'1 heure
            login_attempts[username]["failed_attempts"] = [
                attempt_time for attempt_time in login_attempts[username]["failed_attempts"]
                if current_time - attempt_time < 3600
            ]

            # Ajouter l'échec
            login_attempts[username]["failed_attempts"].append(current_time)

            attempts = len(login_attempts[username]["failed_attempts"])
            needs_captcha = attempts >= self.MAX_LOGIN_ATTEMPTS

        # Sauvegarder
        data["login_attempts"] = login_attempts
        self._save_security_log(data)

        return needs_captcha, attempts

    def generate_captcha(self):
        """
        Génère un CAPTCHA simple (texte)
        Returns: captcha_text
        """
        captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=self.CAPTCHA_LENGTH))

        # Stocker dans la session
        st.session_state.captcha_text = captcha_text
        st.session_state.captcha_generated_at = datetime.now().isoformat()

        return captcha_text

    def verify_captcha(self, user_input):
        """
        Vérifie le CAPTCHA
        Returns: bool
        """
        if 'captcha_text' not in st.session_state:
            return False

        # Vérifier l'expiration (5 minutes)
        if 'captcha_generated_at' in st.session_state:
            generated_at = datetime.fromisoformat(st.session_state.captcha_generated_at)
            if (datetime.now() - generated_at).total_seconds() > 300:
                return False

        # Vérification insensible à la casse
        return user_input.upper() == st.session_state.captcha_text.upper()

    def display_captcha(self):
        """Affiche le CAPTCHA dans l'interface Streamlit"""
        if 'captcha_text' not in st.session_state or st.session_state.get('regenerate_captcha', False):
            captcha = self.generate_captcha()
            st.session_state.regenerate_captcha = False
        else:
            captcha = st.session_state.captcha_text

        # Affichage stylisé du CAPTCHA
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px; border-radius: 8px; text-align: center; margin: 10px 0;'>
            <p style='color: white; margin: 0; font-size: 12px;'>Vérification de sécurité</p>
            <p style='color: white; font-size: 32px; font-weight: bold; letter-spacing: 8px;
                      font-family: monospace; margin: 10px 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
                {captcha}
            </p>
        </div>
        """, unsafe_allow_html=True)

        return captcha

    def get_session_id(self):
        """Génère ou récupère l'ID de session"""
        if 'security_session_id' not in st.session_state:
            # Créer un ID unique basé sur timestamp + random
            session_data = str(datetime.now()) + ''.join(random.choices(string.ascii_letters, k=10))
            st.session_state.security_session_id = hashlib.md5(session_data.encode()).hexdigest()[:16]

        return st.session_state.security_session_id

    def reset_session(self):
        """Réinitialise les données de session de sécurité"""
        keys_to_reset = [
            'security_session_id', 'last_activity', 'captcha_text',
            'captcha_generated_at', 'regenerate_captcha'
        ]
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]

    def get_rate_limit_info(self, session_id):
        """
        Récupère les informations de rate limiting pour affichage
        Returns: dict avec infos
        """
        data = self._load_security_log()
        rate_limits = data.get("rate_limits", {})

        if session_id not in rate_limits:
            return {
                "total_requests": 0,
                "limit": self.RATE_LIMIT_REQUESTS,
                "remaining": self.RATE_LIMIT_REQUESTS
            }

        now = datetime.now().timestamp()

        # Compter les requêtes dans la fenêtre actuelle
        valid_requests = [
            req_time for req_time in rate_limits[session_id]["requests"]
            if now - req_time < self.RATE_LIMIT_WINDOW
        ]

        return {
            "total_requests": len(valid_requests),
            "limit": self.RATE_LIMIT_REQUESTS,
            "remaining": max(0, self.RATE_LIMIT_REQUESTS - len(valid_requests))
        }

# Instance globale
security_middleware = SecurityMiddleware()
