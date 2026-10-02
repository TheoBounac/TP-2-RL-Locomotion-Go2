"""Unitree Go2 velocity environment configurations. File adapted from MJlab repository (https://github.com/mujocolab/mjlab)"""

import math
from typing import Literal, TYPE_CHECKING

from unitree_go2.go2_constants import (
    GO2_ACTION_SCALE,
    get_go2_robot_cfg,
)
from . import custom_mdp

from mjlab.envs import ManagerBasedRlEnvCfg
from mjlab.envs.mdp import dr
from mjlab.envs.mdp.actions import JointPositionActionCfg
from mjlab.managers import TerminationTermCfg
from mjlab.managers.action_manager import ActionTermCfg
from mjlab.managers.command_manager import CommandTermCfg
from mjlab.managers.curriculum_manager import CurriculumTermCfg
from mjlab.managers.event_manager import EventTermCfg
from mjlab.managers.metrics_manager import MetricsTermCfg
from mjlab.managers.reward_manager import RewardTermCfg
from mjlab.managers.observation_manager import ObservationGroupCfg, ObservationTermCfg
from mjlab.utils.noise import UniformNoiseCfg as Unoise
from mjlab.managers.scene_entity_config import SceneEntityCfg
from mjlab.scene import SceneCfg
from mjlab.sensor import (
    ContactMatch,
    ContactSensorCfg,
    ObjRef,
    RingPatternCfg,
    TerrainHeightSensorCfg,
)
from mjlab.sim import MujocoCfg, SimulationCfg
from mjlab.tasks.velocity import mdp
from mjlab.tasks.velocity.mdp import UniformVelocityCommandCfg
from mjlab.terrains import TerrainEntityCfg
from mjlab.viewer import ViewerConfig


