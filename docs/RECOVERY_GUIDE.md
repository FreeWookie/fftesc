# Guide de Récupération du Contrôleur FTESC

## Cas d'usage

Ce guide s'applique lorsque :
- Le contrôleur FTESC ne répond plus (aucune connexion UART possible)
- Le contrôleur ne fait aucun bip au démarrage
- Après une surtension ou une erreur de flashage ayant corrompu le firmware
- Le contrôleur est bloqué dans un état inconnu

## Procédure de Récupération UART (Recommandée en première intention)

Cette procédure utilise l'interface UART normale du contrôleur pour forcer le redémarrage en mode bootloader natif.

### Étapes :

1. **Lancer FFTESC Tool**
   - Assurez-vous que votre contrôleur est connecté via USB/UART
   - Lancez l'application FFTESC

2. **Accéder à la Zone de Récupération**
   - Dans la barre latérale gauche, cliquez sur le bouton **"🆘 Réanimation"** (en bas, couleur rouge)
   - Une fenêtre modale s'ouvre avec les options de récupération

3. **Forcer le Mode Bootloader**
   - Cliquez sur le bouton **"Forcer le mode Bootloader"**
   - Une fenêtre de confirmation apparaît pour prévenir de l'action irréversible
   - Confirmez en cliquant sur **"Oui"**

4. **Redémarrage du Contrôleur**
   - Le contrôleur reçoit la commande et redémarre immédiatement en mode bootloader
   - FFTESC se déconnecte automatiquement (le contrôleur n'est plus en mode application normale)
   - Vous verrez un message de confirmation : "Le contrôleur redémarre en mode bootloader"

5. **Flasher le Firmware**
   - Utilisez un outil de flashage UART compatible (ex: STM32CubeProgrammer, dfu-util, ou l'outil officiel FTESC)
   - Chargez le fichier firmware officiel `.bin` correspondant à votre modèle de contrôleur
   - Effectuez l'opération de flashage selon les instructions de l'outil choisi
   - Une fois le flashage terminé, redémarrez le contrôleur (débranchez/rebranchez l'alimentation)

## Procédure de Récupération ST-Link (En dernier recours)

Utilisez cette procédure uniquement si la méthode UART échoue et que vous disposez d'un adaptateur ST-Link V2/V3.

### Prérequis :
- Adaptateur ST-Link V2 ou V3
- Câbles de connexion (ou câble adaptateur)
- STM32CubeProgrammer installé (téléchargeable sur le site STMicroelectronics)

### Étapes :

1. **Câblage ST-Link → FTESC**
   Connectez les broches suivant le schéma ci-dessous :
   ```
   ST-Link     →  FTESC (FT85BD)
   ------------------------------
   SWDIO       →  PA13
   SWCLK       →  PA14
   GND         →  GND
   3.3V        →  3.3V
   NRST        →  NRST (optionnel, permet le reset matériel)
   ```

   **Important** : 
   - Assurez-vous que l'alimentation du FTESC est **coupée** avant de connecter le 3.3V du ST-Link.
   - Certains modèles de contrôleur peuvent avoir les broches SWD sur des pads de test - référez-vous au schéma électrique de votre carte.

2. **Lancer STM32CubeProgrammer**
   - Lancez l'application STM32CubeProgrammer
   - En mode de connexion, sélectionnez **"SWV"** (Single Wire View) ou **"SWD"** comme interface
   - Le logiciel devrait détecter le périphérique STM32Fxxx

3. **Vérification de la Connexion**
   - Cliquez sur **"Connect"** pour établir la liaison
   - Si la connexion réussit, vous pouvez lire l'ID de la puce et vérifier la mémoire flash

4. **Effacer et Reprogrammer**
   - Dans l'onglet "Erasing & Programming", choisissez :
     - "Erase all" pour effacer complètement la mémoire flash (recommandé en cas de corruption)
     - Puis sélectionnez le fichier firmware officiel `.bin`
     - Cliquez sur "Start Programming"
   - Attendez la fin de l'opération de programmation

5. **Redémarrage**
   - Une fois le flashage terminé, débranchez le ST-Link
   - Remettez l'alimentation normale du contrôleur (USB ou autre source)
   - Le contrôleur devrait démarrer avec le nouveau firmware

## Avertissements Importants

⚠️ **Cette opération est à vos risques et périls.**
- Une mauvaise connexion ou un fichier de firmware incorrect peut rendre le contrôleur définitivement inutilisable ("brick").
- La récupération via ST-Link annule généralement la garantie du dispositif.
- Assurez-vous d'utiliser exclusivement le firmware officiel correspondant exactement à votre modèle de contrôleur.
- En cas de doute, sollicitez l'aide de la communauté FTESC ou du fabricant de votre ESC.

## Liens Utiles

- [STM32CubeProgrammer - Site officiel STMicroelectronics](https://www.st.com/en/development-tools/stm32cubeprog.html)
- [Firmware officiel FTESC (référentiel GitHub)](https://github.com/FlightControl/FTESC-firmware)
- [Guide de câblage ST-Link général (UM1750)](https://www.st.com/resource/en/user_manual/dm00181729-st-link-v2-usb-interface-for-stm32-microcontroller-debug-stm32cube-programming-stm32cube-programmer-stmicroelectronics.pdf)

## Dépannage

| Symptomatique | Solution Possible |
|--------------|-------------------|
| Aucun détecteur en UART après "Forcer Bootloader" | Vérifiez les câbles USB/UART, essayez un autre port, assurez-vous que le contrôleur est bien alimenté |
| STM32CubeProgrammer ne détecte pas le périphérique en SWD | Vérifiez le câblage (SWDIO, SWCLK, GND, 3.3V), assurez-vous que le NRST est bien connecté si utilisé pour le reset, réduisez la vitesse de connexion dans STM32CubeProgrammer |
| Erreur de vérification après flashage | Réessayez le flashage, effacez complètement la flash avant de reprogrammer, vérifiez l'intégrité du fichier .bin |
| Le contrôleur chauffe anormalement après récupération | Débranchez immédiatement, vérifiez que vous avez utilisé le bon firmware et que aucune broche n'est en court-circuit |

## Notes Techniques

- La commande UART `ENTER_BOOTLOADER` (ID 60) force un saut vers l'adresse du bootloader natif stocké dans la zone de mémoire système du microcontrôleur STM32.
- Le bootloader natif STM32 permet le flashage via UART (USART1) en utilisant le protocole série standard (compatible avec les outils DFU classiques).
- En cas de corruption sévère de la zone de bootloader, seule la méthode ST-Link peut permettre une récupération.