import time
import mujoco
import mujoco.viewer
from threading import Thread
import threading

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py_bridge import UnitreeSdk2Bridge, ElasticBand, VirtualRemoteUI

import config

locker = threading.Lock()
shutdown_event = threading.Event()

mj_model = mujoco.MjModel.from_xml_path(str(config.ROBOT_SCENE))
mj_data = mujoco.MjData(mj_model)

# Disable shadows and material reflections before creating the viewer.
# Rendering flags belong to MjvScene, which launch_passive() does not expose.
mj_model.light_castshadow[:] = 0
mj_model.mat_reflectance[:] = 0


if config.ENABLE_ELASTIC_BAND:
    elastic_band = ElasticBand()
    if config.ROBOT == "h1" or config.ROBOT == "g1":
        band_attached_link = mj_model.body("torso_link").id
    else:
        band_attached_link = mj_model.body("base_link").id
    viewer = mujoco.viewer.launch_passive(
        mj_model, mj_data, key_callback=elastic_band.MujuocoKeyCallback
    )
else:
    elastic_band = None
    viewer = mujoco.viewer.launch_passive(mj_model, mj_data)

mj_model.opt.timestep = config.SIMULATE_DT
num_motor_ = mj_model.nu
dim_motor_sensor_ = 3 * num_motor_

time.sleep(0.2)

ChannelFactoryInitialize(config.DOMAIN_ID, config.INTERFACE)
unitree = UnitreeSdk2Bridge(mj_model, mj_data)
unitree.SetupVirtualRemote()
virtual_ui = VirtualRemoteUI(unitree.GetVirtualRemoteState())

if config.PRINT_SCENE_INFORMATION:
    unitree.PrintSceneInformation()


def SimulationThread():
    global mj_data, mj_model

    while viewer.is_running() and not shutdown_event.is_set():
        step_start = time.perf_counter()

        locker.acquire()

        if config.ENABLE_ELASTIC_BAND:
            if elastic_band.enable:
                mj_data.xfrc_applied[band_attached_link, :3] = elastic_band.Advance(
                    mj_data.qpos[:3], mj_data.qvel[:3]
                )
        mujoco.mj_step(mj_model, mj_data)

        locker.release()

        time_until_next_step = mj_model.opt.timestep - (
            time.perf_counter() - step_start
        )
        if time_until_next_step > 0:
            time.sleep(time_until_next_step)


def PhysicsViewerThread():
    while viewer.is_running() and not shutdown_event.is_set():
        locker.acquire()
        viewer.sync()
        locker.release()
        time.sleep(config.VIEWER_DT)


if __name__ == "__main__":
    viewer_thread = Thread(target=PhysicsViewerThread, daemon=True)
    sim_thread = Thread(target=SimulationThread, daemon=True)

    viewer_thread.start()
    sim_thread.start()

    virtual_ui.start()
    try:
        while viewer.is_running() and virtual_ui.pump_once():
            time.sleep(0.005)
    finally:
        shutdown_event.set()
        virtual_ui.stop()
