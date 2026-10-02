import math
import numpy as np

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress_bar import ProgressBar
from rich.console import Group
from common.rotation_helper import get_gravity_orientation



class DashboardMixin:


    def _is_invalid(self, value):
        if value is None:
            return True
        try:
            arr = np.asarray(value, dtype=np.float32)
            return not np.all(np.isfinite(arr))
        except Exception:
            return True

    def _safe_array(self, value, size, dtype=np.float32):
        if value is None:
            return np.zeros(size, dtype=dtype)

        try:
            arr = np.asarray(value, dtype=dtype).reshape(-1)
        except Exception:
            return np.zeros(size, dtype=dtype)

        if arr.size == 0:
            return np.zeros(size, dtype=dtype)

        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

        if arr.size == size:
            return arr

        out = np.zeros(size, dtype=dtype)
        n = min(size, arr.size)
        out[:n] = arr[:n]
        return out

    def _safe_scalar(self, value, default=0.0):
        if value is None:
            return float(default)
        try:
            value = float(value)
            if not math.isfinite(value):
                return float(default)
            return value
        except Exception:
            return float(default)

    def _fmt_vec(self, vec, precision=3, size=None):
        if size is not None:
            vec = self._safe_array(vec, size)
        elif vec is None:
            vec = np.zeros(3, dtype=np.float32)
        else:
            vec = np.asarray(vec, dtype=np.float32).reshape(-1)
            vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)

        return "[" + ", ".join(f"{float(v): .{precision}f}" for v in vec) + "]"

    def _fmt_raw_value(self, value, precision=3):
        if value is None:
            return "None"

        try:
            if isinstance(value, np.ndarray):
                arr = value.reshape(-1)
                result = "[" + ", ".join(
                    "nan" if not math.isfinite(float(v)) else f"{float(v): .{precision}f}"
                    for v in arr
                ) + "]"
                return self._normalize_display_text(result)

            if isinstance(value, (list, tuple)):
                parts = []
                for v in value:
                    try:
                        fv = float(v)
                        parts.append("nan" if not math.isfinite(fv) else f"{fv: .{precision}f}")
                    except Exception:
                        parts.append(repr(v))
                result = "[" + ", ".join(parts) + "]"
                return self._normalize_display_text(result)

            fv = float(value)
            result = "nan" if not math.isfinite(fv) else f"{fv: .{precision}f}"
            return self._normalize_display_text(result)

        except Exception:
            return self._normalize_display_text(repr(value))

    def _normalize_display_text(self, value):
        if value is None:
            return "None"

        text = str(value)
        if text.strip() == "":
            return "None"

        return text

    def _fmt_obs_display(self, raw_obs_slice, precision=3):
        if raw_obs_slice is None:
            return "None"

        try:
            arr = np.asarray(raw_obs_slice, dtype=np.float32).reshape(-1)

            if arr.size == 0:
                return "None"

            if np.allclose(arr, 0.0):
                return "None"

            if np.all(np.isfinite(arr)):
                return "[" + ", ".join(f"{float(v): .{precision}f}" for v in arr) + "]"

            return self._fmt_raw_value(raw_obs_slice, precision=precision)

        except Exception:
            return self._fmt_raw_value(raw_obs_slice, precision=precision)

    def _signed_bar(self, value: float, limit: float = 1.0, width: int = 24):
        value = self._safe_scalar(value, 0.0)
        clipped = max(-limit, min(limit, value))
        completed = clipped + limit
        return ProgressBar(total=2 * limit, completed=completed, width=width)

    def _vector_bars_table(self, title: str, labels, values, limits, bar_width=24):
        values = self._safe_array(values, len(labels))

        if isinstance(limits, (int, float)):
            limits = [float(limits)] * len(labels)

        table = Table.grid(padding=(0, 1), expand=False)
        table.add_column(style="bold cyan", width=10)
        table.add_column(width=bar_width + 2)
        table.add_column(justify="right", width=8)

        for label, value, limit in zip(labels, values, limits):
            table.add_row(
                label,
                self._signed_bar(value, limit=limit, width=bar_width),
                f"{float(value): .3f}",
            )

        return Panel(table, title=title, border_style="cyan", expand=False)

    def _compare_status(self, raw_value, expected_value, atol=1e-4, rtol=1e-4):
        if expected_value is None:
            return "[red]INVALID FORMAT[/red]"

        if self._is_invalid(raw_value):
            return "[red]INVALID FORMAT[/red]"

        try:
            raw = np.asarray(raw_value, dtype=np.float32).reshape(-1)
            exp = np.asarray(expected_value, dtype=np.float32).reshape(-1)
        except Exception:
            return "[red]INVALID FORMAT[/red]"

        raw = np.nan_to_num(raw, nan=0.0, posinf=0.0, neginf=0.0)
        exp = np.nan_to_num(exp, nan=0.0, posinf=0.0, neginf=0.0)

        if raw.shape != exp.shape:
            return "[red]WRONG[/red]"

        if np.allclose(raw, exp, atol=atol, rtol=rtol):
            return "[green]VALID[/green]"

        return "[red]WRONG[/red]"

    def _get_obs_constants(self):
        return {
            "LEG_JOINT2MOTOR_IDX": np.array([3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8], dtype=np.int32),
            "DEFAULT_ANGLES": np.array(
                [
                    0.1,  0.8, -1.5,
                   -0.1,  0.8, -1.5,
                    0.1,  1.0, -1.5,
                   -0.1,  1.0, -1.5,
                ],
                dtype=np.float32,
            ),
            "OBS_SCALES_ANG_VEL": 0.25,
            "CMD_SCALE": np.array([3.0, 2.0, 0.5], dtype=np.float32),
            "OBS_SCALES_DOF_POS": 1.0,
            "OBS_SCALES_DOF_VEL": 0.05,
        }

    def _get_low_cmd_target_positions(self):
        leg_joint2motor_idx = np.array([3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8], dtype=np.int32)

        low_cmd = getattr(self, "low_cmd", None)
        if low_cmd is None:
            return np.zeros(12, dtype=np.float32)

        target_q = np.zeros(12, dtype=np.float32)

        try:
            for i in range(12):
                motor_idx = int(leg_joint2motor_idx[i])
                target_q[i] = float(low_cmd.motor_cmd[motor_idx].q)
        except Exception:
            return np.zeros(12, dtype=np.float32)

        return target_q

    def _compute_expected_observation_parts(self):
        low_state_ref = getattr(self, "obs_low_state_ref", None)
        if low_state_ref is None:
            return None

        remote_ref = getattr(self, "obs_remote_ref", {})
        const = self._get_obs_constants()

        leg_joint2motor_idx = const["LEG_JOINT2MOTOR_IDX"]
        default_angles = const["DEFAULT_ANGLES"]
        obs_scales_ang_vel = const["OBS_SCALES_ANG_VEL"]
        cmd_scale = const["CMD_SCALE"]
        obs_scales_dof_pos = const["OBS_SCALES_DOF_POS"]
        obs_scales_dof_vel = const["OBS_SCALES_DOF_VEL"]

        try:
            ang_vel_raw = np.array(low_state_ref.imu_state.gyroscope, dtype=np.float32)
            quat_raw = np.array(low_state_ref.imu_state.quaternion, dtype=np.float32)
            gravity_orientation = np.array(get_gravity_orientation(quat_raw), dtype=np.float32)

            cmd_raw = np.zeros(3, dtype=np.float32)
            if getattr(self, "use_remote_controller", False):
                cmd_raw[0] = float(remote_ref.get("ly", 0.0))
                cmd_raw[1] = -float(remote_ref.get("lx", 0.0))
                cmd_raw[2] = -float(remote_ref.get("rx", 0.0))

            qj = np.zeros(12, dtype=np.float32)
            dqj = np.zeros(12, dtype=np.float32)
            for i in range(12):
                qj[i] = low_state_ref.motor_state[int(leg_joint2motor_idx[i])].q
                dqj[i] = low_state_ref.motor_state[int(leg_joint2motor_idx[i])].dq

            qj_obs = qj.copy() - default_angles
            dqj_obs = dqj.copy()

            last_action = None
            if getattr(self, "obs_action_ref", None) is not None:
                last_action = np.asarray(self.obs_action_ref, dtype=np.float32).reshape(-1)

            return {
                "ang_vel_raw": ang_vel_raw,
                "quat_raw": quat_raw,
                "gravity_raw": gravity_orientation,
                "cmd_raw": cmd_raw,
                "ang_vel_obs": ang_vel_raw * obs_scales_ang_vel,
                "gravity_obs": gravity_orientation,
                "cmd_obs": cmd_raw * cmd_scale,
                "qj_obs": qj_obs * obs_scales_dof_pos,
                "dqj_obs": dqj_obs * obs_scales_dof_vel,
                "last_action_obs": last_action,
            }
        except Exception:
            return None
        
    def _obs_blocks_table(self):
        raw_obs = getattr(self, "obs", None)
        expected = self._compute_expected_observation_parts()

        raw_ang_vel_slice = None if raw_obs is None else raw_obs[0:3]
        raw_gravity_slice = None if raw_obs is None else raw_obs[3:6]
        raw_cmd_slice = None if raw_obs is None else raw_obs[6:9]
        raw_qj_obs_slice = None if raw_obs is None else raw_obs[9:21]
        raw_dqj_obs_slice = None if raw_obs is None else raw_obs[21:33]
        raw_last_action_slice = None if raw_obs is None else raw_obs[33:45]

        table = Table(show_header=True, header_style="bold magenta", expand=True, padding=(1, 1))
        table.add_column("Observation block", width=12, no_wrap=True)
        table.add_column("Slice", width=8, no_wrap=True)
        table.add_column("Values", ratio=1)
        table.add_column("Status", width=16, no_wrap=True)

        table.add_row(
            "ang_vel", "0:3",
            self._fmt_obs_display(raw_ang_vel_slice),
            self._compare_status(raw_ang_vel_slice, None if expected is None else expected["ang_vel_obs"]),
        )
        table.add_row(
            "gravity", "3:6",
            self._fmt_obs_display(raw_gravity_slice),
            self._compare_status(raw_gravity_slice, None if expected is None else expected["gravity_obs"]),
        )
        table.add_row(
            "remote cmd", "6:9",
            self._fmt_obs_display(raw_cmd_slice),
            self._compare_status(raw_cmd_slice, None if expected is None else expected["cmd_obs"]),
        )
        table.add_row(
            "qj_obs", "9:21",
            self._fmt_obs_display(raw_qj_obs_slice),
            self._compare_status(raw_qj_obs_slice, None if expected is None else expected["qj_obs"]),
        )
        table.add_row(
            "dqj_obs", "21:33",
            self._fmt_obs_display(raw_dqj_obs_slice),
            self._compare_status(raw_dqj_obs_slice, None if expected is None else expected["dqj_obs"]),
        )
        table.add_row(
            "last_action", "33:45",
            self._fmt_obs_display(raw_last_action_slice),
            self._compare_status(raw_last_action_slice, None if expected is None else expected["last_action_obs"]),
        )

        return Panel(table, title="OBSERVATIONS", border_style="magenta")

    def _cmd_panel(self):
        raw_obs = getattr(self, "obs", None)
        cmd_obs = np.zeros(3, dtype=np.float32) if raw_obs is None else self._safe_array(raw_obs[6:9], 3)

        return self._vector_bars_table(
            "REMOTE COMMAND",
            ["vx", "vy", "yaw"],
            cmd_obs,
            limits=[3.1, 2.1, 0.6],
            bar_width=40,
        )

    def _policy_panel(self):
        raw_action = getattr(self, "action", None)
        action = self._safe_array(raw_action, 12)

        table = Table.grid(padding=(0, 1), expand=False)
        table.add_column(style="bold yellow", width=10)
        table.add_column(width=26)
        table.add_column(justify="right", width=8)

        for i, value in enumerate(action):
            table.add_row(
                f"a{i}",
                self._signed_bar(value, limit=1.0, width=24),
                f"{float(value): .3f}",
            )

        title = "POLICY OUTPUT"
        if self._is_invalid(raw_action):
            title += " [invalid->0]"

        return Panel(table, title=title, border_style="yellow")

    def _draw_line(self, canvas, x0, y0, x1, y1, char="•"):
        h = len(canvas)
        w = len(canvas[0])
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)

        for i in range(steps + 1):
            t = i / steps
            x = int(round(x0 + t * (x1 - x0)))
            y = int(round(y0 + t * (y1 - y0)))
            if 0 <= x < w and 0 <= y < h:
                canvas[y][x] = char

    def _leg_points(self, thigh_angle, calf_angle, width=17, height=9):
        thigh_angle = self._safe_scalar(thigh_angle, 0.0)
        calf_angle = self._safe_scalar(calf_angle, 0.0)

        hip_x = width // 2
        hip_y = 1

        l1 = 3.0
        l2 = 3.0

        theta1 = math.pi / 2 + thigh_angle
        theta2 = theta1 + calf_angle

        knee_x = hip_x + l1 * math.cos(theta1)
        knee_y = hip_y + l1 * math.sin(theta1)

        foot_x = knee_x + l2 * math.cos(theta2)
        foot_y = knee_y + l2 * math.sin(theta2)

        knee_x = 0 if not math.isfinite(knee_x) else knee_x
        knee_y = 0 if not math.isfinite(knee_y) else knee_y
        foot_x = 0 if not math.isfinite(foot_x) else foot_x
        foot_y = 0 if not math.isfinite(foot_y) else foot_y

        return (
            (int(round(hip_x)), int(round(hip_y))),
            (int(round(knee_x)), int(round(knee_y))),
            (int(round(foot_x)), int(round(foot_y))),
        )

    def _get_joint_limits(self):
        joint_max = np.array(
            [0.960, 2.704, 0.735,
             1.161, 2.704, 0.735,
             0.962, 3.552, 0.735,
             1.162, 3.552, 0.735],
            dtype=np.float32,
        )

        joint_min = np.array(
            [-1.161, -2.386, -1.458,
             -0.961, -2.384, -1.297,
             -1.164, -1.544, -1.338,
             -0.961, -1.537, -1.293],
            dtype=np.float32,
        )

        return joint_min, joint_max

    def _leg_ascii(self, leg_name, start_idx):
        low_cmd_target = self._get_low_cmd_target_positions()
        joint_min, joint_max = self._get_joint_limits()

        hip_angle = float(low_cmd_target[start_idx])
        thigh_angle = float(low_cmd_target[start_idx + 1])
        calf_angle = float(low_cmd_target[start_idx + 2])

        leg_angles = np.array([hip_angle, thigh_angle, calf_angle], dtype=np.float32)
        leg_min = joint_min[start_idx:start_idx + 3]
        leg_max = joint_max[start_idx:start_idx + 3]

        in_band = np.all((leg_angles >= leg_min) & (leg_angles <= leg_max))

        values = Table.grid(padding=(0, 1), expand=False)
        values.add_column(style="bold blue", width=6)
        values.add_column(justify="right", width=7)
        values.add_row("hip", f"{hip_angle: .2f}")
        values.add_row("thigh", f"{thigh_angle: .2f}")
        values.add_row("calf", f"{calf_angle: .2f}")

        width = 17
        height = 9

        if not in_band:
            warning_lines = [
                "",
                " Invalid angle ",
                " out of band  ",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
            warning_block = Text("\n".join(line.ljust(width) for line in warning_lines), style="bold red")

            return Panel(
                Group(
                    warning_block,
                    values,
                ),
                title=f"{leg_name} q target",
                border_style="red",
            )

        canvas = [[" " for _ in range(width)] for _ in range(height)]

        hip, knee, foot = self._leg_points(thigh_angle, calf_angle, width=width, height=height)

        self._draw_line(canvas, hip[0], hip[1], knee[0], knee[1], char="•")
        self._draw_line(canvas, knee[0], knee[1], foot[0], foot[1], char="•")

        if 0 <= hip[1] < height and 0 <= hip[0] < width:
            canvas[hip[1]][hip[0]] = "H"
        if 0 <= knee[1] < height and 0 <= knee[0] < width:
            canvas[knee[1]][knee[0]] = "K"
        if 0 <= foot[1] < height and 0 <= foot[0] < width:
            canvas[foot[1]][foot[0]] = "F"

        lines = ["".join(row).rstrip() for row in canvas]
        ascii_leg = "\n".join(line if line else " " for line in lines)

        return Panel(
            Group(
                Text(ascii_leg),
                values,
            ),
            title=f"{leg_name} q target",
            border_style="blue",
        )

    def _targets_panel(self):
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)

        grid.add_row(
            self._leg_ascii("FL", 0),
            self._leg_ascii("FR", 3),
        )
        grid.add_row(
            self._leg_ascii("RL", 6),
            self._leg_ascii("RR", 9),
        )

        legend = Panel(
            Text("H=hip  K=knee  F=foot", justify="center", style="dim"),
            border_style="blue",
        )

        return Panel(Group(grid, legend), title="LEG TARGET CONTROL", border_style="blue")

    def render_dashboard(self):
        counter = getattr(self, "counter", 0)
        num_obs = getattr(self, "num_obs", 45)
        num_actions = getattr(self, "num_actions", 12)
        control_dt = getattr(self, "control_dt", 0.02)

        header = Panel(
            Text(
                f"step = {counter} | observations dimension = {num_obs} | action dimension = {num_actions} | dt = {control_dt:.3f}s",
                justify="center",
                style="bold white",
            ),
            border_style="white",
        )

        cmd_center = Table.grid(expand=True)
        cmd_center.add_column(ratio=1)
        cmd_center.add_column(ratio=2)
        cmd_center.add_column(ratio=1)
        cmd_center.add_row("", self._cmd_panel(), "")

        obs_stack = Group(
            self._obs_blocks_table(),
            cmd_center,
        )

        layout = Layout()
        layout.split_column(
            Layout(header, size=3),
            Layout(name="main"),
        )

        layout["main"].split_row(
            Layout(obs_stack, ratio=2),
            Layout(name="right", ratio=1),
        )

        layout["right"].split_column(
            Layout(self._policy_panel(), size=16),
            Layout(self._targets_panel(), ratio=1),
        )

        return layout