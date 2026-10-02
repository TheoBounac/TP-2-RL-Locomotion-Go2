<p align="center">
  <img src="doc/banniere.png" width="1000">
</p>

 <div align="justify">
Le réseau métier des roboticiens et mécatroniciens du CNRS organise des journées thématiques sur les robots quadrupèdes et humanoïdes afin de favoriser le partage de connaissances et les retours d’expérience autour de ces robots. Cette journée est cofinancée par le réseau 2RM et INRIA. [12 et 13 octobre 2026].
</div>

 ---

 
# TP2 — RL pour la locomotion du robot Unitree Go2

Ce TP est le second TP des journées thématiques *robotique quadrupède et humanoïde 2026*.

L'objectif pour les participants est de comprendre et tester un modèle de contrôle entraîné par apprentissage par renforcement pour la locomotion du robot Unitree Go2.

## 📑 Sommaire

1. [Architecture](#Architecture)
2. [Installation guide](#Installation)
3. [Partie 1: Entraînement](#Entraînement)
4. [Partie 2: Déploiement ](#Déploiement )

**Ce dépôt fournit un framework Python pour l’entraînement et le déploiement du robot quadrupède Unitree Go2. Il est conçu pour entraîner des politiques par apprentissage par renforcement (Reinforcement Learning) et les déployer dans MuJoCo de la même manière qu’elles le seraient sur le robot réel.**




<table align="center" style="border-collapse:collapse;">
<th style="width:30%; text-align:center;">
  <div style="display:inline-block; width:100px;">Entraînement sur Mjlab</div>
</th>

  <tr>
    <td style="width:30%; text-align:center;">
      <img src="doc/mjlab.png" style="width:400px; display:block; margin:auto;">
    </td>

  </tr>
</table>

<table align="center" style="border-collapse:collapse;">
<th style="width:30%; text-align:center;">
  <div style="display:inline-block; width:200px;">Déploiement sur Mujoco</div>
</th>

  <tr>
    <td style="width:30%; text-align:center;">
      <img src="doc/gif3.gif" style="width:600px; display:block; margin:auto;">
    </td>

  </tr>
</table>

---
<a id="Architecture"></a>
## 📁 Architecture

```
SUMMER-SCHOOL-RL/
  ├── 1.Training/
  │     └── src/
  │          ├── unitree_go2/
  │          │    ├── xmls
  │          │    └── go2_constants.py
  │          │
  │          └── unitree_go2_velocity/
  │               ├── env_cfg.py
  │               ├── rl_cfg.py
  │               └── runner.py
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
<a id="Installation"></a>
# 📝 Installation guide
Pour ce tutoriel, les participants doivent installer l'image Docker déjà construite. Veuillez suivre ce guide. Il est conçu pour que vous n’ayez normalement qu’à copier-coller les commandes dans le terminal. Si vous rencontrez un problème, veuillez nous contacter : theo.bounaceur@loria.fr & adrien.guenard@loria.fr.

**🐳 Docker** : [📘 Installation avec Docker](doc/Docker.md)

---
<a id="Entraînement"></a>
# 🏋️ Partie 1: Entraînement 
Une fois le Docker téléchargé, vous pouvez essayer de le lancer.

(Make sure you completed the docker installation)

Inside the container, go to the MJLab workspace:

```bash
cd /opt/mjlab
```
You should see:
<p align="center">
  <img src="docker1.png" width="900">
</p>

---

Launch the Go2 environment with a random policy:

```bash
uv run play Mjlab-Velocity-Flat-Unitree-Go2 --agent random
```
You should see:
<p align="center">
  <img src="docker2.png" width="900">
  <img src="docker3.png" width="900">
</p>

---

You can try to launch the training script, which is incompleted (students will complete it during the summer shcoool)

Start training:

```bash
uv run train Mjlab-Velocity-Flat-Unitree-Go2 --env.scene.num-envs 1024
```
Enter choice 3:
<p align="center">
  <img src="docker4.png" width="900">
</p>

You should see the logs:
<p align="center">
  <img src="docker5.png" width="900">
</p>

---
<a id="Déploiement"></a>
# 🤖 Partie 2: Déploiement 
(MuJoCo)
[📘 Instructions de déploiement](doc/deploy_instruction.md)


---
##  Liens

Voici les dépôts que nous avons utilisés pour ce workshop :

| 🔗 Resources | 📍 Link |
|--------------|---------|
|  **Unitree SDK2 Python** | [https://github.com/unitreerobotics/unitree_sdk2_python](https://github.com/unitreerobotics/unitree_sdk2_python) |
|  **unitree_rl_lab** | [https://github.com/unitreerobotics/unitree_rl_lab](https://github.com/unitreerobotics/unitree_rl_lab) |
|  **Mujoco** | [https://github.com/unitreerobotics/unitree_mujoco](https://github.com/unitreerobotics/unitree_mujoco) |
|  **Mjlab** | [https://github.com/mujocolab/mjlab](https://github.com/mujocolab/mjlab) |





---
## 👥 Authors & Contributors

**Author:**  
Théo Bounaceur & Ioannis Loizou (PhD student)  
Laboratory **LORIA** (CNRS / University of Lorraine), Nancy, France  
🧬 Field: Reinforcement Learning · Unitree robots · Unitree SDK2 · IsaacLab · IsaacGym · MuJoCo · ROS2  
📫 Contact: theo.bounaceur@loria.fr & ioannis.loizou@inria.fr

**Supervisors / Advisors:**  
- Adrien Guenard, Ingénieur robotique, Loria 
- Cyril Regan, Ingénieur I.A., Loria
- Serena Ivaldi, Chercheuse en robotique, Loria
  
