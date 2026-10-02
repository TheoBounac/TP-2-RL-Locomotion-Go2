import mujoco
import numpy as np
import pygame
import sys
import struct
import threading

from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelPublisher

from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import WirelessController_
from unitree_sdk2py.idl.default import unitree_go_msg_dds__SportModeState_
from unitree_sdk2py.idl.default import unitree_go_msg_dds__WirelessController_
from unitree_sdk2py.utils.thread import RecurrentThread

import config
if config.ROBOT == "g1":
    from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
    from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
    from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_ as LowState_default
else:
    from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_
    from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_
    from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowState_ as LowState_default

TOPIC_LOWCMD = "rt/lowcmd"
TOPIC_LOWSTATE = "rt/lowstate"
TOPIC_HIGHSTATE = "rt/sportmodestate"
TOPIC_WIRELESS_CONTROLLER = "rt/wirelesscontroller"

MOTOR_SENSOR_NUM = 3
NUM_MOTOR_IDL_GO = 20
NUM_MOTOR_IDL_HG = 35


class KeyMap:
    R1 = 0
    L1 = 1
    start = 2
    select = 3
    R2 = 4
    L2 = 5
    F1 = 6
    F2 = 7
    A = 8
    B = 9
    X = 10
    Y = 11
    up = 12
    right = 13
    down = 14
    left = 15


class VirtualRemoteState:
    def __init__(self):
        self.lock = threading.Lock()
        self.lx = 0.0
        self.ly = 0.0
        self.rx = 0.0
        self.ry = 0.0
        self.buttons = [0] * 16

    def snapshot(self):
        with self.lock:
            return {
                "lx": float(self.lx),
                "ly": float(self.ly),
                "rx": float(self.rx),
                "ry": float(self.ry),
                "buttons": list(self.buttons),
            }

    def set_axes(self, lx=None, ly=None, rx=None, ry=None):
        with self.lock:
            if lx is not None:
                self.lx = float(lx)
            if ly is not None:
                self.ly = float(ly)
            if rx is not None:
                self.rx = float(rx)
            if ry is not None:
                self.ry = float(ry)

    def set_button(self, idx, value):
        with self.lock:
            self.buttons[idx] = 1 if value else 0

    def clear_stick(self):
        with self.lock:
            self.lx = 0.0
            self.ly = 0.0

    def clear_rotation(self):
        with self.lock:
            self.rx = 0.0
            self.ry = 0.0


