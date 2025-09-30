#!/usr/bin/env python3
"""
Met à jour les noms de pays dans Entity_Mappings.xlsx
"""

import pandas as pd
from pathlib import Path

# Mapping des codes pays ISO vers noms complets
COUNTRY_CODES = {
    'AD': 'ANDORRE', 'AE': 'EMIRATS ARABES UNIS', 'AF': 'AFGHANISTAN', 'AG': 'ANTIGUA-ET-BARBUDA',
    'AI': 'ANGUILLA', 'AL': 'ALBANIE', 'AM': 'ARMENIE', 'AO': 'ANGOLA', 'AQ': 'ANTARCTIQUE',
    'AR': 'ARGENTINE', 'AS': 'SAMOA AMERICAINES', 'AT': 'AUTRICHE', 'AU': 'AUSTRALIE', 
    'AW': 'ARUBA', 'AX': 'ILES ALAND', 'AZ': 'AZERBAIDJAN', 'BA': 'BOSNIE-HERZEGOVINE',
    'BB': 'BARBADE', 'BD': 'BANGLADESH', 'BE': 'BELGIQUE', 'BF': 'BURKINA FASO',
    'BG': 'BULGARIE', 'BH': 'BAHREIN', 'BI': 'BURUNDI', 'BJ': 'BENIN', 'BL': 'SAINT-BARTHELEMY',
    'BM': 'BERMUDES', 'BN': 'BRUNEI', 'BO': 'BOLIVIE', 'BQ': 'BONAIRE', 'BR': 'BRESIL',
    'BS': 'BAHAMAS', 'BT': 'BHOUTAN', 'BV': 'ILE BOUVET', 'BW': 'BOTSWANA', 'BY': 'BIELARUS',
    'BZ': 'BELIZE', 'CA': 'CANADA', 'CC': 'ILES COCOS', 'CD': 'RD CONGO', 'CF': 'CENTRAFRIQUE',
    'CG': 'CONGO', 'CH': 'SUISSE', 'CI': 'COTE D\'IVOIRE', 'CK': 'ILES COOK', 'CL': 'CHILI',
    'CM': 'CAMEROUN', 'CN': 'CHINE', 'CO': 'COLOMBIE', 'CR': 'COSTA RICA', 'CU': 'CUBA',
    'CV': 'CAP-VERT', 'CW': 'CURACAO', 'CX': 'ILE CHRISTMAS', 'CY': 'CHYPRE', 'CZ': 'TCHEQUIE',
    'DE': 'ALLEMAGNE', 'DJ': 'DJIBOUTI', 'DK': 'DANEMARK', 'DM': 'DOMINIQUE', 'DO': 'REP DOMINICAINE',
    'DZ': 'ALGERIE', 'EC': 'EQUATEUR', 'EE': 'ESTONIE', 'EG': 'EGYPTE', 'EH': 'SAHARA OCCIDENTAL',
    'ER': 'ERYTHREE', 'ES': 'ESPAGNE', 'ET': 'ETHIOPIE', 'FI': 'FINLANDE', 'FJ': 'FIDJI',
    'FK': 'ILES FALKLAND', 'FM': 'MICRONESIE', 'FO': 'ILES FEROE', 'FR': 'FRANCE', 'GA': 'GABON',
    'GB': 'ROYAUME-UNI', 'GD': 'GRENADE', 'GE': 'GEORGIE', 'GF': 'GUYANE FRANCAISE', 'GG': 'GUERNESEY',
    'GH': 'GHANA', 'GI': 'GIBRALTAR', 'GL': 'GROENLAND', 'GM': 'GAMBIE', 'GN': 'GUINEE',
    'GP': 'GUADELOUPE', 'GQ': 'GUINEE EQUATORIALE', 'GR': 'GRECE', 'GS': 'GEORGIE DU SUD',
    'GT': 'GUATEMALA', 'GU': 'GUAM', 'GW': 'GUINEE-BISSAU', 'GY': 'GUYANA', 'HK': 'HONG KONG',
    'HM': 'ILES HEARD', 'HN': 'HONDURAS', 'HR': 'CROATIE', 'HT': 'HAITI', 'HU': 'HONGRIE',
    'ID': 'INDONESIE', 'IE': 'IRLANDE', 'IL': 'ISRAEL', 'IM': 'ILE DE MAN', 'IN': 'INDE',
    'IO': 'TERRITOIRE BRITANNIQUE', 'IQ': 'IRAK', 'IR': 'IRAN', 'IS': 'ISLANDE', 'IT': 'ITALIE',
    'JE': 'JERSEY', 'JM': 'JAMAIQUE', 'JO': 'JORDANIE', 'JP': 'JAPON', 'KE': 'KENYA',
    'KG': 'KIRGHIZISTAN', 'KH': 'CAMBODGE', 'KI': 'KIRIBATI', 'KM': 'COMORES', 'KN': 'SAINT-KITTS',
    'KP': 'COREE DU NORD', 'KR': 'COREE DU SUD', 'KW': 'KOWEIT', 'KY': 'ILES CAIMANS',
    'KZ': 'KAZAKHSTAN', 'LA': 'LAOS', 'LB': 'LIBAN', 'LC': 'SAINTE-LUCIE', 'LI': 'LIECHTENSTEIN',
    'LK': 'SRI LANKA', 'LR': 'LIBERIA', 'LS': 'LESOTHO', 'LT': 'LITUANIE', 'LU': 'LUXEMBOURG',
    'LV': 'LETTONIE', 'LY': 'LIBYE', 'MA': 'MAROC', 'MC': 'MONACO', 'MD': 'MOLDAVIE',
    'ME': 'MONTENEGRO', 'MF': 'SAINT-MARTIN', 'MG': 'MADAGASCAR', 'MH': 'ILES MARSHALL',
    'MK': 'MACEDOINE DU NORD', 'ML': 'MALI', 'MM': 'MYANMAR', 'MN': 'MONGOLIE', 'MO': 'MACAO',
    'MP': 'ILES MARIANNES', 'MQ': 'MARTINIQUE', 'MR': 'MAURITANIE', 'MS': 'MONTSERRAT',
    'MT': 'MALTE', 'MU': 'MAURICE', 'MV': 'MALDIVES', 'MW': 'MALAWI', 'MX': 'MEXIQUE',
    'MY': 'MALAISIE', 'MZ': 'MOZAMBIQUE', 'NA': 'NAMIBIE', 'NC': 'NOUVELLE-CALEDONIE',
    'NE': 'NIGER', 'NF': 'ILE NORFOLK', 'NG': 'NIGERIA', 'NI': 'NICARAGUA', 'NL': 'PAYS-BAS',
    'NO': 'NORVEGE', 'NP': 'NEPAL', 'NR': 'NAURU', 'NU': 'NIUE', 'NZ': 'NOUVELLE-ZELANDE',
    'OM': 'OMAN', 'PA': 'PANAMA', 'PE': 'PEROU', 'PF': 'POLYNESIE FRANCAISE', 'PG': 'PAPOUASIE',
    'PH': 'PHILIPPINES', 'PK': 'PAKISTAN', 'PL': 'POLOGNE', 'PM': 'SAINT-PIERRE',
    'PN': 'PITCAIRN', 'PR': 'PORTO RICO', 'PS': 'PALESTINE', 'PT': 'PORTUGAL', 'PW': 'PALAOS',
    'PY': 'PARAGUAY', 'QA': 'QATAR', 'RE': 'REUNION', 'RO': 'ROUMANIE', 'RS': 'SERBIE',
    'RU': 'RUSSIE', 'RW': 'RWANDA', 'SA': 'ARABIE SAOUDITE', 'SB': 'ILES SALOMON',
    'SC': 'SEYCHELLES', 'SD': 'SOUDAN', 'SE': 'SUEDE', 'SG': 'SINGAPOUR', 'SH': 'SAINTE-HELENE',
    'SI': 'SLOVENIE', 'SJ': 'SVALBARD', 'SK': 'SLOVAQUIE', 'SL': 'SIERRA LEONE', 'SM': 'SAINT-MARIN',
    'SN': 'SENEGAL', 'SO': 'SOMALIE', 'SR': 'SURINAME', 'SS': 'SOUDAN DU SUD', 'ST': 'SAO TOME',
    'SV': 'EL SALVADOR', 'SX': 'SAINT-MARTIN', 'SY': 'SYRIE', 'SZ': 'ESWATINI', 'TC': 'TURKS',
    'TD': 'TCHAD', 'TF': 'TERRES AUSTRALES', 'TG': 'TOGO', 'TH': 'THAILANDE', 'TJ': 'TADJIKISTAN',
    'TK': 'TOKELAU', 'TL': 'TIMOR ORIENTAL', 'TM': 'TURKMENISTAN', 'TN': 'TUNISIE', 'TO': 'TONGA',
    'TR': 'TURQUIE', 'TT': 'TRINITE-ET-TOBAGO', 'TV': 'TUVALU', 'TW': 'TAIWAN', 'TZ': 'TANZANIE',
    'UA': 'UKRAINE', 'UG': 'OUGANDA', 'UM': 'ILES MINEURES', 'US': 'ETATS-UNIS', 'UY': 'URUGUAY',
    'UZ': 'OUZBEKISTAN', 'VA': 'VATICAN', 'VC': 'SAINT-VINCENT', 'VE': 'VENEZUELA', 'VG': 'ILES VIERGES BRIT',
    'VI': 'ILES VIERGES US', 'VN': 'VIETNAM', 'VU': 'VANUATU', 'WF': 'WALLIS-ET-FUTUNA',
    'WS': 'SAMOA', 'XK': 'KOSOVO', 'YE': 'YEMEN', 'YT': 'MAYOTTE', 'ZA': 'AFRIQUE DU SUD',
    'ZM': 'ZAMBIE', 'ZW': 'ZIMBABWE'
}