def unitree_go2_flat_env_cfg(play: bool = False) -> ManagerBasedRlEnvCfg:
    """Create Unitree Go2 flat terrain velocity configuration."""

    ##
    # Sensors
    ##

    site_names = ("FR", "FL", "RR", "RL")
    geom_names = tuple(f"{name}_foot_collision" for name in site_names)

    foot_height_scan = TerrainHeightSensorCfg(
        name="foot_height_scan",
        frame=tuple(ObjRef(type="site", name=s, entity="robot") for s in site_names),
        pattern=RingPatternCfg.single_ring(radius=0.04, num_samples=4),
        ray_alignment="yaw",
        max_distance=1.0,
        exclude_parent_body=True,
        include_geom_groups=(0,),  # Terrain only.
        debug_vis=False,
        viz=TerrainHeightSensorCfg.VizCfg(
            show_rays=False,
            hit_color=(1.0, 0.0, 1.0, 0.8),  # Magenta rays.
            hit_sphere_color=(1.0, 0.0, 1.0, 1.0),
        ),
    )

    # TODO(Exercise 2 - Contact Sensor): 
    
    feet_ground_cfg = ContactSensorCfg(
        name="feet_ground_contact",
        primary=ContactMatch(mode="geom", pattern=geom_names, entity="robot"),
        secondary=ContactMatch(mode="body", pattern="terrain"),
        fields=("found", "force"),
        reduce="netforce",
        num_slots=1,
        track_air_time=True,
    )

    nonfeet_ground_cfg = ContactSensorCfg(
        name="nonfeet_ground_touch",
        primary=ContactMatch(
            mode="geom",
            entity="robot",
            # Grab all collision geoms...
            pattern=r".*_collision\d*$",
            # Except for the foot geoms.
            exclude=tuple(geom_names),
        ),
        secondary=ContactMatch(mode="body", pattern="terrain"),
        fields=("found", "force"),
        reduce="none",
        num_slots=1,
        history_length=4,
    )

    scene = SceneCfg(
        terrain=TerrainEntityCfg(terrain_type="plane"),
        entities={"robot": get_go2_robot_cfg()},
        sensors=(foot_height_scan, feet_ground_cfg, nonfeet_ground_cfg),
        num_envs=1,
        extent=2.0,
    )

    ##
    # Observations
    ##

    # TODO(Exercise 3 - Observation): 

    actor_terms = {
        "base_ang_vel": ObservationTermCfg(
            func=mdp.builtin_sensor,
            params={"sensor_name": "robot/imu_ang_vel"},
            noise=Unoise(n_min=-0.2, n_max=0.2),
            scale=0.25,
        ),
        "projected_gravity": ObservationTermCfg(
            func=mdp.projected_gravity,
            noise=Unoise(n_min=-0.05, n_max=0.05),
            scale=1.0,
        ),
        "command": ObservationTermCfg(
            func=mdp.generated_commands,
            params={"command_name": "twist"},
            scale=(3.0, 2.0, 0.5),
        ),
        "joint_pos": ObservationTermCfg(
            func=mdp.joint_pos_rel,
            noise=Unoise(n_min=-0.01, n_max=0.01),
            scale=1.0,
        ),
        "joint_vel": ObservationTermCfg(
            func=mdp.joint_vel_rel,
            noise=Unoise(n_min=-1.5, n_max=1.5),
            scale=0.05,
        ),
        "actions": ObservationTermCfg(
            func=mdp.last_action,
            scale=1.0,
        ),
    }

    critic_terms = {
        **actor_terms,
        "foot_height": ObservationTermCfg(
            func=mdp.foot_height,
            params={"sensor_name": "foot_height_scan"},
        ),
        "foot_air_time": ObservationTermCfg(
            func=mdp.foot_air_time,
            params={"sensor_name": "feet_ground_contact"},
        ),
        "foot_contact": ObservationTermCfg(
            func=mdp.foot_contact,
            params={"sensor_name": "feet_ground_contact"},
        ),
        "foot_contact_forces": ObservationTermCfg(
            func=mdp.foot_contact_forces,
            params={"sensor_name": "feet_ground_contact"},
        ),
    }

    observations = {
        "actor": ObservationGroupCfg(
            terms=actor_terms,
            concatenate_terms=True,
            enable_corruption=not play,
        ),
        "critic": ObservationGroupCfg(
            terms=critic_terms,
            concatenate_terms=True,
            enable_corruption=False,
        ),
    }

    ##
    # Metrics
    ##

    metrics = {
        "mean_action_acc": MetricsTermCfg(
            func=mdp.mean_action_acc,
        ),
    }

    ##
    # Actions
    ##

    actions: dict[str, ActionTermCfg] = {
        "joint_pos": JointPositionActionCfg(
            entity_name="robot",
            actuator_names=(".*",),
            scale=GO2_ACTION_SCALE,  # Override per-robot.
            use_default_offset=True,
        )
    }

    ##
    # Commands
    ##

    commands: dict[str, CommandTermCfg] = {
        "twist": UniformVelocityCommandCfg(
            entity_name="robot",
            resampling_time_range=(3.0, 8.0),
            rel_standing_envs=0.1,
            rel_heading_envs=0.3,
            rel_forward_envs=0.2,
            heading_command=True,
            heading_control_stiffness=0.5,
            debug_vis=True,
            ranges=UniformVelocityCommandCfg.Ranges(
                lin_vel_x=(-1.0, 1.0),
                lin_vel_y=(-1.0, 1.0),
                ang_vel_z=(-0.5, 0.5),
                heading=(-math.pi, math.pi),
            ),
        )
    }

    ##
    # Events
    ##

    # TODO(Exercise 4 - Event):

    events = {
        "reset_base": EventTermCfg(
            func=mdp.reset_root_state_uniform,
            mode="reset",
            params={
                "pose_range": {
                    "x": (-0.5, 0.5),
                    "y": (-0.5, 0.5),
                    "z": (0.01, 0.05),
                    "yaw": (-3.14, 3.14),
                },
                "velocity_range": {},
            },
        ),
        "reset_robot_joints": EventTermCfg(
            func=mdp.reset_joints_by_offset,
            mode="reset",
            params={
                "position_range": (0.0, 0.0),
                "velocity_range": (0.0, 0.0),
                "asset_cfg": SceneEntityCfg("robot", joint_names=(".*",)),
            },
        ),
        "foot_friction_slide": EventTermCfg(
            mode="startup",
            func=dr.geom_friction,
            params={
                "asset_cfg": SceneEntityCfg("robot", geom_names=geom_names),
                "operation": "abs",
                "axes": [0],
                "ranges": (0.3, 1.5),
                "shared_random": True,
            },
        ),
        "foot_friction_spin": EventTermCfg(
            mode="startup",
            func=dr.geom_friction,
            params={
                "asset_cfg": SceneEntityCfg("robot", geom_names=geom_names),
                "operation": "abs",
                "distribution": "log_uniform",
                "axes": [1],
                "ranges": (1e-4, 2e-2),
                "shared_random": True,
            },
        ),
        "foot_friction_roll": EventTermCfg(
            mode="startup",
            func=dr.geom_friction,
            params={
                "asset_cfg": SceneEntityCfg("robot", geom_names=geom_names),
                "operation": "abs",
                "distribution": "log_uniform",
                "axes": [2],
                "ranges": (1e-5, 5e-3),
                "shared_random": True,
            },
        ),
        "encoder_bias": EventTermCfg(
            mode="startup",
            func=dr.encoder_bias,
            params={
                "asset_cfg": SceneEntityCfg("robot"),
                "bias_range": (-0.015, 0.015),
            },
        ),
        "base_com": EventTermCfg(
            mode="startup",
            func=dr.body_com_offset,
            params={
                "asset_cfg": SceneEntityCfg("robot", body_names=("base_link",)),  # Set per-robot.
                "operation": "add",
                "ranges": {
                    0: (-0.025, 0.025),
                    1: (-0.025, 0.025),
                    2: (-0.03, 0.03),
                },
            },
        ),
        "push_robot": EventTermCfg(
            func=mdp.push_by_setting_velocity,
            mode="interval",
            interval_range_s=(1.0, 3.0),
            params={
                "velocity_range": {
                    "x": (-0.5, 0.5),
                    "y": (-0.5, 0.5),
                    "z": (-0.4, 0.4),
                    "roll": (-0.52, 0.52),
                    "pitch": (-0.52, 0.52),
                    "yaw": (-0.78, 0.78),
                }
            },
        ),
    }

    ##
    # Rewards
    ##

    # TODO(Exercise 5 - Reward):

    rewards = {
        "track_linear_velocity": RewardTermCfg(
            func=mdp.track_linear_velocity,
            weight=2.0,
            params={"command_name": "twist", "std": math.sqrt(0.25)},
        ),
        "track_angular_velocity": RewardTermCfg(
            func=custom_mdp.track_angular_velocity,
            weight=2.0,
            params={"command_name": "twist", "std": math.sqrt(0.5)},
        ),
        "upright": RewardTermCfg(
            func=mdp.upright,
            weight=1.0,
            params={
                "std": math.sqrt(0.2),
                "asset_cfg": SceneEntityCfg("robot", body_names=("base_link",)),
            },
        ),
        "pose": RewardTermCfg(
            func=mdp.variable_posture,
            weight=1.0,
            params={
                "asset_cfg": SceneEntityCfg("robot", joint_names=(".*",)),
                "command_name": "twist",
                "std_standing": {
                    r".*(FR|FL|RR|RL)_(hip|thigh)_joint.*": 0.05,
                    r".*(FR|FL|RR|RL)_calf_joint.*": 0.1,
                },
                "std_walking": {
                    r".*(FR|FL|RR|RL)_(hip|thigh)_joint.*": 0.3,
                    r".*(FR|FL|RR|RL)_calf_joint.*": 0.6,
                },
                "std_running": {
                    r".*(FR|FL|RR|RL)_(hip|thigh)_joint.*": 0.3,
                    r".*(FR|FL|RR|RL)_calf_joint.*": 0.6,
                },
                "walking_threshold": 0.05,
                "running_threshold": 1.5,
            },
        ),
        "dof_pos_limits": RewardTermCfg(func=mdp.joint_pos_limits, weight=-1.0),
        "action_rate_l2": RewardTermCfg(func=mdp.action_rate_l2, weight=-0.1),
        "foot_clearance": RewardTermCfg(
            func=mdp.feet_clearance,
            weight=-2.0,
            params={
                "target_height": 0.1,
                "height_sensor_name": "foot_height_scan",
                "command_name": "twist",
                "command_threshold": 0.05,
                "asset_cfg": SceneEntityCfg("robot", site_names=site_names),
            },
        ),
        "foot_swing_height": RewardTermCfg(
            func=mdp.feet_swing_height,
            weight=-0.25,
            params={
                "sensor_name": "feet_ground_contact",
                "height_sensor_name": "foot_height_scan",
                "target_height": 0.1,
                "command_name": "twist",
                "command_threshold": 0.05,
            },
        ),
        "foot_slip": RewardTermCfg(
            func=mdp.feet_slip,
            weight=-0.1,
            params={
                "sensor_name": "feet_ground_contact",
                "command_name": "twist",
                "command_threshold": 0.05,
                "asset_cfg": SceneEntityCfg("robot", site_names=site_names),
            },
        ),
        "soft_landing": RewardTermCfg(
            func=mdp.soft_landing,
            weight=-1e-5,
            params={
                "sensor_name": "feet_ground_contact",
                "command_name": "twist",
                "command_threshold": 0.05,
            },
        ),
    }


    ##
    # Terminations
    ##

    terminations = {
        "time_out": TerminationTermCfg(func=mdp.time_out, time_out=True),
        # func points at custom_mdp.bad_orientation, which is Exercise 8 (see
        # custom_mdp.py) — the wiring here is already done for you, but the
        # function body raises NotImplementedError until you write it.
        "fell_over": TerminationTermCfg(
            func=custom_mdp.bad_orientation,
            params={"limit_angle": math.radians(70.0)},
        ),
        "illegal_contact": TerminationTermCfg(
            func=mdp.illegal_contact,
            params={"sensor_name": nonfeet_ground_cfg.name},
        ),
    }

    ##
    # Curriculum
    ##

    curriculum: dict[str, CurriculumTermCfg] = {}

    # TODO(Exercise 6 - Curriculum):

    curriculum["command_vel"] = CurriculumTermCfg(
        func=mdp.commands_vel,
        params={
            "command_name": "twist",
            "velocity_stages": [
                {"step": 0, "lin_vel_x": (-1.0, 1.0), "ang_vel_z": (-0.5, 0.5)},
                {"step": 5000 * 24, "lin_vel_x": (-1.5, 2.0), "ang_vel_z": (-0.7, 0.7)},
                {"step": 10000 * 24, "lin_vel_x": (-2.0, 3.0)},
            ],
        },
    )

    ##
    # Assemble base config
    ##

    cfg = ManagerBasedRlEnvCfg(
        scene=scene,
        observations=observations,
        actions=actions,
        commands=commands,
        events=events,
        rewards=rewards,
        terminations=terminations,
        curriculum=curriculum,
        metrics=metrics,
        viewer=ViewerConfig(
            origin_type=ViewerConfig.OriginType.ASSET_BODY,
            entity_name="robot",
            body_name="base_link",
            distance=1.5,
            elevation=-10.0,
            azimuth=90.0,
        ),
        sim=SimulationCfg(
            nconmax=None,
            njmax=300,
            contact_sensor_maxmatch=64,
            mujoco=MujocoCfg(
                timestep=0.005,
                iterations=10,
                ls_iterations=20,
                ccd_iterations=50,
            ),
        ),
        decimation=4,
        episode_length_s=20.0,
    )

    if play:
        cfg.episode_length_s = int(1e9)
        cfg.observations["actor"].enable_corruption = False
        cfg.events.pop("push_robot", None)
        pass

    return cfg
