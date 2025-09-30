#!/usr/bin/env python3
"""
WATCHAI - Surveillance de toutes les connexions utilisateurs
Ce script surveille automatiquement les connexions de Julien, Erick et Jean
"""

import time
from datetime import datetime, timedelta
from pathlib import Path
import json
from watchai_logger import watchai_logger

# Couleurs pour l'affichage
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def check_new_connections():
    """
    Vérifie les nouvelles connexions de tous les utilisateurs
    """
    log_file = Path("connection_logs.json")
    history_file = Path("all_users_connection_history.json")

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

        new_connections = []
        for log in logs:
            if (log.get('success') and
                log['timestamp'] not in processed_timestamps):
                new_connections.append(log)
                processed_timestamps.add(log['timestamp'])

        # S'il y a de nouvelles connexions
        if new_connections:
            for connection in new_connections:
                username = connection['username']
                timestamp = datetime.fromisoformat(connection['timestamp'])

                # Choisir la couleur selon l'utilisateur
                if username == "Julien":
                    color = Colors.OKGREEN
                elif username == "Erick":
                    color = Colors.OKBLUE
                elif username == "Jean":
                    color = Colors.WARNING
                else:
                    color = Colors.ENDC

                # Afficher l'alerte
                print(f"\n{color}{'='*60}")
                print(f"CONNEXION: {username.upper()}")
                print(f"Date: {timestamp.strftime('%d/%m/%Y')}")
                print(f"Heure: {timestamp.strftime('%H:%M:%S')}")
                print(f"{'='*60}{Colors.ENDC}\n")

                # Enregistrer dans les logs WATCHAI
                watchai_logger.log_activity(
                    f"{username.lower()}_connection",
                    f"{username} connecté à {timestamp.strftime('%H:%M:%S')}"
                )

            # Sauvegarder l'historique mis à jour
            with open(history_file, 'w') as f:
                json.dump({'processed': list(processed_timestamps)}, f)

            return new_connections

    return []

def get_today_summary():
    """
    Affiche un résumé des connexions du jour
    """
    log_file = Path("connection_logs.json")

    if log_file.exists():
        with open(log_file, 'r') as f:
            logs = json.load(f)

        # Filtrer les connexions d'aujourd'hui
        today = datetime.now().date()
        today_connections = {
            "Julien": [],
            "Erick": [],
            "Jean": []
        }

        for log in logs:
            if log.get('success'):
                log_time = datetime.fromisoformat(log['timestamp'])
                if log_time.date() == today:
                    username = log['username']
                    if username in today_connections:
                        today_connections[username].append(log_time)

        print(f"\n{Colors.HEADER}{'='*60}")
        print(f"RÉSUMÉ DES CONNEXIONS D'AUJOURD'HUI")
        print(f"{'='*60}{Colors.ENDC}")
        print(f"Date: {today.strftime('%d/%m/%Y')}\n")

        total_today = 0
        for username, connections in today_connections.items():
            if username == "Julien":
                color = Colors.OKGREEN
            elif username == "Erick":
                color = Colors.OKBLUE
            elif username == "Jean":
                color = Colors.WARNING

            count = len(connections)
            total_today += count

            print(f"{color}{username}: {count} connexion(s){Colors.ENDC}")

            if connections:
                last_conn = max(connections)
                print(f"   Dernière connexion: {last_conn.strftime('%H:%M:%S')}")

                # Afficher toutes les connexions du jour
                if count > 1:
                    print(f"   Connexions: ", end="")
                    for conn in sorted(connections):
                        print(f"{conn.strftime('%H:%M')} ", end="")
                    print()
            print()

        print(f"{Colors.BOLD}Total aujourd'hui: {total_today} connexion(s){Colors.ENDC}")

        # Alertes
        print(f"\n{Colors.HEADER}ALERTES:{Colors.ENDC}")

        # Alerte si Erick ne s'est pas connecté
        if len(today_connections["Erick"]) == 0:
            print(f"{Colors.FAIL}Erick ne s'est pas encore connecté aujourd'hui{Colors.ENDC}")

        # Alerte si Jean ne s'est pas connecté
        if len(today_connections["Jean"]) == 0:
            print(f"{Colors.FAIL}Jean ne s'est pas encore connecté aujourd'hui{Colors.ENDC}")

        # Statistiques globales
        print(f"\n{Colors.HEADER}STATISTIQUES GLOBALES:{Colors.ENDC}")
        all_connections = {
            "Julien": 0,
            "Erick": 0,
            "Jean": 0
        }

        for log in logs:
            if log.get('success'):
                username = log['username']
                if username in all_connections:
                    all_connections[username] += 1

        for username, count in all_connections.items():
            percentage = (count / len([l for l in logs if l.get('success')]) * 100) if logs else 0
            print(f"  {username}: {count} connexions totales ({percentage:.1f}%)")

    else:
        print("\nAucun log de connexion disponible")

def monitor_continuous():
    """
    Surveillance continue de tous les utilisateurs
    """
    print(f"{Colors.HEADER}WATCHAI - Surveillance de tous les utilisateurs{Colors.ENDC}")
    print("="*60)
    print("Surveillance active: Julien, Erick, Jean")
    print("Appuyez sur Ctrl+C pour arrêter\n")

    check_interval = 30  # Vérifier toutes les 30 secondes
    last_summary_hour = -1

    try:
        while True:
            current_hour = datetime.now().hour

            # Afficher un résumé toutes les heures
            if current_hour != last_summary_hour:
                get_today_summary()
                last_summary_hour = current_hour

            # Vérifier les nouvelles connexions
            new_connections = check_new_connections()

            if new_connections:
                print(f"\n{Colors.BOLD}{len(new_connections)} nouvelle(s) connexion(s) détectée(s){Colors.ENDC}")

            # Afficher un point de progression
            print(".", end="", flush=True)

            # Attendre avant la prochaine vérification
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.HEADER}Surveillance arrêtée.{Colors.ENDC}")
        get_today_summary()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        get_today_summary()
    else:
        # Afficher d'abord le résumé
        get_today_summary()
        print("\n" + "="*60)

        # Puis lancer la surveillance continue
        monitor_continuous()