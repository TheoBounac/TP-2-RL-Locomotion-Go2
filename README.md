<p align="center">
  <img src="doc/summer.png" width="500">
</p>

 <p align="center">
  <img src="doc/im3.png" width="1000">
  <br>
 </p>
 
# <h2 align="center">SUMMER-SCHOOL-RL-WORKSHOP</h2>

**RL Locomotion tutorial with Unitree Go2 in The AI for Human–Robot Interaction summer school which will be held at the Loria and Inria Center at the Université de Lorraine, in Nancy (France) from July 6th to 10th of 2026.**

**This repository provides a Python training/deployment framework for the Unitree Go2 quadruped robot, designed to train Reinforcement-Learning policies and deploy them in MuJoCo exactly like it would be on real hardware.**




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
