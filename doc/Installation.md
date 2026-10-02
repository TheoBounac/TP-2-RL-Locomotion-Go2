<p align="center">
  <img src="doc/summer.png" width="500">
</p>

 <p align="center">
  <img src="doc/im3.png" width="1000">
  <br>
 </p>
 
# <h2 align="center">SUMMER-SCHOOL-RL-WORKSHOP</h2>

**RL Locomotion tutorial with Unitree Go2 in The AI for Human–Robot Interaction summer school which will be held at the Loria and Inria Center at the Université de Lorraine, in Nancy (France) from July 6th to 10th of 2026.**

**This repository provides a Python training/deployment framework for the Unitree Go2 quadrupped robot, designed to train Reinforcement-Learning policies and deploy them in MuJoCo exactly like it would be on real hardware.**




<table align="center" style="border-collapse:collapse;">
<th style="width:30%; text-align:center;">
  <div style="display:inline-block; width:100px;">Train on Mjlab</div>
</th>

  <tr>
    <td style="width:30%; text-align:center;">
      <img src="doc/mjlab.png" style="width:400px; display:block; margin:auto;">
    </td>

  </tr>
</table>

<table align="center" style="border-collapse:collapse;">
<th style="width:30%; text-align:center;">
  <div style="display:inline-block; width:200px;">Deploy on Mujoco</div>
</th>

  <tr>
    <td style="width:30%; text-align:center;">
      <img src="doc/gif3.gif" style="width:600px; display:block; margin:auto;">
    </td>

  </tr>
</table>



---
## 📁 Architecture

```
SUMMER-SCHOOL-RL/
  ├── 1.Training/
  │     ├── unitree_go2/
  │     │    ├── xmls
  │     │    └── go2_constants.py
  │     │
  │     └── unitree_go2_velocity/
  │         ├── env_cfg.py
  │         ├── rl_cfg.py
  │         └── runner.py
  │     
  ├── 2.Deploy/
  │     ├── Unitree_mujoco/
  │     │    ├── simulate_python
  │     │    ├── terrain_tool
  │     │    └── unitree_robots
  │     │
  │     ├── Deploy_python/
  │     │   ├── common
  │     │   ├── mini_examples
  │     │   ├── policy
  │     │   ├── deploy.py
  │     │   └── deploy_to_fill.py
  │     │
  │     ├── cyclonedds
  │     └── unitree_sdk2_python
  ├── doc/
  ├── docker/
  └── README.md
```

---



# 🐳 Docker Installation

This project can also be launched entirely inside Docker.

## 1️⃣ Install Docker

Install:

- Docker
- Docker Compose

Verify installation:

```bash
docker --version
docker compose version
```

---

## 2️⃣ Clone the repository

```bash
git clone https://github.com/TheoBounac/SUMMER-SCHOOL-RL.git
cd SUMMER-SCHOOL-RL
```

---

## 3️⃣ Allow Docker to access the graphical display

```bash
xhost +local:docker
```

This allows MuJoCo and pygame windows to open correctly from the container.

---

## 4️⃣ Build the Docker image

```bash
docker compose -f docker/docker-compose.yml build --no-cache
```

The first build can take several minutes.

---

## 5️⃣ Launch the container

```bash
docker compose -f docker/docker-compose.yml run --rm summer-school-rl
```

You should now be inside the Docker container:

```bash
root@xxxxx:/workspace/SUMMER-SCHOOL-RL#
```

---

## 6️⃣ Launch MuJoCo simulation

Inside the container:

```bash
python 1.Unitree_mujoco/simulate_python/unitree_mujoco.py
```

---

## 7️⃣ Open a second terminal inside the same container

On the host machine:

```bash
docker ps
```

Copy the container name, then:

```bash
docker exec -it CONTAINER_NAME bash
```

Example:

```bash
docker exec -it summer_school_workshop_rl-summer-school-rl-run-xxxx bash
```

---

## 8️⃣ Launch deploy.py

