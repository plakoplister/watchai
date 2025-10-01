"""
WATCHAI - Data Watermarking System
Système de watermarking invisible pour tracer les fuites de données
"""

import pandas as pd
import numpy as np
import hashlib
import streamlit as st

class DataWatermarking:
    def __init__(self):
        # Configuration du watermarking
        self.ADMIN_USER = "Julien"  # Admin voit les données exactes
        self.NOISE_PERCENTAGE = 0.003  # ±0.3% de bruit (invisible à l'œil)
        self.MIN_NOISE = 0.001  # Minimum 0.1%
        self.MAX_NOISE = 0.005  # Maximum 0.5%

        # Colonnes à watermarker (colonnes numériques sensibles)
        self.WATERMARK_COLUMNS = [
            'POIDS_TONNES',
            'PDSNET'
        ]

    def get_user_seed(self, username):
        """
        Génère un seed unique et déterministe pour chaque utilisateur
        Le même utilisateur aura toujours le même bruit
        """
        if username == self.ADMIN_USER:
            return None  # Admin = pas de watermark

        # Hash du username pour générer un seed stable
        hash_object = hashlib.sha256(username.encode())
        seed = int(hash_object.hexdigest(), 16) % (2**32 - 1)
        return seed

    def apply_watermark(self, df, username):
        """
        Applique un watermark invisible aux données

        Args:
            df: DataFrame original
            username: Nom de l'utilisateur

        Returns:
            DataFrame watermarké (ou original si admin)
        """
        # Si admin, retourner les données exactes
        if username == self.ADMIN_USER:
            return df.copy()

        # Copier le dataframe pour ne pas modifier l'original
        df_watermarked = df.copy()

        # Générer le seed utilisateur
        seed = self.get_user_seed(username)
        np.random.seed(seed)

        # Appliquer le watermark sur chaque colonne numérique
        for col in self.WATERMARK_COLUMNS:
            if col in df_watermarked.columns:
                # Générer un facteur de bruit unique pour cette colonne
                # Chaque valeur aura un bruit légèrement différent mais déterministe
                n_rows = len(df_watermarked)

                # Créer un bruit gaussien centré sur 0
                noise_factors = np.random.normal(0, self.NOISE_PERCENTAGE, n_rows)

                # Clipper pour éviter des variations trop importantes
                noise_factors = np.clip(noise_factors, -self.MAX_NOISE, self.MAX_NOISE)

                # Appliquer le bruit multiplicatif
                df_watermarked[col] = df_watermarked[col] * (1 + noise_factors)

        # Logger le watermarking
        self._log_watermark(username, len(df_watermarked))

        return df_watermarked

    def apply_watermark_to_value(self, value, username, identifier=""):
        """
        Applique un watermark à une valeur unique

        Args:
            value: Valeur numérique à watermarker
            username: Nom de l'utilisateur
            identifier: Identifiant unique pour cette valeur (pour cohérence)

        Returns:
            Valeur watermarkée
        """
        # Si admin, retourner la valeur exacte
        if username == self.ADMIN_USER:
            return value

        # Générer un seed basé sur username + identifier
        seed_string = f"{username}_{identifier}"
        hash_object = hashlib.sha256(seed_string.encode())
        seed = int(hash_object.hexdigest(), 16) % (2**32 - 1)

        np.random.seed(seed)
        noise_factor = np.random.normal(0, self.NOISE_PERCENTAGE)
        noise_factor = np.clip(noise_factor, -self.MAX_NOISE, self.MAX_NOISE)

        return value * (1 + noise_factor)

    def _log_watermark(self, username, n_rows):
        """Log l'application du watermark"""
        try:
            from watchai_logger import watchai_logger
            watchai_logger.log_activity(
                "data_watermark",
                f"Applied watermark for user {username} on {n_rows} rows"
            )
        except:
            pass

    def verify_watermark(self, df, username, original_df):
        """
        Vérifie si un dataframe a été watermarké par un utilisateur spécifique
        Utile pour tracer les fuites

        Args:
            df: DataFrame suspect
            username: Nom de l'utilisateur suspecté
            original_df: DataFrame original

        Returns:
            dict avec score de correspondance et détails
        """
        seed = self.get_user_seed(username)
        if seed is None:
            return {"match": False, "score": 0, "reason": "Admin user - no watermark"}

        # Régénérer le watermark pour cet utilisateur
        df_expected = self.apply_watermark(original_df, username)

        # Comparer les valeurs
        matches = 0
        total = 0

        for col in self.WATERMARK_COLUMNS:
            if col in df.columns and col in df_expected.columns:
                # Calculer la différence relative
                diff = np.abs((df[col] - df_expected[col]) / df_expected[col])
                matches += (diff < 0.0001).sum()  # Tolérance de 0.01%
                total += len(df)

        score = matches / total if total > 0 else 0

        return {
            "match": score > 0.95,  # 95% de correspondance = match
            "score": score,
            "username": username,
            "confidence": "HIGH" if score > 0.95 else "MEDIUM" if score > 0.80 else "LOW"
        }

    def get_watermark_info(self, username):
        """
        Retourne les informations sur le watermarking pour un utilisateur
        Utile pour affichage admin
        """
        if username == self.ADMIN_USER:
            return {
                "enabled": False,
                "user": username,
                "type": "ADMIN - No watermark",
                "noise_level": "0%"
            }

        seed = self.get_user_seed(username)
        return {
            "enabled": True,
            "user": username,
            "type": "Invisible data fingerprinting",
            "noise_level": f"±{self.NOISE_PERCENTAGE * 100:.1f}%",
            "seed": seed,
            "description": "Données légèrement modifiées pour traçabilité"
        }

# Instance globale
watermarking = DataWatermarking()


# Fonction helper pour Streamlit
def get_watermarked_data(df, username=None):
    """
    Helper function pour watermarker facilement dans Streamlit

    Usage:
        df_display = get_watermarked_data(df, st.session_state.username)
        st.dataframe(df_display)
    """
    if username is None:
        # Essayer de récupérer depuis session_state
        if hasattr(st, 'session_state') and 'username' in st.session_state:
            username = st.session_state.username
        else:
            # Pas de session, retourner données exactes (ne devrait pas arriver)
            return df

    return watermarking.apply_watermark(df, username)
