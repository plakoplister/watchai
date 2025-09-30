#!/usr/bin/env python3
"""
Script de test pour simuler des connexions de différents utilisateurs
"""

from auth_config import log_connection
from datetime import datetime
import time

def test_multiple_connections():
    """Simule plusieurs connexions"""
    print("=== Test de connexions multiples ===\n")

    # Simuler une connexion de Julien
    log_connection("Julien", success=True)
    print(f"Connexion de Julien à {datetime.now().strftime('%H:%M:%S')}")
    time.sleep(1)

    # Simuler une connexion d'Erick
    log_connection("Erick", success=True)
    print(f"Connexion d'Erick à {datetime.now().strftime('%H:%M:%S')}")
    time.sleep(1)

    # Simuler une autre connexion de Jean
    log_connection("Jean", success=True)
    print(f"Connexion de Jean à {datetime.now().strftime('%H:%M:%S')}")

    print("\nTest terminé!")
    print("Vérifiez l'interface admin sur http://localhost:8524")

if __name__ == "__main__":
    test_multiple_connections()