Inside the second Docker terminal:

```bash
python 2.Deploy_python/deploy.py
```

Or without the dashboard:

```bash
python 2.Deploy_python/deploy.py --debug
```

---
---
<h2 align="center">🔧 Installation Guides🔧</h2> 

## 1️⃣ 🐍 Create & prepare the Conda environment

Create the env conda :
```bash
conda create -n go2_rl python=3.11
conda activate go2_rl
```

Install libraries :
```bash
pip install -U torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
pip install rich
pip install scipy
```

Clone project :
```bash
git clone https://github.com/TheoBounac/SUMMER-SCHOOL-RL.git
```

## 2️⃣ 🤖 Install Unitree SDK2 Python

Go to unitree_sdk2_python folder and install cyclonedds (with the right path):
```bash
cd SUMMER-SCHOOL-RL/unitree_sdk2_python
sudo apt install python3-pip
export CYCLONEDDS_HOME=~/SUMMER-SCHOOL-RL/cyclonedds/install
pip3 install -e .
```

## 3️⃣ 🏗️ Launch the Mujoco simulation

```bash
pip3 install mujoco
pip3 install pygame
python SUMMER-SCHOOL-RL/1.Unitree_mujoco/simulate_python/unitree_mujoco.py
```
You should see :

 <p align="center">
  <img src="doc/leve.png" width="900">
  <br>
 </p>

<p align="center">
Press <kbd>9</kbd> to deactivate the elastic band and <kbd>7</kbd> / <kbd>8</kbd> to raise / lower the robot.
</p>
 
You should see :
 <p align="center">
  <img src="doc/bonne.png" width="900">
  <br>
 </p>
 


---
## 4️⃣ 🚀 Launch the deploy.py code

In an other terminal (also export cyclonedds):
```bash
conda activate go2_rl
export CYCLONEDDS_HOME=~/SUMMER-SCHOOL-RL/cyclonedds/install
python SUMMER-SCHOOL-RL/2.Deploy_python/deploy.py
```
You should see :
 <p align="center">
  <img src="doc/fill.png" width="1100">
  <br>
 </p>

You can also launch the code without this graphic panel with `--debug`:
```bash
conda activate go2_rl
python SUMMER-SCHOOL-RL/2.Deploy_python/deploy.py --debug
```

---


Now you must follow the tasks and fill the `deploy.py` file:

<div align="center">
  <img src="doc/obs.png" width="1100"><br>
  <img src="doc/policy.png" width="1100" style="margin-top:-800px;"><br>
  <img src="doc/motor.png" width="1100" style="margin-top:-800px;">
</div>


When you completed all the tasks, the robot should walk and you should see :
 <p align="center">
  <img src="doc/im2.png" width="1100">
  <br>
 </p>

---
---

##  Links

These are the repositories we used for this workshop :

| 🔗 Resources | 📍 Link |
|--------------|---------|
|  **IsaacLab (NVIDIA)** | [https://github.com/isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab) |
|  **Unitree SDK2 Python** | [https://github.com/unitreerobotics/unitree_sdk2_python](https://github.com/unitreerobotics/unitree_sdk2_python) |
|  **unitree_rl_lab** | [https://github.com/unitreerobotics/unitree_rl_lab](https://github.com/unitreerobotics/unitree_rl_lab) |
|  **Mujoco** | [https://github.com/unitreerobotics/unitree_mujoco](https://github.com/unitreerobotics/unitree_mujoco) |




---

## 👥 Author & Contributors

**Author:**  
Théo Bounaceur  
Laboratory **LORIA** (CNRS / University of Lorraine), Nancy, France  
🧬 Field: Reinforcement Learning · Unitree robots · IsaacLab · IsaacGym · ROS 2 · Unitree SDK2  
📫 Contact: theo.bounaceur@loria.fr  (do not hesitate to contact me)

**Supervisors / Advisors:**  
- Adrien Guenard  
- Cyril Regan  
