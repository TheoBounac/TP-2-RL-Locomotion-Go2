"""Hand-written MDP terms for the Unitree Go2 velocity task.

Unlike the rest of the reward/observation/event/termination library (imported
in env_cfg.py as `mdp`, from mjlab.tasks.velocity), the functions in this file
are implemented by you, using torch directly on the simulation state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from mjlab.entity import Entity
from mjlab.managers.scene_entity_config import SceneEntityCfg

if TYPE_CHECKING:
    from mjlab.envs import ManagerBasedRlEnv

_DEFAULT_ASSET_CFG = SceneEntityCfg("robot")


def track_angular_velocity(
    env: ManagerBasedRlEnv,
    std: float,
    command_name: str,
    asset_cfg: SceneEntityCfg = _DEFAULT_ASSET_CFG,
) -> torch.Tensor:
    """Reward for tracking the commanded base yaw rate (angular velocity about z).

    The commanded xy angular velocities are assumed to be zero.
    """
    asset: Entity = env.scene[asset_cfg.name]
    command = env.command_manager.get_command(command_name)
    assert command is not None, f"Command '{command_name}' not found."
    actual = asset.data.root_link_ang_vel_b

    # TODO(Exercise 7 - Angular Velocity Reward):

    z_error = torch.square(command[:, 2] - actual[:, 2])
    xy_error = torch.sum(torch.square(actual[:, :2]), dim=1)
    ang_vel_error = z_error + xy_error

    return torch.exp(-ang_vel_error / std**2)


def bad_orientation(
    env: ManagerBasedRlEnv,
    limit_angle: float,
    asset_cfg: SceneEntityCfg = _DEFAULT_ASSET_CFG,
) -> torch.Tensor:
    """Terminate when the robot's orientation exceeds the limit angle."""
    asset: Entity = env.scene[asset_cfg.name]
    projected_gravity = asset.data.projected_gravity_b

    # TODO(Exercise 8 - Fell Over Termination):

    tilt_angle = torch.acos(-projected_gravity[:, 2]).abs()

    return tilt_angle > limit_angle
