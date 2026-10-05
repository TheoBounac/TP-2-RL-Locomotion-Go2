<h2 align="center">🐳 Installation de Docker</h2>

Ce projet peut être lancé entièrement à l’intérieur du conteneur Docker que vous allez Télécharger .

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
git clone https://github.com/TheoBounac/TP-2-RL-Locomotion-Go2
cd TP-2-RL-Locomotion-Go2
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

## 4️⃣(BIS) Option: vous pouvez aussi construire l'image

```bash
docker compose -f docker/docker-compose.yml build
```

> **Note:** The first build can take several minutes (30 min - 1 h) because it installs MJLab, MuJoCo Warp, Unitree SDK2, CycloneDDS, and all Python dependencies.

> **Troubleshooting:** If `uv` fails due to a network timeout, increase the HTTP timeout:
> ```bash
> export UV_HTTP_TIMEOUT=300s
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
root@xxxxx:/workspace/TP-RL-2RM#
```
---


