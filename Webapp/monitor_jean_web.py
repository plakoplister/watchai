#!/usr/bin/env python3
"""
WATCHAI - Surveillance des connexions de Jean sur l'application Web
Ce script surveille automatiquement si Jean se connecte sur l'app Streamlit Cloud
"""

import time
from datetime import datetime
from pathlib import Path
import json
from watchai_logger import watchai_logger

def check_jean_connections():
    """
    Vérifie les nouvelles connexions de Jean
    """
    log_file = Path("connection_logs.json")
    history_file = Path("jean_connection_history.json")

    # Charger l'historique des connexions déjà traitées
    processed_timestamps = set()
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
            processed_timestamps = set(history.get('processed', []))

    # Vérifier les nouveaux logs
    if log_file.exists():
        with open(log_file, 'r') as f:
            logs = json.load(f)

        new_jean_connections = []
        for log in logs:
            if (log.get('username') == 'Jean' and
                log.get('success') and
                log['timestamp'] not in processed_timestamps):
                new_jean_connections.append(log)
                processed_timestamps.add(log['timestamp'])

        # S'il y a de nouvelles connexions de Jean
        if new_jean_connections:
            for connection in new_jean_connections:
                timestamp = datetime.fromisoformat(connection['timestamp'])

                # Afficher une alerte
                print(f"\n{'='*60}")
                print(f"ALERTE: JEAN S'EST CONNECTÉ!")
                print(f"Date: {timestamp.strftime('%d/%m/%Y')}")
                print(f"Heure: {timestamp.strftime('%H:%M:%S')}")
                print(f"{'='*60}\n")

                # Enregistrer dans les logs WATCHAI
                watchai_logger.log_activity(
                    "jean_web_connection",
                    f"Jean connecté via l'application web à {timestamp.strftime('%H:%M:%S')}"
                )

            # Sauvegarder l'historique mis à jour
            with open(history_file, 'w') as f:
                json.dump({'processed': list(processed_timestamps)}, f)

            return len(new_jean_connections)

    return 0

def monitor_continuous():
    """
    Surveillance continue des connexions de Jean
    """
    print("WATCHAI - Surveillance des connexions de Jean")
    print("="*60)
    print("Surveillance active de l'application web...")
    print("Appuyez sur Ctrl+C pour arrêter\n")

    check_interval = 30  # Vérifier toutes les 30 secondes
    total_connections = 0

    try:
        while True:
            # Vérifier les nouvelles connexions
            new_connections = check_jean_connections()

            if new_connections > 0:
                total_connections += new_connections
                print(f"Total des connexions de Jean détectées: {total_connections}")

            # Afficher un point de progression
            print(".", end="", flush=True)

            # Attendre avant la prochaine vérification
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print(f"\n\nSurveillance arrêtée.")
        print(f"Total des connexions de Jean détectées pendant cette session: {total_connections}")

def get_jean_summary():
    """
    Affiche un résumé des connexions de Jean
    """
    log_file = Path("connection_logs.json")

    if log_file.exists():
        with open(log_file, 'r') as f:
            logs = json.load(f)

        # Filtrer les connexions de Jean
        jean_logs = [log for log in logs if log.get('username') == 'Jean' and log.get('success')]

        if jean_logs:
            print("\nRÉSUMÉ DES CONNEXIONS DE JEAN")
            print("="*60)
            print(f"Nombre total de connexions: {len(jean_logs)}")

            # Première et dernière connexion
            first = datetime.fromisoformat(jean_logs[0]['timestamp'])
            last = datetime.fromisoformat(jean_logs[-1]['timestamp'])

            print(f"Première connexion: {first.strftime('%d/%m/%Y à %H:%M:%S')}")
            print(f"Dernière connexion: {last.strftime('%d/%m/%Y à %H:%M:%S')}")

            # Jours depuis la dernière connexion
            days_since = (datetime.now() - last).days
            if days_since == 0:
                print("Jean s'est connecté aujourd'hui")
            elif days_since == 1:
                print("Jean s'est connecté hier")
            else:
                print(f"Jean ne s'est pas connecté depuis {days_since} jours")

            # 5 dernières connexions
            print("\n5 dernières connexions:")
            for log in jean_logs[-5:][::-1]:
                timestamp = datetime.fromisoformat(log['timestamp'])
                print(f"  - {timestamp.strftime('%d/%m/%Y à %H:%M:%S')}")
        else:
            print("\nJean ne s'est jamais connecté à l'application")
    else:
        print("\nAucun log de connexion disponible")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        get_jean_summary()
    else:
        # Afficher d'abord le résumé
        get_jean_summary()
        print("\n" + "="*60)

        # Puis lancer la surveillance continue
        monitor_continuous()