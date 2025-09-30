#!/usr/bin/env python3
"""
Script de test pour simuler une connexion de Jean
et vérifier le système de logs
"""

from auth_config import log_connection, get_connection_stats
from datetime import datetime
import json

def test_jean_connection():
    """Simule une connexion de Jean"""
    print("=== Test de connexion de Jean ===")

    # Simuler une connexion réussie de Jean
    log_connection("Jean", success=True)
    print(f"Connexion de Jean enregistrée à {datetime.now().strftime('%H:%M:%S')}")

    # Récupérer les statistiques
    stats = get_connection_stats()

    print("\nStatistiques actuelles:")
    print(f"- Total des connexions: {stats['total_connections']}")
    print(f"- Utilisateurs uniques: {stats['unique_users']}")
    print(f"- Connexions par utilisateur:")
    for user, count in stats['connections_by_user'].items():
        print(f"  - {user}: {count} connexion(s)")

    # Afficher les dernières connexions
    print("\nDernières connexions:")
    for log in stats['last_connections'][:5]:
        timestamp = datetime.fromisoformat(log['timestamp'])
        print(f"  - {log['username']} - {timestamp.strftime('%d/%m/%Y %H:%M:%S')}")

    print("\nTest terminé avec succès!")
    print("Vous pouvez maintenant vérifier dans l'interface admin (port 8524)")
    print("dans l'onglet 'Suivi Jean' pour voir les connexions de Jean")

if __name__ == "__main__":
    test_jean_connection()