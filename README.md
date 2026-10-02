<p align="center">
  <img src="doc/banniere.png" width="1000">
</p>

 <div align="justify">
Le réseau métier des roboticiens et mécatroniciens du CNRS organise des journées thématiques sur les robots quadrupèdes et humanoïdes afin de favoriser le partage de connaissances et les retours d’expérience autour de ces robots. Cette journée est cofinancée par le réseau 2RM et INRIA. [12 et 13 octobre 2026].
</div>

 ---

 
# TP2 — RL pour la locomotion du robots Unitree Go2

Ce TP est le second TP des journées thématiques *robotique quadrupède et humanoïde 2026*.

L'objectif pour les participants est de comprendre et tester un modèle de contrôle entraîné par apprentissage par renforcement pour la locomotion du robot Unitree Go2.

 <p align="center">
  <img src="doc/im3.png" width="1000">
  <br>
 </p>

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

## 📑 Sommaire

1. [Principe de fonctionnement du système](#principe)
2. [Matériel nécessaire](#composants)
3. [Montage de l'Emetteur](#transmetteur)
4. [Montage du Récepteur](#recepteurvrai)
5. [Fonctionnement logique](#logique)
6. [Test avec une LED](#test-led)
7. [Test sur le robot](#test-robot)


---
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



# 📝 Installation guide
For the summer school tutorial, students are required to install this workshop using Docker. Please follow this guide. It is designed so that you normally only need to copy and paste the commands into the terminal. If you have any trouble, please contact us theo.bounaceur@loria.fr & ioannis.loizou@inria.fr.

You should normally follow the instructions at [https://github.com/aixhri-summer-school-2026/docker-tutorials/tree/main](https://github.com/aixhri-summer-school-2026/docker-tutorials/tree/main).

Otherwise, you can also install only this workshop following this instruction : **🐳 Docker** : [📘 Docker Installation](doc/Docker.md)

In any case, once the docker is installed you can try to launch it:

🏋️ Training (MJLab)

**Part 1** : [📘 Training instruction](doc/training_instruction.md)

🤖 Deployment

**Part 2** : [📘 Deploy instruction](doc/deploy_instruction.md)


---

##  Links

These are the repositories we used for this workshop :

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
- Adrien Guenard  
- Cyril Regan
- Serena Ivaldi  
