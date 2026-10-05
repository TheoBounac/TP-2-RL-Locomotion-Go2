<h2 align="center">🐳 Installation de Docker</h2>

Ce projet peut être lancé entièrement à l’intérieur du conteneur Docker que vous allez Télécharger (ou construire en option).

L’image Docker installe automatiquement toutes les dépendances nécessaires pour :

* **L’entraînement** (MJLab + MuJoCo Warp)
* **Le déploiement** (Unitree SDK2 + CycloneDDS + simulateur MuJoCo)

Aucune installation manuelle de MJLab, MuJoCo, CycloneDDS ou du SDK Unitree n’est nécessaire.

---

## 1️⃣ Installer Docker

Installez :

* Docker
* Docker Compose

Vérifiez l’installation :

```bash
docker --version
docker compose version
```

---

## 2️⃣ Cloner le dépôt

```bash
git clone https://github.com/aixhri-summer-school-2026/Tutorial_06_RL_Locomotion.git
cd SUMMER-SCHOOL-RL
```

---

## 3️⃣ Autoriser Docker à accéder à l’affichage graphique

```bash
xhost +local:docker
```

Cela permet aux fenêtres MuJoCo, MJLab et pygame de s’ouvrir correctement depuis le conteneur.

---

## 4️⃣ Télécharger l’image Docker

>
> ```bash
> docker pull adriengloria/tutorl:latest
> docker tag adriengloria/tutorl:latest tp-rl-2rm:latest
> docker rmi adriengloria/tutorl:latest
> ```

---

## 5️⃣ Lancer le conteneur

```bash
docker compose -f docker/docker-compose.yml run --rm tp-rl-2rm
```

> **Dépannage :** Si Docker ne parvient pas à accéder au GPU NVIDIA, testez-le avec :
>
> ```bash
> docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
> ```
>
> Si cette commande retourne une erreur, installez et configurez NVIDIA Container Toolkit :
>
> ```bash
> sudo apt update
> sudo apt install -y nvidia-container-toolkit
> sudo nvidia-ctk runtime configure --runtime=docker
> sudo systemctl restart docker
> ```

Vous devriez maintenant être à l’intérieur du conteneur Docker :

```bash
root@xxxxx:/workspace/SUMMER-SCHOOL-RL#
```

## 4️⃣ Construire l’image Docker

```bash
docker compose -f docker/docker-compose.yml build
```

> **Remarque :** La première construction de l’image peut prendre plusieurs minutes (30 min à 1 h), car elle installe MJLab, MuJoCo Warp, Unitree SDK2, CycloneDDS ainsi que toutes les dépendances Python.

> **Dépannage :** Si `uv` échoue à cause d’un délai d’attente réseau, augmentez le délai HTTP :
>
> ```bash
> export UV_HTTP_TIMEOUT=300s
> ```

---

Vous pouvez maintenant tester la Partie 1 et la Partie 2 afin de vérifier que tout fonctionne correctement.
