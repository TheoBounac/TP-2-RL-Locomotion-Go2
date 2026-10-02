from pathlib import Path
LEGGED_GYM_ROOT_DIR = Path(__file__).resolve().parents[1]

import time
import numpy as np
import torch

from rich.live import Live

from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_, unitree_go_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_ as LowCmdGo
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_ as LowStateGo
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient
from unitree_sdk2py.go2.sport.sport_client import SportClient
from unitree_sdk2py.go2.robot_state.robot_state_client import RobotStateClient
from common.command_helper import create_zero_cmd, create_damping_cmd
from common.rotation_helper import get_gravity_orientation
from common.remote_controller import RemoteController, KeyMap
from common.dashboard_panels import DashboardMixin

POLICY_PATH = LEGGED_GYM_ROOT_DIR / "Deploy_python/policy/trained.pt"
NUM_ACTIONS = 12
NUM_OBS = 45
CONTROL_DT = 0.02
DISPLAY_EVERY = 5
ACTION_SCALE = 0.25
OBS_SCALES_ANG_VEL = 0.25
OBS_SCALES_DOF_POS = 1.0
OBS_SCALES_DOF_VEL = 0.05
CMD_SCALE = [3.0, 2.0, 0.5]
KPS = [20.0] * 12
KDS = [0.5] * 12
DEFAULT_ANGLES = np.array(
    [
        0.1,  0.8, -1.5,
       -0.1,  0.8, -1.5,
        0.1,  1.0, -1.5,
       -0.1,  1.0, -1.5,
    ],
    dtype=np.float32,
)
LEG_JOINT2MOTOR_IDX = [
    3, 4, 5,
    0, 1, 2,
    9, 10, 11,
    6, 7, 8,
]
LOWCMD_TOPIC = "rt/lowcmd"
LOWSTATE_TOPIC = "rt/lowstate"
LEG_CONFIG = [
    ("FL", 0),
    ("FR", 3),
    ("RL", 6),
    ("RR", 9),
]

class ObsNormalizer(torch.nn.Module):
    def __init__(self, num_obs: int, eps: float = 1e-8) -> None:
        super().__init__()
        self.eps = eps
        self.register_buffer("_mean", torch.zeros(1, num_obs))
        self.register_buffer("_var", torch.ones(1, num_obs))
        self.register_buffer("_std", torch.ones(1, num_obs))
        self.register_buffer("count", torch.tensor(0.0))

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return (obs - self._mean) / (self._std + self.eps)


class Distribution(torch.nn.Module):
    def __init__(self, num_actions: int) -> None:
        super().__init__()
        self.std_param = torch.nn.Parameter(torch.zeros(num_actions))


