# 🏋️ Training (MJLab)
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
