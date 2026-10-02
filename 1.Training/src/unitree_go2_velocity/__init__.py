import os

os.environ.setdefault("MUJOCO_GL", "egl")

from mjlab.tasks.registry import register_mjlab_task

from .env_cfg import unitree_go2_flat_env_cfg
from .rl_cfg import unitree_go2_ppo_runner_cfg

register_mjlab_task(
  task_id="Mjlab-Velocity-Flat-Unitree-Go2",
  env_cfg=unitree_go2_flat_env_cfg(),
  play_env_cfg=unitree_go2_flat_env_cfg(play=True),
  rl_cfg=unitree_go2_ppo_runner_cfg(),
)