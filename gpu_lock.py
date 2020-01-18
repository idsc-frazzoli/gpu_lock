import getpass
import logging
import os
import json
import time

import time
from pathlib import Path
from typing import Optional, List, Set, Union

LOCKDIR = "/var/tmp/gpu_lock"

class _GPULock:
    """
    Creates a Lock on a single GPU by creating a JSON file in LOCKDIR.
    """
    def __init__(self, uid: int = None):
        self.user: str = getpass.getuser()
        self.uid: int = uid
        self.pid: int = os.getpid()
            
        self.lock_dir: Path = Path(LOCKDIR)
        self.lock_dir.mkdir(mode=666, exist_ok=True, parents=False)

        self.lock: Path = self.lock_dir / f"gpu_{self.uid}.json"

    def __enter__(self):
        self._aquire_lock()
        self._add_uid_visible_devices()

    def __exit__(self, exit_type, value, traceback):
        self._remove_uid_visible_devices()
        self._release_lock()
    
    def _add_uid_visible_devices(self) -> None:
        os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
        try:
            visible_devices: Set[str] = self._parse_visible_devices()
            visible_devices.add(str(self.uid))
        except KeyError:
            visible_devices = set([str(self.uid)])
        
        self._set_visible_devices(visible_devices)

    def _remove_uid_visible_devices(self) -> None:
        visible_devices: Set[str] = self._parse_visible_devices()
        visible_devices.remove(str(self.uid))
        self._set_visible_devices(visible_devices)

    def _release_lock(self) -> None:
        if os.path.exists(self.lock):
            os.remove(self.lock)
            logging.debug(f"Released GPU {self.uid} lock")
        else:
            logging.debug(f"GPU {self.uid} lockfile was not created, so it will not be removed.") 

    def _aquire_lock(self) -> None: 
        self.check_lock_availability()
        if self.lock.exists():
            os.remove(self.lock)
        self._create_lock()

    def _create_lock(self) -> None:
        with open(self.lock, mode="w", newline="") as lockfp:
            json.dump({"user": self.user, "time": int(time.time()), "uid": self.uid, "owner": self.pid}, fp=lockfp, indent=4)
        os.chmod(self.lock, 666)
        logging.debug(f"Aquired lock on GPU {self.uid}")

    def check_lock_availability(self) -> None:
        """
        Check if a lock can be aquired for the GPU with uid self.uid
        
        Raises
        ------
        RuntimeError
            If a valid and current lock exists for the GPU with uid self.uid.
        """
        if self.lock.exists():
            with open(self.lock, mode="r") as lockfp:
                lock = json.load(lockfp)
            
            if lock["user"] == self.user or lock["owner"] == self.pid:
                logging.warning(f"Found existing GPU lock for user {self.user}. Please make sure to release resources after finishing your scripts. Old lock will be renewed.")
            elif not self.check_pid_alive(pid=lock["owner"]):
                logging.debug(f"Found stale GPU lock with dead owner.")
            else:
                raise RuntimeError(f"Could not aquire lock. The resource is locked by {lock['user']}")
    
    @staticmethod
    def check_pid_alive(pid: int) -> bool:        
        """ 
        Check For the existence of a unix pid.
        """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True
    
    @staticmethod
    def _parse_visible_devices() -> Set[str]:
        return set(os.environ["CUDA_VISIBLE_DEVICES"].replace(" ", "").split(","))

    @staticmethod
    def _set_visible_devices(visible_devices: Set[str]) -> None:
        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(visible_devices)


class _MultiGPULock:
    """
    This class allows users to Lock multiple GPUs by creating a single lock that can be opened using the python with syntax.
    """
    
    def __init__(self, n: int, n_system_gpus: int):
        """
        Create a new instance.
        
        Parameters
        ----------
        n : int
            The number of GPUs to aquire locks for.
        n_system_gpus : int
            The total number of GPUs in the system.
        
        Raises
        ------
        RuntimeError
            If less than n GPUs are available.
        """
        self.locks: List[_GPULock] = []
        for uid in range(n_system_gpus):
            try:
                new_lock = _GPULock(uid)
                new_lock.check_lock_availability()
                self.locks.append(new_lock)

                if len(self.locks) == n:
                    break
            except RuntimeError:
                logging.info(f"Could not aquire lock on GPU {uid}")
        
        self.uid: List[int] = [lock.uid for lock in self.locks]
        
        if len(self.locks) < n:
            raise RuntimeError(f"Could not acquire at {n} locks. Too many GPUs are busy!")
    
    def __enter__(self):
        for lock in self.locks:
            lock.__enter__()
    
    def __exit__(self, exit_type, value, traceback):
        for lock in self.locks:
            lock.__exit__(exit_type, value, traceback)


def lock_gpu(n: int = 1, n_system_gpus: int= 8) -> Union[_MultiGPULock, _GPULock]:
    """
    Get a lock on one or multiple GPUs.
    
    Parameters
    ----------
    n : int, optional
        specifies the number of GPUs that should be acquired, by default 1
    n_system_gpus : int, optional
        the total number of GPUs in your system. For Rudolf this should never need to be changed, by default 8
    
    Returns
    -------
    Union[_MultiGPULock, _GPULock]
        Returns a single _GPULock if n==1 or a _MultiGPULock if n>1.
    """
    if n == 1:
        for uid in range(n_system_gpus):
            try:
                new_lock = _GPULock(uid)
                new_lock.check_lock_availability()
                return new_lock
            except RuntimeError:
                logging.info(f"Could not aquire lock on GPU {uid}")

    else:
        return _MultiGPULock(n, n_system_gpus)
