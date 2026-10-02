"""Unitree Go2 constants. File adapted from G02 unitree_rl_mjlab (https://github.com/unitreerobotics/unitree_rl_mjlab)"""

from pathlib import Path

import mujoco

from mjlab.actuator import BuiltinPositionActuatorCfg
from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
from mjlab.utils.actuator import ElectricActuator, reflected_inertia
from mjlab.utils.spec_config import CollisionCfg

##
# MJCF and assets.
##

_HERE = Path(__file__).parent

# Path to the main MJCF (lives under the xmls subfolder).
GO_2_XML: Path = _HERE / "xmls" / "go2.xml"
assert GO_2_XML.exists()


def get_assets(meshdir: str) -> dict[str, bytes]:
    assets: dict[str, bytes] = {}
    assets_dir = GO_2_XML.parent / "assets"
    
    if assets_dir.exists():
        # Recursively find all files in the assets directory
        for file_path in assets_dir.rglob("*"):
            if file_path.is_file():
                # Get the path relative to the XML folder (e.g., 'assets/mesh.stl')
                rel_path = str(file_path.relative_to(GO_2_XML.parent))
                assets[rel_path] = file_path.read_bytes()
                
    return assets


def get_spec() -> mujoco.MjSpec: # type: ignore
    spec = mujoco.MjSpec.from_file(str(GO_2_XML)) # type: ignore
    spec.assets = get_assets(spec.meshdir)
    return spec




##
# Actuator config.
##

GO2_ACTUATOR_HIP = BuiltinPositionActuatorCfg(
  target_names_expr=(
    ".*hip_.*",
  ),
  stiffness=20.0,
  damping=0.5,
  effort_limit=23.5,
  armature=0.01,
)
GO2_ACTUATOR_THIGH = BuiltinPositionActuatorCfg(
  target_names_expr=(
    ".*thigh_.*",
  ),
  stiffness=20.0,
  damping=0.5,
  effort_limit=23.5,
  armature=0.01,
)
GO2_ACTUATOR_CALF = BuiltinPositionActuatorCfg(
  target_names_expr=(
    ".*calf_.*",
  ),
  stiffness=20.0,
  damping=0.5,
  effort_limit=45,
  armature=0.02,
)

##
# Keyframes.
##

# TODO(Exercise 1 - Init State):

INIT_STATE = EntityCfg.InitialStateCfg(
  pos=(0.0, 0.0, 0.32),
  joint_pos={
    "^F[LR]_thigh_joint$": 0.8,
    "^R[LR]_thigh_joint$": 1.0,
    ".*calf_joint": -1.5,
    ".*R_hip_joint": 0.1,
    ".*L_hip_joint": -0.1,
  },
  joint_vel={".*": 0.0},
)


##
# Collision config.
##

_foot_regex = "^[FR][LR]_foot_collision$"

# This disables all collisions except the feet.
# Furthermore, feet self collisions are disabled.
FEET_ONLY_COLLISION = CollisionCfg(
  geom_names_expr=(_foot_regex,),
  contype=0,
  conaffinity=1,
  condim=3,
  priority=1,
  friction=(0.6,),
  solimp=(0.9, 0.95, 0.023),
)

# This enables all collisions, excluding self collisions.
# Foot collisions are given custom condim, friction and solimp.
FULL_COLLISION = CollisionCfg(
  geom_names_expr=(".*_collision",),
  condim={_foot_regex: 3, ".*_collision": 1},
  priority={_foot_regex: 1},
  friction={_foot_regex: (0.6,)},
  solimp={_foot_regex: (0.9, 0.95, 0.023)},
  contype=1,
  conaffinity=0,
)

##
# Final config.
##

GO2_ARTICULATION = EntityArticulationInfoCfg(
  actuators=(
    GO2_ACTUATOR_HIP,
    GO2_ACTUATOR_THIGH,
    GO2_ACTUATOR_CALF,
  ),
  soft_joint_pos_limit_factor=0.9,
)

GO2_ACTION_SCALE: dict[str, float] = {}
for a in GO2_ARTICULATION.actuators:
  assert isinstance(a, BuiltinPositionActuatorCfg)
  names = a.target_names_expr
  for n in names:
    GO2_ACTION_SCALE[n] = 0.25

def get_go2_robot_cfg() -> EntityCfg:
  """Get a fresh Go2 robot configuration instance.

  Returns a new EntityCfg instance each time to avoid mutation issues when
  the config is shared across multiple places.
  """
  return EntityCfg(
    init_state=INIT_STATE,
    collisions=(FULL_COLLISION,),
    spec_fn=get_spec,
    articulation=GO2_ARTICULATION,
  )

if __name__ == "__main__":
  import mujoco.viewer as viewer

  from mjlab.entity.entity import Entity

  robot = Entity(get_go2_robot_cfg())

  viewer.launch(robot.spec.compile())
