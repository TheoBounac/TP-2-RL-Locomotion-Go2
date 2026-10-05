# 🤖 Partie 2: Déploiement 

## 1️⃣ Lancer le simulateur MuJoCo

Dans le conteneur :

```bash id="mujoco-launch"
cd /workspace/SUMMER-SCHOOL-RL/2.Deploy

python Unitree_mujoco/simulate_python/unitree_mujoco.py
```

<p align="center">
  <img src="../doc/deploy1.png" width="800">
  <br>
</p>
 
Vous devriez voir :

<p align="center">
  <img src="../doc/leve.png" width="800">
  <br>
</p>

<p align="center">
Le robot est maintenu par un élastique invisible :
  
Appuyez sur <kbd>9</kbd> pour activer ou désactiver l’élastique. Lorsqu’il est activé, vous pouvez modifier la force de l’élastique : appuyez plusieurs fois sur <kbd>7</kbd> pour lever le robot et plusieurs fois sur <kbd>8</kbd> pour l’abaisser.
</p>

Appuyez sur le bouton <kbd>RESET</kbd> dans le menu à gauche pour réinitialiser la position du robot (assurez-vous que l’élastique est désactivé en appuyant sur <kbd>9</kbd> sur votre clavier).

Consultez le guide des commandes de MuJoCo :

<p align="center">
  <img src="../doc/bonne.png" width="800">
  <br>
</p>
 
# Important

Ici, MuJoCo fonctionne exactement comme en conditions réelles : vous ne devez pas fermer la fenêtre MuJoCo. Cela fonctionne comme si vous aviez le robot à côté de vous. Réinitialisez simplement le robot chaque fois que vous lancez le fichier `deploy.py` pendant le workshop, en appuyant sur le bouton reset entouré en rouge dans l’image précédente.
 
---

## 2️⃣ Ouvrir un second terminal dans le même conteneur

Sur la machine hôte :

```bash id="docker-ps"
docker ps
```

Copiez le nom du conteneur, puis exécutez :

```bash id="docker-exec"
docker exec -it CONTAINER_NAME bash
```

Exemple :

```bash id="docker-exec-example"
docker exec -it docker-summer-school-rl-run-8a7194d5a1f7 bash
```

<p align="center">
  <img src="../doc/deploy2.png" width="900">
  <br>
</p>
 
---

## 3️⃣ Lancer le script de déploiement

Dans le second terminal Docker :

```bash id="deploy-launch"
cd /workspace/SUMMER-SCHOOL-RL/2.Deploy

python Deploy_python/deploy.py
```

**ASSUREZ-VOUS QUE LE ROBOT EST ALLONGÉ ET RÉINITIALISÉ, AVEC L’ÉLASTIQUE DÉSACTIVÉ.**

Vous devriez voir :

<p align="center">
  <img src="../doc/fill.png" width="900">
  <br>
</p>
 
Ou sans le tableau de bord, avec l’option `--debug` :

```bash id="deploy-debug"
python Deploy_python/deploy.py --debug
```

Au début, le fichier de déploiement ne fonctionne pas correctement tant que vous n’avez pas terminé le workshop. Le robot va donc simplement tomber après s’être relevé :

<p align="center">
  <img src="../doc/im4.png" width="800">
  <br>
</p>
 
## 4️⃣ Réaliser les tâches du TP

La préparation est maintenant terminée.

Pendant la semaine de la summer school, les étudiants devront réaliser les différentes tâches nécessaires pour entraîner puis déployer une politique de locomotion pour le Go2.

Lorsque vous aurez terminé toutes les tâches, le robot devrait marcher et vous devriez voir :

<p align="center">
  <img src="../doc/im2.png" width="900">
  <br>
</p>

<table align="center" style="border-collapse:collapse;">
  <th style="width:30%; text-align:center;">
    <div style="display:inline-block; width:200px;">Fichier de déploiement complété</div>
  </th>
  <tr>
    <td style="width:30%; text-align:center;">
      <img src="../doc/gif3.gif" style="width:600px; display:block; margin:auto;">
    </td>
  </tr>
</table>
