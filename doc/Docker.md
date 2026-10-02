<h2 align="center">🐳 Docker Installation</h2>

This project can be launched entirely inside the Docker container you are about to build.

The Docker image automatically installs all dependencies required for both:

* **Training** (MJLab + MuJoCo Warp)
* **Deployment** (Unitree SDK2 + CycloneDDS + MuJoCo simulator)

No manual installation of MJLab, MuJoCo, CycloneDDS, or the Unitree SDK is required.

---

## 1️⃣ Install Docker

Install:

* Docker
* Docker Compose

Verify the installation:

```bash
docker --version
docker compose version
```

---

## 2️⃣ Clone the repository

```bash
git clone https://github.com/aixhri-summer-school-2026/Tutorial_06_RL_Locomotion.git
cd SUMMER-SCHOOL-RL
```

---

## 3️⃣ Allow Docker to access the graphical display

```bash
xhost +local:docker
```

This allows MuJoCo, MJLab, and pygame windows to open correctly from the container.

---

## 4️⃣ Build the Docker image

```bash
docker compose -f docker/docker-compose.yml build
```

> **Note:** The first build can take several minutes (30min - 1h) because it installs MJLab, MuJoCo Warp, Unitree SDK2, CycloneDDS, and all Python dependencies.

> **Troubleshooting:** If uv fails with a network timeout, increase the HTTP timeout:
export UV_HTTP_TIMEOUT=300s
---

## 5️⃣ Launch the container

```bash
docker compose -f docker/docker-compose.yml run --rm summer-school-rl
```

> **Troubleshooting:** If Docker cannot access the NVIDIA GPU, test it with: ```docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi```. If this command returns an error, install and configure the NVIDIA Container Toolkit:```sudo apt update``` + ```sudo apt install -y nvidia-container-toolkit``` + ```sudo nvidia-ctk runtime configure --runtime=``` + ```sudo systemctl restart docker```


You should now be inside the Docker container:

```bash
root@xxxxx:/workspace/SUMMER-SCHOOL-RL#
```

---

You can now test Part 1 and Part 2 to make sure everything works as expected.