class ActorNet(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.obs_normalizer = ObsNormalizer(NUM_OBS)
        self.distribution = Distribution(NUM_ACTIONS)
        self.mlp = torch.nn.Sequential(
            torch.nn.Linear(NUM_OBS, 512),
            torch.nn.ELU(),
            torch.nn.Linear(512, 256),
            torch.nn.ELU(),
            torch.nn.Linear(256, 128),
            torch.nn.ELU(),
            torch.nn.Linear(128, NUM_ACTIONS),
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.mlp(self.obs_normalizer(obs))


class ActorMLP(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = ActorNet()

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.net(obs)


def load_trained_policy(path: Path) -> ActorMLP:
    checkpoint = torch.load(path, map_location="cpu")

    policy = ActorMLP()
    actor_state_dict = checkpoint["actor_state_dict"]

    if not any(key.startswith("net.") for key in actor_state_dict):
        actor_state_dict = {f"net.{key}": value for key, value in actor_state_dict.items()}

    policy.load_state_dict(actor_state_dict)
    policy.eval()
    return policy

class Controller(DashboardMixin):
    def __init__(self) -> None:
        self.remote_controller = RemoteController()
        self.use_remote_controller = True
        self.policy = load_trained_policy(POLICY_PATH)

        self.num_actions = NUM_ACTIONS
        self.num_obs = NUM_OBS
        self.control_dt = CONTROL_DT

        self.qj = np.zeros(NUM_ACTIONS, dtype=np.float32)
        self.dqj = np.zeros(NUM_ACTIONS, dtype=np.float32)
        self.action = np.zeros(NUM_ACTIONS, dtype=np.float32)
        self.target_dof_pos = DEFAULT_ANGLES.copy()
        self.obs = np.zeros(NUM_OBS, dtype=np.float32)
        self.cmd = np.array([0.8, 0.0, 0.0], dtype=np.float32)
        self.counter = 0

        self.ang_vel = np.zeros(3, dtype=np.float32)
        self.quat = np.zeros(4, dtype=np.float32)
        self.gravity_orientation = np.zeros(3, dtype=np.float32)
        self.qj_obs = np.zeros(NUM_ACTIONS, dtype=np.float32)
        self.dqj_obs = np.zeros(NUM_ACTIONS, dtype=np.float32)

        self.low_cmd = unitree_go_msg_dds__LowCmd_()
        self.low_state = unitree_go_msg_dds__LowState_()

        self.lowcmd_publisher = ChannelPublisher(LOWCMD_TOPIC, LowCmdGo)
        self.lowcmd_publisher.Init()

        self.lowstate_subscriber = ChannelSubscriber(LOWSTATE_TOPIC, LowStateGo)
        self.lowstate_subscriber.Init(self.LowStateHandler, 10)

    def LowStateHandler(self, msg: LowStateGo):
        self.low_state = msg
        self.remote_controller.set(self.low_state.wireless_remote)

    def send_cmd(self, cmd: LowCmdGo):
        cmd.crc = CRC().Crc(cmd)
        self.lowcmd_publisher.Write(cmd)

    def zero_torque_state(self):
        print("Waiting for the [START] signal.")
        while self.remote_controller.button[KeyMap.start] != 1:
            create_zero_cmd(self.low_cmd)
            self.send_cmd(self.low_cmd)
            time.sleep(CONTROL_DT)

    def move_to_default_pos(self):
        print("Moving to default pos.")
        total_time = 2.0
        num_step = int(total_time / CONTROL_DT)

        init_dof_pos = np.zeros(12, dtype=np.float32)
        for i in range(12):
            init_dof_pos[i] = self.low_state.motor_state[LEG_JOINT2MOTOR_IDX[i]].q

        for i in range(num_step):
            alpha = i / num_step
            for j in range(12):
                motor_idx = LEG_JOINT2MOTOR_IDX[j]
                target_pos = DEFAULT_ANGLES[j]
                self.low_cmd.motor_cmd[motor_idx].q = init_dof_pos[j] * (1 - alpha) + target_pos * alpha
                self.low_cmd.motor_cmd[motor_idx].dq = 0.0
                self.low_cmd.motor_cmd[motor_idx].kp = 40.0
                self.low_cmd.motor_cmd[motor_idx].kd = 0.6
                self.low_cmd.motor_cmd[motor_idx].tau = 0.0
            self.send_cmd(self.low_cmd)
            time.sleep(CONTROL_DT)

    def default_pos_state(self):
        print("Enter default pos state.")
        print("Waiting for the Button [A] signal.")
        while self.remote_controller.button[KeyMap.A] != 1:
            for i in range(12):
                motor_idx = LEG_JOINT2MOTOR_IDX[i]
                self.low_cmd.motor_cmd[motor_idx].q = DEFAULT_ANGLES[i]
                self.low_cmd.motor_cmd[motor_idx].dq = 0.0
                self.low_cmd.motor_cmd[motor_idx].kp = 40.0
                self.low_cmd.motor_cmd[motor_idx].kd = 0.6
                self.low_cmd.motor_cmd[motor_idx].tau = 0.0
            self.send_cmd(self.low_cmd)
            time.sleep(CONTROL_DT)

        print("Button [A] received, starting policy control.")
        print("Press [SELECT] button to exit.")

    def run(self):
        self.counter += 1


        # ================================== OBSERVATION ======================================== #
        ################################# USEFUL VARIABLES ########################################
        LEG_JOINT2MOTOR_IDX = [3, 4, 5,                                                           #
                               0, 1, 2,                                                           #
                               9, 10, 11,                                                         #
                               6, 7, 8]                                                           #
                                                                                                  #
        DEFAULT_ANGLES = np.array([                                                               #
                                    0.1,  0.8, -1.5,                                              #
                                   -0.1,  0.8, -1.5,                                              #
                                    0.1,  1.0, -1.5,                                              #
                                   -0.1,  1.0, -1.5,                                              #
                                  ], dtype=np.float32)                                            #
                                                                                                  #
        OBS_SCALES_ANG_VEL = 0.25                                                                 #
        CMD_SCALE = [3.0, 2.0, 0.5]                                                               #
        OBS_SCALES_DOF_POS = 1.0                                                                  #
        OBS_SCALES_DOF_VEL = 0.05                                                                 #
        ###########################################################################################
        self.ang_vel = np.array(self.low_state.imu_state.gyroscope, dtype=np.float32)             #
                                                                                                  #
        self.quat = np.array(self.low_state.imu_state.quaternion, dtype=np.float32)               #
        self.gravity_orientation = np.array(get_gravity_orientation(self.quat), dtype=np.float32) #
                                                                                                  #
        if self.use_remote_controller:                                                            #
            self.cmd[0] = self.remote_controller.ly                                               #
            self.cmd[1] = -self.remote_controller.lx                                              #
            self.cmd[2] = -self.remote_controller.rx                                              #
                                                                                                  #
        for i in range(12):                                                                       #
            self.qj[i] = self.low_state.motor_state[LEG_JOINT2MOTOR_IDX[i]].q                     #
            self.dqj[i] = self.low_state.motor_state[LEG_JOINT2MOTOR_IDX[i]].dq                   #
                                                                                                  #
        self.qj_obs = self.qj.copy() - DEFAULT_ANGLES                                             #
        self.dqj_obs = self.dqj.copy()                                                            #
                                                                                                  #
        self.obs[:3] = self.ang_vel * OBS_SCALES_ANG_VEL                                          #
        self.obs[3:6] = self.gravity_orientation                                                  #
        self.obs[6:9] = self.cmd * CMD_SCALE                                                      #
        self.obs[9:21] = self.qj_obs * OBS_SCALES_DOF_POS                                         #
        self.obs[21:33] = self.dqj_obs * OBS_SCALES_DOF_VEL                                       #
        self.obs[33:45] = self.action                                                             #
        # ======================================================================================= #
        # ==================== REFERENCE DO NOT MODIFY ============================= #
        self.obs_low_state_ref = self.low_state                                      #
        self.obs_remote_ref = {                                                      #
            "ly": getattr(self.remote_controller, "ly", 0.0),                        #
            "lx": getattr(self.remote_controller, "lx", 0.0),                        #
            "rx": getattr(self.remote_controller, "rx", 0.0),                        #
        }                                                                            #
        self.obs_action_ref = self.action.copy() if self.action is not None else None#
        # ========================================================================== #


        # ==================================== POLICY ======================================= #
        ################################# USEFUL VARIABLES ####################################
        DEFAULT_ANGLES = np.array([                                                           #
                                    0.1,  0.8, -1.5,                                          #
                                   -0.1,  0.8, -1.5,                                          #
                                    0.1,  1.0, -1.5,                                          #
                                   -0.1,  1.0, -1.5,                                          #
                                  ], dtype=np.float32)                                        #
                                                                                              #
        ACTION_SCALE = 0.25                                                                   #
        #######################################################################################
        obs_tensor = torch.from_numpy(self.obs).unsqueeze(0)                                  #
        with torch.no_grad():                                                                 #
            results = self.policy(obs_tensor)                                                 #
        self.action = results.detach().cpu().numpy().astype(np.float32).squeeze()             #
                                                                                              #
        self.target_dof_pos = DEFAULT_ANGLES + self.action * ACTION_SCALE                     #
        # =================================================================================== #


        # ==================================== ACTION ===================================== #
        ################################# USEFUL VARIABLES ##################################
        LEG_JOINT2MOTOR_IDX = [3, 4, 5,                                                     #
                               0, 1, 2,                                                     #
                               9, 10, 11,                                                   #
                               6, 7, 8]                                                     #
                                                                                            #
        KPS = [20.0] * 12                                                                   #
        KDS = [0.5] * 12                                                                    #
        CONTROL_DT = 0.02                                                                   #
        #####################################################################################
        for i in range(12):                                                                 #
            motor_idx = LEG_JOINT2MOTOR_IDX[i]                                              #
            self.low_cmd.motor_cmd[motor_idx].q = float(self.target_dof_pos[i])             #
            self.low_cmd.motor_cmd[motor_idx].dq = 0.0                                      #
            self.low_cmd.motor_cmd[motor_idx].kp = KPS[i]                                   #
            self.low_cmd.motor_cmd[motor_idx].kd = KDS[i]                                   #
            self.low_cmd.motor_cmd[motor_idx].tau = 0.0                                     #
                                                                                            #
        self.send_cmd(self.low_cmd)                                                         #
        time.sleep(CONTROL_DT)                                                              #
        # ================================================================================= #


if __name__ == "__main__":
    ChannelFactoryInitialize(0, "lo")
    controller = Controller()

    controller.zero_torque_state()
    controller.move_to_default_pos()
    controller.default_pos_state()

    with Live(
        controller.render_dashboard(),
        refresh_per_second=5,
        screen=False,
        transient=False,
    ) as live:
        while True:
            try:
                controller.run()

                if controller.counter % DISPLAY_EVERY == 0:
                    live.update(controller.render_dashboard())

                if controller.remote_controller.button[KeyMap.select] == 1:
                    break

            except KeyboardInterrupt:
                break

    create_damping_cmd(controller.low_cmd)
    controller.send_cmd(controller.low_cmd)
    print("Exit")
