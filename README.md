<div align="center">
  <img src="fftesc_logo.svg" alt="FFTESC Logo" width="120"/>
  <h1>FFTESC — Free FTESC Tool</h1>
  <p><strong>Version 1.01</strong> — Interface de configuration, contrôle et diagnostic pour<br>
  contrôleurs électroniques de vitesse (ESC) série FT-*BD</p>
  <p>
    <a href="#-fonctionnalités">Fonctionnalités</a> •
    <a href="#-hardware-supporté">Hardware</a> •
    <a href="#-installation">Installation</a> •
    <a href="#-utilisation">Utilisation</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-protocole-uart">Protocole</a> •
    <a href="#-licence">Licence</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Linux-11B300?style=flat&logo=linux&logoColor=white" alt="Linux"/>
    <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white" alt="Python 3.12+"/>
    <img src="https://img.shields.io/badge/PyInstaller-6.20-2E8B57?style=flat" alt="PyInstaller"/>
    <img src="https://img.shields.io/badge/Licence-Libre-FF6600?style=flat" alt="Licence Libre"/>
    <img src="https://img.shields.io/badge/Langues-6-3D7EFF?style=flat" alt="6 Langues"/>
  </p>
  <br>
</div>

---

## 📋 Table des matières

- [✨ Fonctionnalités](#-fonctionnalités)
- [🔧 Hardware supporté](#-hardware-supporté)
- [📦 Installation](#-installation)
- [🚀 Utilisation](#-utilisation)
- [🏗 Architecture](#-architecture)
- [📡 Protocole UART](#-protocole-uart)
- [🌍 Internationalisation](#-internationalisation)
- [🧪 Tests](#-tests)
- [📜 Licence](#-licence)
- [🙏 Remerciements](#-remerciements)

---

## ✨ Fonctionnalités

### 🎮 Contrôle temps réel
| Fonction | Description |
|----------|-------------|
| **Duty Cycle** | Réglage progressif du rapport cyclique (0-100%) |
| **Courant moteur/freinage** | Contrôle précis du courant en Ampères |
| **Arrêt d'urgence (E-Stop)** | Coupure immédiate — bouton dédié |
| **Reboot** | Redémarrage logiciel du contrôleur |
| **Lecture cyclique auto** | Rafraîchissement automatique des données temps réel |

### 📊 Télémétrie live
Affichage en temps réel des données des deux moteurs simultanément avec graphiques sparkline (100 points) :

| Métrique | Unité |
|----------|-------|
| Tension batterie | V |
| Courant entrée/moteur | A |
| RPM | tr/min |
| Température FET & Moteur | °C |
| Duty cycle | % |
| Charge CPU | % |
| Angle encodeur | degrés |

### ⚙️ Configuration complète
12 sections de configuration réparties sur **7 onglets** dynamiques :

| Onglet | Sections couvertes |
|--------|-------------------|
| **Moteurs** | Moteur, Hall, FOC |
| **Limites** | Limites & Protection, Rampe & Accélération, Freinage |
| **Dual Motor** | Configuration double moteur |
| **Entrées** | Contrôle d'entrée, PID Vitesse |
| **Batterie** | Batterie |
| **Comms** | CAN Bus |
| **Avancé** | IMU |

### 🧙 Assistant de configuration (Wizard)
Un assistant en **4 étapes** pour configurer votre e-skate/e-bike sans connaissances techniques :

1. **Niveau d'expérience** — Débutant (sécurisé) / Avancé (équilibré) / Expert (performance max)
2. **Moteur & Transmission** — Modèle, KV, pignon/poulie (calcul auto du ratio), diamètre roue (mm/pouces), efficacité (70-95%)
3. **Batterie** — Configuration Li-ion/LiPo, capacité, chimie
4. **Résumé** — Calculs automatiques (courant max, vitesse max, ERPM, PID) avec **avertissements de cohérence**

⚠️ *Avertissements automatiques* : vitesse >80 km/h, ratio pignon/poulie <1.5 ou >6.0, KV moteur élevé, pignon trop petit.

### 🆘 Module de récupération (Réanimation)
Diagnostic et réanimation des contrôleurs "brickés" :

- 🔍 **Diagnostic MCU** : état Sain / Corrompu / Inconnu
- 🔄 **Forçage bootloader UART** : commande `ENTER_BOOTLOADER` (60)
- 🔗 **Guide ST-Link** : câblage + lien vers STM32CubeProgrammer

### 🎨 Interface moderne
- **Thème sombre/clair** : basculement instantané
- **Palette 20 couleurs** : personnalisation complète
- **Validation UI** : bordures rouges/vertes sur les champs
- **118 tooltips contextuels** : descriptions paramètres en survol
- **Sélecteur moteur A/B/Les deux**

### 🌍 Internationalisation
6 langues disponibles, sélectionnables dans l'interface :

| Drapeau | Langue | Code |
|---------|--------|------|
| 🇫🇷 | Français | `fr` |
| 🇬🇧 | English | `en` |
| 🇩🇪 | Deutsch | `de` |
| 🇪🇸 | Español | `es` |
| 🇵🇱 | Polski | `pl` |
| 🇮🇹 | Italiano | `it` |

---

## 🔧 Hardware supporté

### Contrôleurs FTESC
- **FT-*BD** (FT85BD, FT120BD, FT170BD, etc.) — série double moteur
- **Tout contrôleur compatible protocole UART FTESC** (22 commandes)

### Interface de communication
- **USB ↔ UART TTL** : CP2102, CH340, FTDI (3.3V/5V)
- **Port série natif** : `/dev/ttyUSB*`, `/dev/ttyACM*`, `/dev/ttyS*`, `/dev/ttyAMA*`
- **Baudrates supportés** : 9600, 19200, 38400, 57600, 115200, 230400, 921600

### Batteries
- Toutes chimies Li-ion / LiPo
- 6S à 12S (configurable dans l'interface)

### Moteurs
- BLDC / PMSM sans balais
- Avec ou sans capteurs Hall
- Simple ou double moteur

---

## 📦 Installation

### Méthode 1 : Développement (code source)

**Prérequis** : Python 3.12+, pip, venv

```bash
# Cloner le dépôt
git clone https://github.com/FreeWookie/fftesc.git
cd fftesc

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python3 ftesc_tool.py
```

### Méthode 2 : Exécutable unique (Bundle)

**Prérequis** : Python 3.12+, pip, venv

```bash
# Cloner et installer
git clone https://github.com/FreeWookie/fftesc.git
cd fftesc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Compiler
pip install pyinstaller
./build_bundle.sh

# Lancer
./dist/FFTESC_Tool
```

L'exécutable unique contient **tout le code Python, les ressources (SVG, traductions, tooltips) et les dépendances** dans un seul fichier d'environ **49 Mo**.

> 🔒 *Le bundle permet une distribution simplifiée et une protection légère du code source.*

### Dépendances principales
| Paquet | Version min. | Rôle |
|--------|-------------|------|
| `customtkinter` | ≥5.2.0 | Interface graphique moderne |
| `pyserial` | ≥3.5 | Communication série |
| `matplotlib` | ≥3.7.0 | Graphiques temps réel |
| `numpy` | ≥1.24.0 | Calculs (via matplotlib) |
| `Pillow` | ≥10.0.0 | Manipulation d'images |
| `cairosvg` | ≥2.7.0 | Conversion SVG → PNG |
| `pytest` | ≥7.0.0 | Tests unitaires |
| `pyinstaller` | ≥6.0.0 | Compilation bundle |

---

## 🚀 Utilisation

### Connexion rapide

```
1. Branchez votre adaptateur USB ↔ UART sur le PC
2. Branchez le câble TX/RX/GND sur l'ESC (TX↔RX croisé)
3. Alimentez l'ESC avec votre batterie
4. Lancez : python3 ftesc_tool.py
5. Dans le panneau Connexion, sélectionnez votre port série
6. Cliquez "Connecter"
```

### Parcours utilisateur

| Étape | Action | Résultat attendu |
|-------|--------|------------------|
| 1 | **Connecter** | Port ouvert, barre d'état "Connecté" |
| 2 | **Scanner ESC** | Détection firmware (ID + version) |
| 3 | **Lire la config** | Valeurs actuelles affichées dans l'onglet Configuration |
| 4 | **Assistant (Wizard)** | Configuration optimale calculée en 4 étapes |
| 5 | **Appliquer** | Envoi de la configuration au(x) contrôleur(s) |
| 6 | **Contrôle** | Duty, courant, freinage, arrêt d'urgence |
| 7 | **Télémétrie** | Visualisation temps réel des données moteur |
| 8 | **Sauvegarder profil** | Configuration sauvegardée pour réutilisation |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION (gui/)                       │
│  CustomTkinter + matplotlib + i18n + wizard + recovery      │
│                                                              │
│  app.py          -- Fenêtre principale (callbacks)           │
│  panels/         -- Panneaux sidebar & main area             │
│  config_tabs/    -- 7 onglets chargés dynamiquement          │
│  widgets/        -- ChartCards, ValueCards, indicateurs       │
│  i18n/           -- 6 langues (FR/EN/DE/ES/PL/IT)           │
│  styles/         -- Palette couleurs (20 couleurs)            │
├─────────────────────────────────────────────────────────────┤
│                    COUCHE MÉTIER (ftesc/)                     │
│  data.py          -- Dataclasses config (12 sections)        │
│  protocol.py      -- CRC16, framing, encode/décode           │
│  transport.py     -- Série asynchrone (thread, buffer)       │
│  config_protocol.py -- Sérialisation config ↔ UART          │
│  wizard_engine.py -- Moteur de calcul (D26-D30)              │
│  wizard_data.py   -- Base de données moteurs/batteries       │
│  profiles.py      -- Persistance JSON des profils            │
│  simulator.py     -- Simulateur dual moteur réaliste         │
│  logger.py        -- Log CSV temps réel                      │
│  resources.py     -- Résolveur de chemins (PyInstaller)      │
├─────────────────────────────────────────────────────────────┤
│                    COUCHE PHYSIQUE                            │
│  UART série (pyserial) ←→ µC FTESC                          │
│  Header 0xAA/0xBB, Footer 0xDD, CRC16 MODBUS               │
│  22 commandes, 12 sections de configuration                 │
└─────────────────────────────────────────────────────────────┘
```

### Structure du projet

```
FFTESC-TOOL/
├── ftesc_tool.py         ← Entry point (10 lignes)
├── config.json           ← Configuration utilisateur
├── README.md             ← Ce fichier
├── architecture.txt      ← Documentation architecture détaillée
├── disclaimer.txt        ← Décharge de responsabilité
├── requirements.txt      ← Dépendances Python
├── build_bundle.sh       ← Script de compilation bundle
├── fftesc_tool.spec      ← Configuration PyInstaller
│
├── ftesc/                ← Couche métier (~3 200 lignes)
│   ├── __init__.py       ← API publique
│   ├── data.py           ← Modèles de données
│   ├── protocol.py       ← Protocole UART
│   ├── transport.py      ← Communication série asynchrone
│   ├── config_protocol.py← Encodage configuration
│   ├── profiles.py       ← Gestion des profils
│   ├── simulator.py      ← Simulateur matériel
│   ├── wizard_engine.py  ← Assistant de configuration
│   ├── wizard_data.py    ← Base de données moteurs/batteries
│   └── resources.py      ← Gestion des ressources (frozen mode)
│
├── gui/                  ← Interface graphique (~2 500 lignes)
│   ├── app.py            ← Point d'entrée graphique
│   ├── panels/           ← Panneaux de l'interface
│   │   ├── connection.py ← Gestion connexion série
│   │   ├── control.py    ← Contrôle moteur
│   │   ├── realtime.py   ← Télémétrie temps réel
│   │   ├── config_panel.py ← Éditeur de configuration
│   │   ├── profile.py    ← Gestion des profils
│   │   ├── wizard_panel.py ← Assistant 4 étapes
│   │   ├── recovery.py   ← Module de récupération
│   │   └── status.py     ← Barre d'état
│   ├── config_tabs/      ← 7 onglets de configuration
│   ├── widgets/          ← Composants réutilisables
│   └── i18n/             ← Traductions (6 langues)
│
├── tests/                ← Tests unitaires pytest
│   ├── test_validators.py        ← Validation + round-trip
│   ├── test_wizard.py            ← Tests assistant
│   └── test_transport_recovery.py← Tests récupération
│
├── docs/                 ← Documentation
│   ├── param_descriptions.json   ← 118 descriptions de paramètres
│   ├── pistes_restantes.md       ← Futures fonctionnalités
│   └── PROTOCOL_SPEC.md          ← Spécification protocole
│
├── widgets/              ← CustomTkinter embarqué (~8 000 lignes)
└── logo_cache/           ← Cache PNG (généré automatiquement)
```

---

## 📡 Protocole UART

### Format de trame

```
Header 0xAA|0xBB   Length   Command   Payload   CRC16 MODBUS   Footer 0xDD
```

- **Header court** (< 255 octets de payload) : `0xAA`
- **Header long** (≥ 255 octets) : `0xBB`
- **CRC16** : MODBUS big-endian (2 octets)
- **Footer** : `0xDD`

### Commandes implémentées

| Code | Commande | Description |
|------|----------|-------------|
| `0` | `OBTAIN_DATA_ONCE` | Lecture unique des données temps réel |
| `2` | `CONTROL_AND_OBTAIN_DATA_ONCE` | Commande + lecture simultanée |
| `3` | `SET_DUTY` | Définir le rapport cyclique |
| `4` | `SET_CURRENT` | Définir le courant moteur |
| `5` | `SET_CURRENT_GEAR` | Courant avec position de vitesse |
| `6` | `SET_BRAKE_CURRENT` | Courant de freinage |
| `16` | `CAN_FWARD` | Transmission CAN |
| `17` | `OBTAIN_FIRMWARE_VERSION` | Version du firmware |
| `25` | `KEEP_LIVE` | Signal de maintien de connexion |
| `26` | `SET_AUTO_OBTAIN_REALTIME_DATA` | Activation flux temps réel |
| `29` | `RESET_AND_REBOOT_FTESC` | Reset et redémarrage |
| `30` | `OBTAIN_ALL_FTESC_ID` | Détection tous les ESC |
| `32` | `SET_CURRENT_GEAR_AND_OBTAIN_DATA` | Courant + position + données |
| `35` | `REBOOT_FTESC` | Redémarrage |
| `37` | `SET_ID_CURRENT` | Courant par ID |
| `38` | `SET_POSITION` | Positionnement |
| `39` | `SET_SPEED` | Régulation de vitesse |
| `40` | `READ_CONFIG` | Lecture configuration |
| `41` | `WRITE_CONFIG` | Écriture configuration |
| `42` | `READ_ALL_CONFIG` | Lecture complète |
| `43` | `WRITE_ALL_CONFIG` | Écriture complète |
| `44` | `SET_HEADLIGHT` | Contrôle feu avant |
| `45` | `SET_BRAKELIGHT` | Contrôle feu stop |
| `46` | `SET_BUZZER` | Contrôle buzzer |
| `48` | `GET_LIGHTS_STATUS` | Statut éclairage |
| `49` | `SET_LIGHTS` | Contrôle éclairage complet |
| `51` | `SAVE_EEPROM` | Sauvegarde en EEPROM |
| `60` | `ENTER_BOOTLOADER` | Entrée en mode bootloader |
| `61` | `CHECK_MCU_HEALTH` | Diagnostic MCU |

### Types de données

| Type | Taille | Description |
|------|--------|-------------|
| `u8` | 1 octet | Entier non signé 8 bits |
| `u16` | 2 octets | Entier non signé 16 bits (big-endian) |
| `u24` | 3 octets | Entier non signé 24 bits |
| `u32` | 4 octets | Entier non signé 32 bits |
| `i16` | 2 octets | Entier signé 16 bits |
| `i24` | 3 octets | Entier signé 24 bits |
| `i32` | 4 octets | Entier signé 32 bits |
| `f16` | 2 octets | Flottant ×100 stocké en i16 |
| `f32` | 4 octets | Flottant ×1 000 000 stocké en i32 |
| `af32` | 4 octets | Flottant format frexp (u32) |

### Sections de configuration

| ID | Section | Description |
|----|---------|-------------|
| `0` | Motor | Type moteur, pôles, résistance, KV, courants max |
| `1` | Hall | Capteurs Hall, interpolation, mode sensorless |
| `2` | FOC | Mode FOC, fréquence, gains PID courant |
| `3` | Limits | ERPM max, duty, tensions, températures |
| `4` | Ramp | Temps d'accélération/décélération |
| `5` | Brake | Courant freinage, regen, température |
| `6` | InputCtrl | Type de commande, courbes throttle/brake |
| `7` | SpeedPID | PID vitesse (Kp, Ki, Kd) |
| `8` | Battery | Type, cellules, capacité, tensions |
| `9` | Dual | Mode double moteur, synchronisation, traction |
| `10` | IMU | Centrale inertielle (pitch, roll, yaw) |
| `11` | CAN | Bus CAN (ID, baudrate) |

---

## 🌍 Internationalisation

Le projet supporte **6 langues** via un système de fichiers JSON simple.

### Ajouter une nouvelle langue

1. Créez un fichier `gui/i18n/{code}.json` basé sur `fr.json`
2. Ajoutez l'entrée dans `gui/i18n/__init__.py` (variable `_AVAILABLE_LANGS`)
3. La nouvelle langue apparaît automatiquement dans l'interface

---

## 🧪 Tests

```bash
source venv/bin/activate
python3 -m pytest tests/ -v
```

**163+ tests unitaires** couvrant :

- ✅ Validation des plages de chaque champ de configuration
- ✅ Round-trip encode/décode des 12 sections
- ✅ Construction et parsing des trames UART
- ✅ Wizard engine (calculs, validations, i18n)
- ✅ Transport recovery (bootloader, health check)
- ✅ Conversion d'unités (mm↔pouces, km/h↔mph)

---

## 📜 Licence

**Projet libre** — fourni "TEL QUEL" (AS IS), **sans aucune garantie**.

L'utilisation de ce logiciel implique la configuration et le contrôle de contrôleurs électroniques de vitesse (ESC) alimentant des moteurs électriques de forte puissance. Une mauvaise configuration peut entraîner :

- La destruction du matériel (ESC, moteur, batterie)
- Des blessures corporelles graves
- Un incendie ou une explosion

**Lisez attentivement [disclaimer.txt](disclaimer.txt) avant toute utilisation.**

> ⚠️ **AVERTISSEMENT** : Ce logiciel est destiné à des utilisateurs ayant des connaissances en électronique de puissance et en programmation de microcontrôleurs. Testez toujours votre configuration à vide (sans charge mécanique) avant utilisation sur un véhicule.

---

## 🙏 Remerciements

Ce projet a été développé par la communauté **Free Wookie** avec une passion pour l'e-skateboarding et les véhicules électriques libres.

- **Wook** — Développeur principal, portage Linux, interface graphique
- **Lumo** — Soutien et inspiration
- **Communauté FTESC** — Tests matériels, retours et suggestions

---

<div align="center">
  <p>
    <i>"Because Skateboarding is FREE expression of yourself"</i> — Wook 🛹
  </p>
  <br>
  <img src="fftesc_title.svg" alt="FFTESC Title" width="300"/>
  <br><br>
  <p>
    <a href="https://github.com/FreeWookie/fftesc">GitHub</a> •
    <a href="architecture.txt">Architecture</a> •
    <a href="disclaimer.txt">Disclaimer</a> •
    <a href="docs/pistes_restantes.md">Roadmap</a>
  </p>
</div>