class VirtualRemoteUI:
    def __init__(self, remote_state, width=430, height=250, deadzone=0.05):
        self.remote_state = remote_state
        self.width = width
        self.height = height
        self.deadzone = deadzone

        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.running = False

        self.stick_center = np.array([330.0, 145.0], dtype=np.float32)
        self.stick_radius = 65.0
        self.stick_knob = self.stick_center.copy()
        self.dragging_stick = False

        self.button_rects = {
            "A": pygame.Rect(35, 75, 50, 50),
            "E": pygame.Rect(105, 75, 50, 50),
            "SELECT": pygame.Rect(35, 160, 65, 30),
            "START": pygame.Rect(105, 160, 65, 30),
        }

        self.mouse_pressed_button = None

    def start(self):
        pygame.init()
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Unitree Virtual Remote")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 17)
        self.small_font = pygame.font.SysFont("Arial", 13)
        self.running = True

    def stop(self):
        self.running = False
        try:
            if pygame.get_init():
                pygame.display.quit()
                pygame.quit()
        except Exception:
            pass

    def _clamp_stick(self, pos):
        delta = np.array(pos, dtype=np.float32) - self.stick_center
        norm = np.linalg.norm(delta)

        if norm > self.stick_radius and norm > 1e-6:
            delta = delta / norm * self.stick_radius

        self.stick_knob = self.stick_center + delta

        lx = float(delta[0] / self.stick_radius)
        ly = float(-delta[1] / self.stick_radius)

        if abs(lx) < self.deadzone:
            lx = 0.0
        if abs(ly) < self.deadzone:
            ly = 0.0

        self.remote_state.set_axes(lx=lx, ly=ly)

    def _reset_stick(self):
        self.dragging_stick = False
        self.stick_knob = self.stick_center.copy()
        self.remote_state.clear_stick()

    def _find_clicked_button(self, pos):
        for name, rect in self.button_rects.items():
            if rect.collidepoint(pos):
                return name
        return None

    def _apply_keyboard_down(self, key):
        if key == pygame.K_a:
            self.remote_state.set_button(KeyMap.A, 1)
            self.remote_state.set_axes(rx=-1.0)
        elif key == pygame.K_e:
            self.remote_state.set_button(KeyMap.B, 1)
            self.remote_state.set_axes(rx=1.0)
        elif key == pygame.K_s:
            self.remote_state.set_button(KeyMap.select, 1)
        elif key == pygame.K_d:
            self.remote_state.set_button(KeyMap.start, 1)

    def _apply_keyboard_up(self, key):
        if key == pygame.K_a:
            self.remote_state.set_button(KeyMap.A, 0)
            snap = self.remote_state.snapshot()
            if snap["rx"] < 0:
                self.remote_state.set_axes(rx=0.0)

        elif key == pygame.K_e:
            self.remote_state.set_button(KeyMap.B, 0)
            snap = self.remote_state.snapshot()
            if snap["rx"] > 0:
                self.remote_state.set_axes(rx=0.0)

        elif key == pygame.K_s:
            self.remote_state.set_button(KeyMap.select, 0)

        elif key == pygame.K_d:
            self.remote_state.set_button(KeyMap.start, 0)

    def _apply_mouse_button_state(self, name, pressed):
        if name == "A":
            self.remote_state.set_button(KeyMap.A, pressed)

            if pressed:
                self.remote_state.set_axes(rx=-1.0)
            else:
                snap = self.remote_state.snapshot()
                if snap["rx"] < 0:
                    self.remote_state.set_axes(rx=0.0)

        elif name == "E":
            self.remote_state.set_button(KeyMap.B, pressed)

            if pressed:
                self.remote_state.set_axes(rx=1.0)
            else:
                snap = self.remote_state.snapshot()
                if snap["rx"] > 0:
                    self.remote_state.set_axes(rx=0.0)

        elif name == "SELECT":
            self.remote_state.set_button(KeyMap.select, pressed)

        elif name == "START":
            self.remote_state.set_button(KeyMap.start, pressed)

    def pump_once(self):
        if not self.running:
            return False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break

            if event.type == pygame.KEYDOWN:
                self._apply_keyboard_down(event.key)

            if event.type == pygame.KEYUP:
                self._apply_keyboard_up(event.key)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = self._find_clicked_button(event.pos)

                if clicked is not None:
                    self.mouse_pressed_button = clicked
                    self._apply_mouse_button_state(clicked, True)
                else:
                    mouse = np.array(event.pos, dtype=np.float32)
                    if np.linalg.norm(mouse - self.stick_center) <= self.stick_radius + 15:
                        self.dragging_stick = True
                        self._clamp_stick(event.pos)

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.mouse_pressed_button is not None:
                    self._apply_mouse_button_state(self.mouse_pressed_button, False)
                    self.mouse_pressed_button = None

                if self.dragging_stick:
                    self._reset_stick()

            if event.type == pygame.MOUSEMOTION and self.dragging_stick:
                self._clamp_stick(event.pos)

        self.draw()
        return self.running

    def draw(self):
        snap = self.remote_state.snapshot()

        self.screen.fill((24, 26, 30))

        title = self.font.render("Virtual Unitree Remote", True, (245, 245, 245))
        title_rect = title.get_rect(center=(self.width // 2, 22))
        self.screen.blit(title, title_rect)

        pygame.draw.circle(
            self.screen,
            (72, 76, 84),
            self.stick_center.astype(int),
            int(self.stick_radius),
            3,
        )

        pygame.draw.circle(
            self.screen,
            (50, 54, 62),
            self.stick_center.astype(int),
            int(self.stick_radius - 8),
        )

        pygame.draw.line(
            self.screen,
            (96, 100, 110),
            (int(self.stick_center[0] - self.stick_radius), int(self.stick_center[1])),
            (int(self.stick_center[0] + self.stick_radius), int(self.stick_center[1])),
            1,
        )

        pygame.draw.line(
            self.screen,
            (96, 100, 110),
            (int(self.stick_center[0]), int(self.stick_center[1] - self.stick_radius)),
            (int(self.stick_center[0]), int(self.stick_center[1] + self.stick_radius)),
            1,
        )

        pygame.draw.circle(
            self.screen,
            (155, 165, 185),
            self.stick_knob.astype(int),
            15,
        )

        button_colors = {
            "A": (200, 90, 90),
            "E": (90, 150, 220),
            "SELECT": (130, 100, 210),
            "START": (90, 175, 120),
        }

        active_map = {
            "A": snap["buttons"][KeyMap.A],
            "E": snap["rx"] > 0.5,
            "SELECT": snap["buttons"][KeyMap.select],
            "START": snap["buttons"][KeyMap.start],
        }

        for name, rect in self.button_rects.items():
            color = button_colors[name] if active_map[name] else (82, 86, 94)

            pygame.draw.rect(self.screen, color, rect, border_radius=7)
            pygame.draw.rect(self.screen, (210, 210, 210), rect, width=1, border_radius=7)

            label = self.font.render(name, True, (255, 255, 255))
            label_rect = label.get_rect(center=rect.center)
            self.screen.blit(label, label_rect)

        wz_label = self.small_font.render("Rotation Wz", True, (220, 220, 220))
        wz_rect = wz_label.get_rect(
            center=((self.button_rects["A"].centerx + self.button_rects["E"].centerx) // 2, 140)
        )
        self.screen.blit(wz_label, wz_rect)

        pygame.display.flip()
        self.clock.tick(60)


class UnitreeSdk2Bridge:

    def __init__(self, mj_model, mj_data):
        self.mj_model = mj_model
        self.mj_data = mj_data

        self.num_motor = self.mj_model.nu
        self.dim_motor_sensor = MOTOR_SENSOR_NUM * self.num_motor
        self.have_imu = False
        self.have_frame_sensor = False
        self.dt = self.mj_model.opt.timestep
        self.idl_type = (self.num_motor > NUM_MOTOR_IDL_GO)

        self.joystick = None
        self.virtual_remote_state = None

        for i in range(self.dim_motor_sensor, self.mj_model.nsensor):
            name = mujoco.mj_id2name(
                self.mj_model, mujoco._enums.mjtObj.mjOBJ_SENSOR, i
            )
            if name == "imu_quat":
                self.have_imu_ = True
            if name == "frame_pos":
                self.have_frame_sensor_ = True

        self.low_state = LowState_default()
        self.low_state_puber = ChannelPublisher(TOPIC_LOWSTATE, LowState_)
        self.low_state_puber.Init()
        self.lowStateThread = RecurrentThread(
            interval=self.dt, target=self.PublishLowState, name="sim_lowstate"
        )
        self.lowStateThread.Start()

        self.high_state = unitree_go_msg_dds__SportModeState_()
        self.high_state_puber = ChannelPublisher(TOPIC_HIGHSTATE, SportModeState_)
        self.high_state_puber.Init()
        self.HighStateThread = RecurrentThread(
            interval=self.dt, target=self.PublishHighState, name="sim_highstate"
        )
        self.HighStateThread.Start()

        self.wireless_controller = unitree_go_msg_dds__WirelessController_()
        self.wireless_controller_puber = ChannelPublisher(
            TOPIC_WIRELESS_CONTROLLER, WirelessController_
        )
        self.wireless_controller_puber.Init()
        self.WirelessControllerThread = RecurrentThread(
            interval=0.01,
            target=self.PublishWirelessController,
            name="sim_wireless_controller",
        )
        self.WirelessControllerThread.Start()

        self.low_cmd_suber = ChannelSubscriber(TOPIC_LOWCMD, LowCmd_)
        self.low_cmd_suber.Init(self.LowCmdHandler, 10)

        self.key_map = {
            "R1": 0,
            "L1": 1,
            "start": 2,
            "select": 3,
            "R2": 4,
            "L2": 5,
            "F1": 6,
            "F2": 7,
            "A": 8,
            "B": 9,
            "X": 10,
            "Y": 11,
            "up": 12,
            "right": 13,
            "down": 14,
            "left": 15,
        }

    def SetupVirtualRemote(self):
        self.virtual_remote_state = VirtualRemoteState()

    def GetVirtualRemoteState(self):
        return self.virtual_remote_state

    def _build_remote_from_virtual(self):
        if self.virtual_remote_state is None:
            return None

        snap = self.virtual_remote_state.snapshot()
        buttons = snap["buttons"]

        keys = 0
        for i in range(16):
            keys |= (int(buttons[i]) & 1) << i

        packed_keys = struct.pack("H", keys)
        packed_lx = struct.pack("f", snap["lx"])
        packed_rx = struct.pack("f", snap["rx"])
        packed_ry = struct.pack("f", snap["ry"])
        packed_ly = struct.pack("f", snap["ly"])

        return {
            "keys": keys,
            "buttons": buttons,
            "lx": snap["lx"],
            "ly": snap["ly"],
            "rx": snap["rx"],
            "ry": snap["ry"],
            "packed_keys_low": packed_keys[0],
            "packed_keys_high": packed_keys[1],
            "packed_lx": packed_lx,
            "packed_rx": packed_rx,
            "packed_ry": packed_ry,
            "packed_ly": packed_ly,
        }

    def LowCmdHandler(self, msg: LowCmd_):
        if self.mj_data is not None:
            for i in range(self.num_motor):
                self.mj_data.ctrl[i] = (
                    msg.motor_cmd[i].tau
                    + msg.motor_cmd[i].kp * (msg.motor_cmd[i].q - self.mj_data.sensordata[i])
                    + msg.motor_cmd[i].kd * (msg.motor_cmd[i].dq - self.mj_data.sensordata[i + self.num_motor])
                )

    def PublishLowState(self):
        if self.mj_data is not None:
            for i in range(self.num_motor):
                self.low_state.motor_state[i].q = self.mj_data.sensordata[i]
                self.low_state.motor_state[i].dq = self.mj_data.sensordata[i + self.num_motor]
                self.low_state.motor_state[i].tau_est = self.mj_data.sensordata[i + 2 * self.num_motor]

            if self.have_frame_sensor_:
                self.low_state.imu_state.quaternion[0] = self.mj_data.sensordata[self.dim_motor_sensor + 0]
                self.low_state.imu_state.quaternion[1] = self.mj_data.sensordata[self.dim_motor_sensor + 1]
                self.low_state.imu_state.quaternion[2] = self.mj_data.sensordata[self.dim_motor_sensor + 2]
                self.low_state.imu_state.quaternion[3] = self.mj_data.sensordata[self.dim_motor_sensor + 3]

                self.low_state.imu_state.gyroscope[0] = self.mj_data.sensordata[self.dim_motor_sensor + 4]
                self.low_state.imu_state.gyroscope[1] = self.mj_data.sensordata[self.dim_motor_sensor + 5] if False else self.mj_data.sensordata[self.dim_motor_sensor + 5]
                self.low_state.imu_state.gyroscope[2] = self.mj_data.sensordata[self.dim_motor_sensor + 6]

                self.low_state.imu_state.accelerometer[0] = self.mj_data.sensordata[self.dim_motor_sensor + 7]
                self.low_state.imu_state.accelerometer[1] = self.mj_data.sensordata[self.dim_motor_sensor + 8]
                self.low_state.imu_state.accelerometer[2] = self.mj_data.sensordata[self.dim_motor_sensor + 9]

            virtual = self._build_remote_from_virtual()
            if virtual is not None:
                self.low_state.wireless_remote[0] = 0
                self.low_state.wireless_remote[1] = 0
                self.low_state.wireless_remote[2] = virtual["packed_keys_low"]
                self.low_state.wireless_remote[3] = virtual["packed_keys_high"]
                self.low_state.wireless_remote[4:8] = virtual["packed_lx"]
                self.low_state.wireless_remote[8:12] = virtual["packed_rx"]
                self.low_state.wireless_remote[12:16] = virtual["packed_ry"]
                self.low_state.wireless_remote[16:20] = b"\x00\x00\x00\x00"
                self.low_state.wireless_remote[20:24] = virtual["packed_ly"]

            self.low_state_puber.Write(self.low_state)

    def PublishHighState(self):
        if self.mj_data is not None:
            self.high_state.position[0] = self.mj_data.sensordata[self.dim_motor_sensor + 10]
            self.high_state.position[1] = self.mj_data.sensordata[self.dim_motor_sensor + 11]
            self.high_state.position[2] = self.mj_data.sensordata[self.dim_motor_sensor + 12]

            self.high_state.velocity[0] = self.mj_data.sensordata[self.dim_motor_sensor + 13]
            self.high_state.velocity[1] = self.mj_data.sensordata[self.dim_motor_sensor + 14]
            self.high_state.velocity[2] = self.mj_data.sensordata[self.dim_motor_sensor + 15]

        self.high_state_puber.Write(self.high_state)

    def PublishWirelessController(self):
        virtual = self._build_remote_from_virtual()
        if virtual is not None:
            self.wireless_controller.keys = virtual["keys"]
            self.wireless_controller.lx = virtual["lx"]
            self.wireless_controller.ly = virtual["ly"]
            self.wireless_controller.rx = virtual["rx"]
            self.wireless_controller.ry = virtual["ry"]
            self.wireless_controller_puber.Write(self.wireless_controller)

    def SetupJoystick(self, device_id=0, js_type="xbox"):
        pygame.init()
        pygame.joystick.init()
        joystick_count = pygame.joystick.get_count()
        if joystick_count > 0:
            self.joystick = pygame.joystick.Joystick(device_id)
            self.joystick.init()
        else:
            print("No gamepad detected.")
            sys.exit()

        if js_type == "xbox":
            self.axis_id = {
                "LX": 0,
                "LY": 1,
                "RX": 2,
                "RY": 3,
                "LT": 3,
                "RT": 3,
                "DX": 3,
                "DY": 3,
            }

            self.button_id = {
                "X": 2,
                "Y": 3,
                "B": 1,
                "A": 0,
                "LB": 4,
                "RB": 5,
                "SELECT": 8,
                "START": 9,
            }

        elif js_type == "switch":
            self.axis_id = {
                "LX": 0,
                "LY": 1,
                "RX": 2,
                "RY": 3,
                "LT": 5,
                "RT": 4,
                "DX": 6,
                "DY": 7,
            }

            self.button_id = {
                "X": 3,
                "Y": 4,
                "B": 1,
                "A": 0,
                "LB": 6,
                "RB": 7,
                "SELECT": 10,
                "START": 11,
            }
        else:
            print("Unsupported gamepad. ")

    def PrintSceneInformation(self):
        print(" ")

        print("<<------------- Link ------------->> ")
        for i in range(self.mj_model.nbody):
            name = mujoco.mj_id2name(self.mj_model, mujoco._enums.mjtObj.mjOBJ_BODY, i)
            if name:
                print("link_index:", i, ", name:", name)
        print(" ")

        print("<<------------- Joint ------------->> ")
        for i in range(self.mj_model.njnt):
            name = mujoco.mj_id2name(self.mj_model, mujoco._enums.mjtObj.mjOBJ_JOINT, i)
            if name:
                print("joint_index:", i, ", name:", name)
        print(" ")

        print("<<------------- Actuator ------------->>")
        for i in range(self.mj_model.nu):
            name = mujoco.mj_id2name(
                self.mj_model, mujoco._enums.mjtObj.mjOBJ_ACTUATOR, i
            )
            if name:
                print("actuator_index:", i, ", name:", name)
        print(" ")

        print("<<------------- Sensor ------------->>")
        index = 0
        for i in range(self.mj_model.nsensor):
            name = mujoco.mj_id2name(
                self.mj_model, mujoco._enums.mjtObj.mjOBJ_SENSOR, i
            )
            if name:
                print(
                    "sensor_index:",
                    index,
                    ", name:",
                    name,
                    ", dim:",
                    self.mj_model.sensor_dim[i],
                )
            index = index + self.mj_model.sensor_dim[i]
        print(" ")


class ElasticBand:
    def __init__(self):
        self.stiffness = 200
        self.damping = 100
        self.point = np.array([0, 0, 3])
        self.length = 0
        self.enable = True

    def Advance(self, x, dx):
        delta_x = self.point - x
        distance = np.linalg.norm(delta_x)
        direction = delta_x / max(distance, 1e-6)
        v = np.dot(dx, direction)
        f = (self.stiffness * (distance - self.length) - self.damping * v) * direction
        return f

    def MujuocoKeyCallback(self, key):
        glfw = mujoco.glfw.glfw
        if key == glfw.KEY_7:
            self.length -= 0.1
        if key == glfw.KEY_8:
            self.length += 0.1
        if key == glfw.KEY_9:
            self.enable = not self.enable
