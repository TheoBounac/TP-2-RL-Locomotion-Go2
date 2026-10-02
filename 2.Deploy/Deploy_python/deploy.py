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
from common.command_helper import create_zero_cmd, create_damping_cmd, init_cmd_go
from common.rotation_helper import get_gravity_orientation
from common.remote_controller import RemoteController, KeyMap
from common.dashboard_panels import DashboardMixin
from common.config import Config

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true")
parser.add_argument("--real", action="store_true")
parser.add_argument("--net", type=str, default="lo")
parser.add_argument("--config", type=str, default="go2.yaml")
parser.add_argument("--policy", type=str, default=None)
args = parser.parse_args()

DEBUG = args.debug
REAL = args.real

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
JOINT2MOTOR_IDX = [
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
    def __init__(self,real=False, config=None) -> None:
        self.real = real
        self.config = config
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
        self.remote_command = np.array([0.8, 0.0, 0.0], dtype=np.float32)
        self.counter = 0

        self.ang_vel = np.zeros(3, dtype=np.float32)
        self.quat = np.zeros(4, dtype=np.float32)
        self.gravity = np.zeros(3, dtype=np.float32)
        self.dof_pos = np.zeros(NUM_ACTIONS, dtype=np.float32)
        self.dof_vel = np.zeros(NUM_ACTIONS, dtype=np.float32)

        self.low_cmd = unitree_go_msg_dds__LowCmd_()
        self.low_state = unitree_go_msg_dds__LowState_()

        lowcmd_topic = self.config.lowcmd_topic if self.real and self.config is not None else LOWCMD_TOPIC
        lowstate_topic = self.config.lowstate_topic if self.real and self.config is not None else LOWSTATE_TOPIC

        self.lowcmd_publisher = ChannelPublisher(lowcmd_topic, LowCmdGo)
        self.lowcmd_publisher.Init()

        self.low_state_received = False
        self.lowstate_subscriber = ChannelSubscriber(lowstate_topic, LowStateGo)
        self.lowstate_subscriber.Init(self.LowStateHandler, 10)

        if self.real:
            self.wait_for_low_state()
            init_cmd_go(self.low_cmd, weak_motor=self.config.weak_motor)


    def LowStateHandler(self, msg: LowStateGo):
        self.low_state = msg
        self.low_state_received = True
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
            init_dof_pos[i] = self.low_state.motor_state[JOINT2MOTOR_IDX[i]].q

        for i in range(num_step):
            alpha = i / num_step
            for j in range(12):
                motor_idx = JOINT2MOTOR_IDX[j]
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
                motor_idx = JOINT2MOTOR_IDX[i]
                self.low_cmd.motor_cmd[motor_idx].q = DEFAULT_ANGLES[i]
                self.low_cmd.motor_cmd[motor_idx].dq = 0.0
                self.low_cmd.motor_cmd[motor_idx].kp = 40.0
                self.low_cmd.motor_cmd[motor_idx].kd = 0.6
                self.low_cmd.motor_cmd[motor_idx].tau = 0.0
            self.send_cmd(self.low_cmd)
            time.sleep(CONTROL_DT)

        print("Button [A] received, starting policy control.")
        print("Press [SELECT] button to exit.")
    
    def wait_for_low_state(self):
        print("Waiting for rt/lowstate...")
        while not self.low_state_received:
            time.sleep(CONTROL_DT)
        print("Connected to robot.")

    def init_real_robot(self):
        self.sc = SportClient()
        self.sc.SetTimeout(5.0)
        self.sc.Init()

        self.msc = MotionSwitcherClient()
        self.msc.SetTimeout(5.0)
        self.msc.Init()

        status, result = self.msc.CheckMode()
        if result is None:
            print("MotionSwitcher unavailable, skipping release.")
            return

        while result["name"]:
            self.sc.StandDown()
            time.sleep(3.0)
            self.msc.ReleaseMode()
            time.sleep(1.0)

            status, result = self.msc.CheckMode()
            if result is None:
                print("MotionSwitcher unavailable, skipping release.")
                return

        print("High level mode released.")

    def move_to_ground(self):
        print("Moving to ground.")
        total_time = 1.5
        num_step = int(total_time / CONTROL_DT)
        ground_pos = np.array(
            [-0.35, 1.36, -2.65,
            0.35, 1.36, -2.65,
            -0.5,  1.36, -2.65,
            0.5,  1.36, -2.65],
            dtype=np.float32,
        )

        init_dof_pos = np.zeros(12, dtype=np.float32)
        for i in range(12):
            init_dof_pos[i] = self.low_state.motor_state[JOINT2MOTOR_IDX[i]].q

        for step in range(num_step):
            alpha = step / num_step
            for i in range(12):
                motor_idx = JOINT2MOTOR_IDX[i]
                self.low_cmd.motor_cmd[motor_idx].q = init_dof_pos[i] * (1 - alpha) + ground_pos[i] * alpha
                self.low_cmd.motor_cmd[motor_idx].dq = 0.0
                self.low_cmd.motor_cmd[motor_idx].kp = 40.0
                self.low_cmd.motor_cmd[motor_idx].kd = 0.6
                self.low_cmd.motor_cmd[motor_idx].tau = 0.0
            self.send_cmd(self.low_cmd)
            time.sleep(CONTROL_DT)

        print("Robot is on the ground.")



    def run(self):

        # ============================== PART 1. OBSERVATION ==================================== #
        ################################# USEFUL VARIABLES ########################################
        low_state = self.low_state                                                                #
        ang_vel_scale = 0.25                                                                      #
                                                                                                  #
                                                                                                  #
        gravity_scale = 1                                                                         #
                                                                                                  #
                                                                                                  #
        vx = self.remote_controller.ly                                                            #
        vy = -self.remote_controller.lx                                                           #
        wz = -self.remote_controller.rx                                                           #
        vx_scale = 3.0                                                                            #
        vy_scale = 2.0                                                                            #
        wz_scale = 0.5                                                                            #
                                                                                                  #
                                                                                                  #
        JOINT2MOTOR_IDX = [3, 4, 5,                                                               #
                           0, 1, 2,                                                               #
                           9, 10, 11,                                                             #
                           6, 7, 8]                                                               #
        DEFAULT_ANGLES = np.array([                                                               #
                                    0.1,  0.8, -1.5,                                              #
                                   -0.1,  0.8, -1.5,                                              #
                                    0.1,  1.0, -1.5,                                              #
                                   -0.1,  1.0, -1.5,                                              #
                                  ], dtype=np.float32)                                            #
        pos_scale = 1.0                                                                           #
                                                                                                  #
                                                                                                  #
        vel_scale = 0.05                                                                          #
                                                                                                  #
        ###########################################################################################

        # TODO [1] Read base angular velocity from IMU
        self.ang_vel = None # MUST BE np.array(...)*ang_vel_scale

        # TODO [2] Read quaternion from IMU and Compute gravity orientation from quaternion
        self.gravity = None

        # TODO [3] Read remote_command from remote controller
        if self.use_remote_controller:                                                            
            self.remote_command[0] = None                                              
            self.remote_command[1] = None                                            
            self.remote_command[2] = None

        # TODO [4] Read dof positions and dof velocities, be careful with the order of the joints: dof_pos[i] -> motor_state[JOINT2MOTOR_IDX[i]]
        self.dof_pos = None
        self.dof_vel = None

        # TODO [5] Read last action (Nothing to do here: observation remain wrong until you do the policy inference in part 2)
        self.last_action = self.action
        
        # TODO [6] Fill the obs with the right observations values
        self.obs[:3] = None                                        
        self.obs[3:6] = None
        self.obs[6:9] = None
        self.obs[9:21] = None 
        self.obs[21:33] = None
        self.obs[33:45] = None 

        # This line put it in a tensor format 
        observations = torch.from_numpy(self.obs).unsqueeze(0) 
        # ======================================================================================= #




        # //////////////////// REFERENCE DO NOT MODIFY ///////////////////////////// #
        self.obs_low_state_ref = self.low_state                                      #
        self.obs_remote_ref = {                                                      #
            "ly": getattr(self.remote_controller, "ly", 0.0),                        #
            "lx": getattr(self.remote_controller, "lx", 0.0),                        #
            "rx": getattr(self.remote_controller, "rx", 0.0),                        #
        }                                                                            #
        self.obs_action_ref = self.action.copy() if self.action is not None else None#
        # ////////////////////////////////////////////////////////////////////////// #




        # ================================ PART 2. POLICY =================================== #
        ################################# USEFUL VARIABLES ####################################
        policy = self.policy                                                                  #
        observations = observations                                                           #
                                                                                              #
        DEFAULT_ANGLES = np.array([                                                           #
                                    0.1,  0.8, -1.5,                                          #
                                   -0.1,  0.8, -1.5,                                          #
                                    0.1,  1.0, -1.5,                                          #
                                   -0.1,  1.0, -1.5,                                          #
                                  ], dtype=np.float32)                                        #
                                                                                              #
        action_scale = 0.25                                                                   #
        ####################################################################################### 

        # TODO [7] Inference of the policy with the observation tensor                                                                                                                
        self.action = torch.zeros((NUM_ACTIONS,), dtype=torch.float32)   
        

        # This line just put it in the format expected by the robot (Do not modify)                                          
        self.action = self.action.detach().cpu().numpy().astype(np.float32).squeeze()
        action = self.action   

        # TODO [8] Fill the target position using the policy output (action)                                                                                
        self.target_joint_position = None                
        # =================================================================================== #





        # ================================ PART 3. ACTION ================================= #
        ################################# USEFUL VARIABLES ##################################
        JOINT2MOTOR_IDX = [3, 4, 5,                                                         #
                           0, 1, 2,                                                         #
                           9, 10, 11,                                                       #
                           6, 7, 8]                                                         #
                                                                                            #
        target_joint_position = self.target_joint_position                                  #
                                                                                            #
        KPS = [20.0] * 12                                                                   #
        KDS = [0.5] * 12                                                                    #
        #####################################################################################

        # TODO [9] Fill the PD controller with the target command (target_joint_pos) and match the indexes beetwen PD controller and policy 
        for i in range(12):                                                                 
            motor_idx = 0                                        
            self.low_cmd.motor_cmd[motor_idx].q =  0.0 # float
            self.low_cmd.motor_cmd[motor_idx].dq = 0.0 # float                                 
            self.low_cmd.motor_cmd[motor_idx].kp = 0.0 # float                              
            self.low_cmd.motor_cmd[motor_idx].kd = 0.0 # float                              
            self.low_cmd.motor_cmd[motor_idx].tau = 0.0 # do not modify
        self.send_cmd(self.low_cmd)

        self.counter += 1                                                         
        time.sleep(CONTROL_DT)
        # ================================================================================= #




if __name__ == "__main__":
    if REAL:
        config_path = Path(__file__).resolve().parent / "common" / args.config
        config = Config(config_path)

        ChannelFactoryInitialize(0, args.net)
        controller = Controller(real=True, config=config)
        controller.init_real_robot()
    else:
        ChannelFactoryInitialize(0, "lo")
        controller = Controller()

    controller.zero_torque_state()
    controller.move_to_default_pos()
    controller.default_pos_state()

    try:
        if not DEBUG and not REAL:
            with Live(
                controller.render_dashboard(),
                refresh_per_second=5,
                screen=False,
                transient=False,
            ) as live:
                while True:
                    controller.run()

                    if controller.counter % DISPLAY_EVERY == 0:
                        live.update(controller.render_dashboard())

                    if controller.remote_controller.button[KeyMap.select] == 1:
                        break
        else:
            while True:
                controller.run()

                if controller.remote_controller.button[KeyMap.select] == 1:
                    if REAL:
                        controller.move_to_ground()
                    break

    except KeyboardInterrupt:
        pass

    finally:
        if REAL:
            create_damping_cmd(controller.low_cmd)
            controller.send_cmd(controller.low_cmd)

    print("Exit")