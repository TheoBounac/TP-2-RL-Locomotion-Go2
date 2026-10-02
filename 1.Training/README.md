# summer-school-2026-mjlab
RL Locomotion tutorial with Unitree Go2 in The AI for Human–Robot Interaction summer school which will be held at the Loria and Inria Center at the Université de Lorraine, in Nancy (France) from July 6 to 10.

In this tutorial you will train a Unitree Go2 to walk from scratch in a flat terrain. You will configure parts of the algorithm and the enviroment which later you will train to obtain your policy.

The files you have which have an uncompleted part for you to complete are 

- `src/unitree_go2/go2_constants.py` : Used to configure most of the parameters related to the robot.

- `src/unitree_go2_velocity/env_cfg.py`: Everything related to the enviroments are configured here (rewards, domain randomization, etc.)

- `src/unitree_go2_velocity/rl_cfg.py`: Everything related to the PPO algorithm are configured here (actor, critic, PPO parameters)

- `src/unitree_go2_velocity/custom_mdp.py`: Hand-written reward/termination math functions (using
  torch directly), as opposed to the pre-built terms imported from mjlab elsewhere.

Each uncompleted part is marked with a `# TODO(Exercise N - ...)` comment, and each
TODO explains what's needed and points to a similar, already-completed piece of code
right next to it to use as a reference.

**Exercises 1-7** are config-wiring exercises: fill in a missing dict entry or
config object. Each one ends in `raise NotImplementedError(...)` placed directly in the
config-building code, so the code will fail to import until you **replace** that `raise`
with your own implementation. You'll hit exercises 1-6 one at a time, in this order:

1. **Init state** (`go2_constants.py`) — define `INIT_STATE`, the robot's default
   standing pose (position + joint angles) used at the start of every episode.
2. **Contact sensor** (`env_cfg.py`) — define `feet_ground_cfg`, the sensor that
   detects feet touching the ground.
3. **Observation** (`env_cfg.py`) — add a `joint_vel` term to the actor's observations.
4. **Event** (`env_cfg.py`) — add a `push_robot` domain-randomization event.
5. **Reward** (`env_cfg.py`) — add a `track_angular_velocity` reward term.
6. **Curriculum** (`env_cfg.py`) — add a `command_vel` curriculum term that widens the
   commanded velocity range over the course of training.
7. **Network architecture** (`rl_cfg.py`) — choose `hidden_dims` and `activation`,
   shared by both the actor and critic MLPs.

**Exercises 8-9** are different: in `custom_mdp.py` you write the actual MDP math
with torch, filling in a few `None` variables per the comment hints, instead of just
wiring together pre-built functions.

8. **Angular velocity reward** (`custom_mdp.py`) — implement `track_angular_velocity`.
9. **Fell-over termination** (`custom_mdp.py`) — implement `bad_orientation`.

To start the docker container run inside the repository folder
```bash
docker compose -f docker/docker-compose.yml run --rm summer-school-rl
```

To be able to run Mjlab commands while you are in the docker container navigate to
```bash
cd /opt/mjlab/
```

## Train the policy
After having completed the scripts, you will be able to launch you training with the following command

```bash
uv run train Mjlab-Velocity-Flat-Unitree-Go2 --env.scene.num-envs 2048 --agent.max-iterations 3_000
```

## Play the policy's latest checkpoint
To see the latest policy behavior in Mujoco during training, it will be needed to open **a new terminal** to not stop the training.
First navigate to the `/Tutorial_06_RL_Locomotion/docker` where the `docker-compose.yml` is located and run

```bash
docker compose exec -w /opt/mjlab summer-school-rl bash
```
Now you can run the following command. If you want to see more agents (robots) in parallel you can use the argument `--num.envs 10`

```bash
uv run play Mjlab-Velocity-Flat-Unitree-Go2 --checkpoint_file /workspace/SUMMER-SCHOOL-RL/logs/rsl_rl/go2_velocity/<run-name>/model_<latest-number>.pt 
```

## Play an already trained policy
Due to the time limitation of the tutorial and given many of you may not have a capable gpu, you can visualise the end result with this command with an already trained policy (50000 max iterations) based on the same configuration.
```bash
uv run play Mjlab-Velocity-Flat-Unitree-Go2 --checkpoint_file /workspace/SUMMER-SCHOOL-RL/1.Training/trained_model.pt 
```
