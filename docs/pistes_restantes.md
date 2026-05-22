# Pistes restantes — FFTESC v1.01

## 1. Éditeur graphique courbes throttle/brake
**Fichiers** : `gui/panels/config_panel.py`, nouveau widget
**Description** : Remplacer les champs CSV "Throttle Curve (6 vals)" et "Brake Curve (6 vals)" par un widget matplotlib interactif. L'utilisateur pourrait cliquer/glisser 6 points de contrôle sur un graphique pour ajuster la courbe d'accélération/freinage visuellement, avec mise à jour automatique du champ texte en temps réel.
**Complexité** : Élevée (widget personnalisé, synchronisation bidirectionnelle)

## 2. Bouton Read All / Write All (toutes sections, tous contrôleurs)
**Fichiers** : `gui/panels/config_panel.py`
**Description** : Actuellement, "Lire tout l'onglet" ne lit que les sections de l'onglet courant. Un bouton "Lire tout" global lirait les 12 sections des deux contrôleurs (A et B) et les sections globales, soit ~26 trames avec délais. Utile pour un snapshot complet au démarrage.
**Complexité** : Moyenne (séquençage des trames, gestion des timeouts)

## 3. Barre de progression pour les opérations bulk
**Fichiers** : `gui/panels/config_panel.py`
**Description** : Quand on lance une lecture/écriture de plusieurs sections, afficher une barre de progression (type CTkProgressBar) dans le footer du ConfigPanel pour visualiser l'avancement (ex: 3/12 sections lues).
**Complexité** : Faible

## 4. Persistance de la config dans l'EEPROM du contrôleur
**Fichiers** : `ftesc/config_protocol.py`, `gui/panels/config_panel.py`
**Description** : Ajouter un bouton "Sauvegarder dans l'EEPROM" qui envoie la commande de sauvegarde permanente au contrôleur (commande firmware dédiée). Complément du "Read All" qui recharge depuis l'EEPROM.
**Complexité** : Moyenne (dépend du support firmware)

## 5. Tests d'intégration simulateur + boucle temps réel
**Fichiers** : `tests/test_integration.py`
**Description** : Tester la boucle complète : simulateur → transport → parse → affichage UI (sans headless Tk). Vérifier que les données simulées transitent correctement jusqu'aux ValueCards/ChartCards.
**Complexité** : Moyenne (besoin d'un mock Tkinter)

## 6. Export/import profils par fichier externe
**Fichiers** : `ftesc/profiles.py`, `gui/panels/config_panel.py`
**Description** : Actuellement les profils sont dans `~/.fftesc_profiles/`. Ajouter "Exporter..." (choisir un chemin .json) et "Importer..." (sélectionner un fichier) pour partager des profils entre machines.
**Complexité** : Faible

## 7. Mode veille auto et reconnexion
**Fichiers** : `ftesc/transport.py`
**Description** : Si le port série se déconnecte (câble débranché), tenter une reconnexion automatique toutes les 2 secondes. Optionnellement, envoyer KEEP_LIVE périodiquement pour détecter la perte de connexion plus rapidement.
**Complexité** : Faible

## 8. Gestion multi-contrôleurs (CAN)
**Fichiers** : `gui/app.py`, `gui/panels/connection.py`
**Description** : Interface pour détecter et sélectionner plusieurs contrôleurs sur le bus CAN. Afficher la liste des IDs, permettre de les nommer, et basculer la configuration/télémétrie entre eux.
**Complexité** : Élevée (nécessite hardware CAN)

## 9. Logging temps réel avec rejeu
**Fichiers** : `ftesc/logger.py`, `gui/panels/realtime.py`
**Description** : Bouton "Enregistrer" dans le panneau télémétrie qui démarre l'enregistrement CSV. Ajouter un mode "Rejeu" qui lit un fichier CSV et le repasse dans l'UI au même rythme (debug sans hardware).
**Complexité** : Moyenne

## 10. Documentation du protocole
**Fichiers** : `docs/PROTOCOL_SPEC.md` (vide actuellement)
**Description** : Rédiger la spécification complète du protocole UART : trames, CRC16, types de données, commandes, sections de configuration. Essentiel pour que d'autres développeurs puissent implémenter le firmware côté ESC.
**Complexité** : Faible (rédactionnel)

## 11. Indicateur de progression par section (spinner)
**Fichiers** : `gui/panels/config_panel.py`
**Description** : Quand on clique "Appliquer" ou "Lire" sur une section, remplacer temporairement l'icône du bouton par un spinner (ou désactiver le bouton) jusqu'à réception de la réponse. Feedback visuel immédiat que l'opération est en cours.
**Complexité** : Faible

---

## ✅ Réalisé en v1.01

- **Thème clair/sombre** : palette 20 couleurs nommées, basculement dynamique
- **Assistant de configuration (Wizard)** : 4 étapes, calculs automatiques, avertissements
- **Module de récupération** : diagnostic MCU, bootloader UART, guide ST-Link
- **Internationalisation** : 6 langues (FR, EN, DE, ES, PL, IT)
- **Conversion d'unités** : diamètre roue (mm/pouces), vitesse (km/h/mph)
- **Efficacité transmission** : configurable 70%-95%
- **Avertissements de cohérence** : vitesse >80 km/h, ratio extrême, KV élevé
- **Décharge de responsabilité** : `disclaimer.txt`