def update_country_names():
    """Met à jour les noms de pays dans Entity_Mappings.xlsx"""
    
    file_path = Path("/Users/julienmarboeuf/Documents/MEREYA/AGL/EXPORT-Db/Master_Data/Entity_Mappings.xlsx")
    
    print("🌍 MISE À JOUR DES NOMS DE PAYS")
    print("="*50)
    
    try:
        # Lire la feuille Destinations
        df = pd.read_excel(file_path, sheet_name='Destinations')
        print(f"Lignes trouvées: {len(df)}")
        
        # Compter les valeurs manquantes
        missing_before = df['DESTINATION SIMPLE'].isna().sum()
        print(f"Noms manquants avant: {missing_before}")
        
        # Mettre à jour les noms manquants
        updated_count = 0
        for idx, row in df.iterrows():
            code = str(row['DESTINATION']).strip().upper()
            current_name = row['DESTINATION SIMPLE']
            
            # Si le nom est manquant et qu'on a le code
            if pd.isna(current_name) and code in COUNTRY_CODES:
                df.loc[idx, 'DESTINATION SIMPLE'] = COUNTRY_CODES[code]
                updated_count += 1
                if updated_count <= 10:  # Afficher les 10 premiers
                    print(f"  {code} → {COUNTRY_CODES[code]}")
        
        if updated_count > 10:
            print(f"  ... et {updated_count - 10} autres")
        
        print(f"\nMis à jour: {updated_count} pays")
        
        # Sauvegarder le fichier mis à jour
        with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            # Lire les autres feuilles pour les préserver
            exportateurs = pd.read_excel(file_path, sheet_name='Exportateurs')
            destinataires = pd.read_excel(file_path, sheet_name='Destinataires')
            
            # Écrire toutes les feuilles
            exportateurs.to_excel(writer, sheet_name='Exportateurs', index=False)
            destinataires.to_excel(writer, sheet_name='Destinataires', index=False)
            df.to_excel(writer, sheet_name='Destinations', index=False)
        
        print(f"✅ Fichier mis à jour: {file_path}")
        
        # Vérification finale
        missing_after = df['DESTINATION SIMPLE'].isna().sum()
        print(f"Noms manquants après: {missing_after}")
        
        # Afficher quelques exemples des codes non trouvés
        if missing_after > 0:
            unknown_codes = df[df['DESTINATION SIMPLE'].isna()]['DESTINATION'].unique()[:10]
            print(f"Codes non reconnus (exemples): {list(unknown_codes)}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    update_country_names()