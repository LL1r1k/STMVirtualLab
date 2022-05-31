import logging
import traceback
from collections import defaultdict
from typing import Any, Dict, List, Optional
import copy
from pygdbmi.gdbcontroller import GdbController  # type: ignore

from pyocd.__main__ import PyOCDTool
import threading
import sys
import ctypes
import time

logger = logging.getLogger(__name__)
GDB_MI_FLAG = ["--interpreter=mi2"]

class thread_openOCD(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        try:
            server_args = ['gdbserver',
            '--target=stm32f103rc']
            pyOCDTool = PyOCDTool()
            pyOCDTool._setup_logging = lambda: None
            sys.exit(pyOCDTool.run(args=server_args))
        finally:
            a = 10

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            logger.info("Exception raise failure")


class StateManager(object):
    def __init__(self, config: Dict[str, Any]):
        self.controller_to_client_ids: Dict[GdbController, List[str]] = defaultdict(
            list
        )  # key is controller, val is list of client ids
        self.gdb_reader_thread = None
        self.config = config
        self.openOCD = None

    def get_gdb_args(self):
        gdb_args = copy.copy(GDB_MI_FLAG)
        if self.config["gdb_args"]:
            gdb_args += self.config["gdb_args"]

        if self.config["initial_binary_and_args"]:
            gdb_args += ["--args"]
            gdb_args += self.config["initial_binary_and_args"]
        return gdb_args



    def connect_client(self, client_id: str, desired_gdbpid: int) -> Dict[str, Any]:
        message = ""
        pid: Optional[int] = 0
        error = False
        using_existing = False

        if desired_gdbpid > 0:
            controller = self.get_controller_from_pid(desired_gdbpid)

            if controller:
                self.controller_to_client_ids[controller].append(client_id)
                message = (
                    "gdbgui is using existing subprocess with pid %s, "
                    "originally opened with command %s"
                ) % (str(desired_gdbpid), controller.get_subprocess_cmd())
                using_existing = True
                pid = desired_gdbpid
            else:
                print("error! could not find that pid")
                message = "Could not find a gdb subprocess with pid %s. " % str(
                    desired_gdbpid
                )
                error = True

        if self.get_controller_from_client_id(client_id) is None:

            gdb_args = self.get_gdb_args()

            controller = GdbController(
                gdb_path=self.config["gdb_path"],
                gdb_args=gdb_args,
                rr=self.config["rr"],
            )
            self.controller_to_client_ids[controller].append(client_id)

            pid = self.get_pid_from_controller(controller)
            if pid is None:
                error = True
                message = "Developer error"
            else:
                message += "gdbgui spawned subprocess with pid %s from command %s." % (
                    str(pid),
                    controller.get_subprocess_cmd(),
                )

            self.openOCD = thread_openOCD()
            self.openOCD.start()

        return {
            "pid": pid,
            "message": message,
            "error": error,
            "using_existing": using_existing,
        }


    def remove_gdb_controller_by_pid(self, gdbpid: int) -> List[str]:
        controller = self.get_controller_from_pid(gdbpid)
        if controller:
            orphaned_client_ids = self.remove_gdb_controller(controller)
        else:
            logger.info("could not find gdb controller with pid " + str(gdbpid))
            orphaned_client_ids = []
        return orphaned_client_ids

    def remove_gdb_controller(self, controller: GdbController) -> List[str]:
        try:
            controller.exit()
            self.openOCD.raise_exception()
        except Exception:
            logger.error(traceback.format_exc())
        orphaned_client_ids = self.controller_to_client_ids.pop(controller, [])
        return orphaned_client_ids

    def get_client_ids_from_gdb_pid(self, pid: int) -> List[str]:
        controller = self.get_controller_from_pid(pid)
        return self.controller_to_client_ids.get(controller, [])

    def get_client_ids_from_controller(self, controller: GdbController):
        return self.controller_to_client_ids.get(controller, [])

    def get_pid_from_controller(self, controller: GdbController) -> Optional[int]:
        if controller and controller.gdb_process:
            return controller.gdb_process.pid

        return None

    def get_controller_from_pid(self, pid: int) -> Optional[GdbController]:
        for controller in self.controller_to_client_ids:
            this_pid = self.get_pid_from_controller(controller)
            if this_pid == pid:
                return controller

        return None

    def get_controller_from_client_id(self, client_id: str) -> Optional[GdbController]:
        for controller, client_ids in self.controller_to_client_ids.items():
            if client_id in client_ids:
                return controller

        return None

    def exit_all_gdb_processes(self):
        logger.info("exiting all subprocesses")
        for controller in self.controller_to_client_ids:
            controller.exit()
            self.controller_to_client_ids.pop(controller)

    def get_dashboard_data(self):
        data = {}
        for controller, client_ids in self.controller_to_client_ids.items():
            if controller.gdb_process:
                pid = str(controller.gdb_process.pid)
            else:
                pid = "process no longer exists"
            data[pid] = {
                "cmd": " ".join(controller.cmd),
                "abs_gdb_path": controller.abs_gdb_path,
                "number_of_connected_browser_tabs": len(client_ids),
                "client_ids": client_ids,
            }
        return data

    def disconnect_client(self, client_id: str):
        for _, client_ids in self.controller_to_client_ids.items():
            if client_id in client_ids:
                client_ids.remove(client_id)

    def _spawn_new_gdb_controller(self):
        pass

    def _connect_to_existing_gdb_controller(self):
        pass
