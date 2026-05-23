FFTESC — Free FTESC Tool
==========================
Version 1.2.0 — Interface de configuration et contrôle pour ESC
double moteur série FT-*BD (e-skate, e-bike, BLDC)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FONCTIONNALITÉS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▪ Contrôle temps réel : duty cycle, courant moteur/freinage,
  arrêt d'urgence, reboot contrôleur, lecture auto cyclique
▪ Télémétrie live : tension, courants, RPM, température FET/
  moteur, duty cycle, CPU load, angle encodeur
▪ Configuration complète : 12 sections (Moteur, Hall, FOC,
  Limites, Rampes, Freinage, Entrées, PID Vitesse, Batterie,
  Dual Motor, IMU, CAN) réparties sur 7 onglets
▪ Validation UI : bordures rouges/vertes sur les entrées
  numériques, blocage apply/save si valeurs invalides
▪ Tooltips contextuels : 118 descriptions paramètres chargées
  depuis docs/param_descriptions.json
▪ Profils : sauvegarde/chargement/suppression de configurations
  complètes dans ~/.fftesc_profiles/
▪ Double moteur : MotorSelector A/B/Les deux, envoi config
  asynchrone vers les deux contrôleurs
▪ Simulateur intégré : données dual moteur réalistes sans
  matériel (dév. et tests hors-ligne)
▪ Détection firmware : ID ESC + version FW affichés dans
  l'en-tête télémétrie à la connexion
▪ Thèmes : palette 20 couleurs nommées, mode sombre/clair
▪ Internationalisation : 6 langues (FR, EN, DE, ES, PL, IT)
▪ 🆿 Module de récupération (Enter Bootloader Mode) :
   - Diagnostic MCU (sain/corrompu/inconnu)
   - Forçage mode bootloader UART (cmd 60)
   - Guide câblage ST-Link/SWD + flash firmware
▪ 🔬 Downgrade FT85BD (reverse engineering) :
   - MCU identifié : Artery AT32, pas STM32
   - Bootloader AT32 implémenté (stm32_bootloader.py)
   - Firmware v1.5 extrait du tool officiel
   - Flash firmware : flash_firmware.py
   - Bridge MITM série : serial_bridge.py
▪ ⚙️ Assistant de configuration (Wizard) 4 étapes :
   - Sélection profil (Débutant/Avancé/Expert)
   - Moteur, batterie, transmission (pignon/poulie auto)
   - Calcul automatique courant, vitesse, ERPM, PID
   - Résumé avec avertissements de cohérence
   - Conversion unités : diamètre roue (mm/pouces),
     vitesse (km/h/mph)
   - Efficacité transmission configurable (70%-95%)
▪ ⚠️ Avertissements de cohérence :
   - Vitesse > 80 km/h
   - Ratio pignon/poulie < 1.5 ou > 6.0
   - KV moteur élevé, pignon trop petit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTALLATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  python3 ftesc_tool.py

Dépendances : customtkinter, pyserial, matplotlib, numpy,
              Pillow, cairosvg, pytest

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPILER EN EXÉCUTABLE UNIQUE (BUNDLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pour protéger le code source et distribuer un seul fichier :

  source venv/bin/activate
  pip install pyinstaller
  ./build_bundle.sh

Ou manuellement :

  pyinstaller fftesc_tool.spec

L'exécutable sera dans : dist/FFTESC_Tool (~49 Mo)
Il contient tout le code Python, les ressources (SVG, i18n,
tooltips) et les dépendances dans un seul fichier.

Exécution : ./dist/FFTESC_Tool
Cache logos : ~/.fftesc/logo_cache/ (créé automatiquement)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────┐
│  PRESENTATION (gui/)                        │
│  CustomTkinter + matplotlib + i18n + wizard │
│  app.py → sidebar panels → config_tabs      │
├─────────────────────────────────────────────┤
│  MÉTIER (ftesc/)                            │
│  data.py ←→ config_protocol.py              │
│  protocol.py ←→ transport.py ← simulator    │
│  wizard_engine.py ←→ wizard_data.py         │
├─────────────────────────────────────────────┤
│  PHYSIQUE                                    │
│  UART série (pyserial) ←→ µC FTESC          │
│  22 commandes (dont BOOTLOADER, MCU_HEALTH) │
└─────────────────────────────────────────────┘

  ftesc/          Couche métier (data, protocol, transport,
                  config_protocol, profiles, logger, simulator,
                  wizard_engine, wizard_data, stm32_bootloader,
                  motor_detection)
  gui/            Interface graphique (app, panels, widgets,
                  styles, config_tabs, i18n)
  tests/          Tests unitaires pytest (163+ tests)
  docs/           Documentation et descriptions paramètres
  flash_firmware.py    Flash firmware via bootloader UART
  serial_bridge.py     MITM série (Wine ↔ ESC)
  debug_comm.py        Debug protocole interactif

┌─────────────────────────────────────────────┐
│  PROTOCOLE UART (23 commandes)              │
│  0  OBTAIN_DATA_ONCE                        │
│  2  CONTROL_AND_OBTAIN_DATA_ONCE            │
│  17 OBTAIN_FIRMWARE_VERSION                 │
│  25 KEEP_LIVE                               │
│  26 SET_AUTO_OBTAIN                         │
│  29 RESET_AND_REBOOT                        │
│  30 OBTAIN_ALL_FTESC_ID                     │
│  39 SET_SPEED                               │
│  44 SET_HEADLIGHT                           │
│  45 SET_BRAKELIGHT                          │
│  46 SET_BUZZER                              │
│  48 GET_LIGHTS_STATUS                       │
│  49 SET_LIGHTS                              │
│  51 SAVE_EEPROM                             │
│  60 ENTER_BOOTLOADER                        │
│  61 CHECK_MCU_HEALTH                        │
└─────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UTILISATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Lancer : python3 ftesc_tool.py
  2. Connecter : port série AUTO ou manuel, cliquer Connecter
  3. Contrôle : slider duty, entries courant/freinage, estop
  4. Config : onglet Configuration → 7 sous-onglets →
     modifier → Appliquer (A/B/Les deux)
  5. Profils : sidebar → Sauvegarder/Charger/Supprimer
  6. Simulateur : Mode Simulateur (sans matériel)
  7. Wizard : Assistant de configuration → 4 étapes
  8. 🆿 Récupération : Enter Bootloader Mode
     → Diagnostic MCU → Bootloader UART → ST-Link/SWD
  9. 🔬 Downgrade FT85BD : flash_firmware.py --skip-enter
     → flashe le firmware v1.5 via bootloader AT32

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  source venv/bin/activate
  python3 -m pytest tests/ -v

163+ tests : validation, round-trip, wizard, récupération

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVERTISSEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

L'utilisation de ce logiciel implique la configuration et le
contrôle de contrôleurs électroniques de vitesse (ESC) alimentant
des moteurs électriques de forte puissance. Une mauvaise
configuration peut entraîner la destruction du matériel, des
blessures graves ou la mort.

Lisez attentivement disclaimer.txt avant toute utilisation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LICENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Projet libre, aucune garantie. Fourni "TEL QUEL" (AS IS).
Consultez disclaimer.txt pour la décharge de responsabilité.
