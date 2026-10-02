# 🤖 Deployment
(Make sure you completed the docker installation)

## 1️⃣ 🏗️ Launch the MuJoCo simulator

Inside the container:

```bash
cd /workspace/SUMMER-SCHOOL-RL/2.Deploy

python Unitree_mujoco/simulate_python/unitree_mujoco.py
```
 <p align="center">
  <img src="deploy1.png" width="900">
  <br>
 </p>
 
You should see :

 <p align="center">
  <img src="leve.png" width="900">
  <br>
 </p>
 <p align="center">
The robot is hold by an invisible elastic band :
  
Press <kbd>9</kbd> to activate or deactivate the elastic band. When activated you can change the force of the elastic: SPAM <kbd>7</kbd> to raise, and SPAM <kbd>8</kbd>  to lower the robot.
</p>

Press <kbd>RESET</kbd> button in the menu at the left, to reset the robot position (make sure the elastic band is deactivate by pressing <kbd>9</kbd> on your keyboard).

See the command instruction guide for MuJoCo:
 <p align="center">
  <img src="bonne.png" width="900">
  <br>
 </p>
 
 # Important 
 Here, MuJoCo works exactly as it would be in real life: You should not exit the mujoco page, it works as if you had the robot next to you, just reset the robot each time you launch the deploy.py file for the workshop.
 
---

## 2️⃣ Open a second terminal inside the same container

On the host machine:

```bash
docker ps
```

Copy the container name, then run:

```bash
docker exec -it CONTAINER_NAME bash
```

Example:

```bash
docker exec -it docker-summer-school-rl-run-8a7194d5a1f7 bash
```
 <p align="center">
  <img src="deploy2.png" width="1100">
  <br>
 </p>
 
---

## 3️⃣ Launch the deployment script

Inside the second Docker terminal:

```bash
cd /workspace/SUMMER-SCHOOL-RL/2.Deploy

python Deploy_python/deploy.py
MAKE SURE THE ROBOT IS LAID DOWN, RESET WITH ELASTIC BAND DISABLED.
```
You should see :
 <p align="center">
  <img src="fill.png" width="1100">
  <br>
 </p>
 
Or without the dashboard with with `--debug`:

```bash
python Deploy_python/deploy.py --debug
```

At the begining, the deploy file does not work well until you complete the workshop. So the robot will just fall after standing up:

 <p align="center">
  <img src="im4.png" width="800">
  <br>
 </p>
 
## 4️⃣ 🚀 Complete the workshop

This is the end of the preparation. 
During the summer school week, students will be asked to do the tasks required to train and deploy a policy for the Go2 locomotion.
When you complete all the tasks, the robot should walk and you should see :
 <p align="center">
  <img src="im2.png" width="1100">
  <br>
 </p>

<table align="center" style="border-collapse:collapse;">
<th style="width:30%; text-align:center;">
  <div style="display:inline-block; width:200px;">Deploy file completed</div>
</th>

  <tr>
    <td style="width:30%; text-align:center;">
      <img src="gif3.gif" style="width:600px; display:block; margin:auto;">
    </td>

  </tr>
</table>

---
