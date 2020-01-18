import getpass
import logging
import os
import json
import time

import time
from pathlib import Path
from typing import Optional

N_GPUS = 8

class _GPULock:
    def __init__(self, uid: int = None):
        self.user: str = getpass.getuser()
        self.uid: int = uid
        self.pid: int = os.getpid()
            
        self.lock_dir: Path = Path("/var/tmp/gpu_lock")
        self.lock_dir.mkdir(exist_ok=True, parents=False)

        self.lock: Path = self.lock_dir / f"gpu_{self.uid}.json"

    def __enter__(self):
        self._aquire_lock()

    def __exit__(self, type, value, traceback):
        self._release_lock()
    
    def _release_lock(self):
        if os.path.exists(self.lock):
            os.remove(self.lock)
            logging.debug(f"Released GPU {self.uid} lock")
        else:
            logging.debug(f"GPU {self.uid} lockfile was not created, so it will not be removed.") 

    def _aquire_lock(self):
        self.check_lock_availability()
        self._create_lock()

    def _create_lock(self):
        with open(self.lock, mode="w", newline="") as lockfp:
            json.dump({"user": self.user, "time": int(time.time()), "id": self.uid, "owner": self.pid}, fp=lockfp, indent=4)
        os.chmod(self.lock, 777)
        logging.debug(f"Aquired lock on GPU {self.uid}")

    def check_lock_availability(self) -> None:
        if self.lock.exists():
            with open(self.lock, mode="r") as lockfp:
                lock = json.load(lockfp)
            
            if lock["user"] == self.user or lock["owner"] == self.pid:
                logging.warning(f"Found existing GPU lock for user {self.user}. Please make sure to release resources after finishing your scripts. Old lock will be renewed.")
                os.remove(self.lock)
                logging.debug(f"Released old GPU lock held by {self.user}")
            elif not self.check_pid_alive(pid=lock["owner"]):
                logging.debug(f"Found stale GPU lock with dead owner.")
                os.remove(self.lock)
                logging.info(f"Released stale GPU lock held by {lock['user']}")
            else:
                raise EnvironmentError(f"Could not aquire lock. The resource is locked by {lock['user']}")
    
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


def lock_gpu(uid: Optional[int]=None) -> _GPULock:
    if uid is not None:
        return _GPULock(uid)
    else:
        uid: int
        for uid in range(N_GPUS):
            try:
                return _GPULock(uid)
            except RuntimeError:
                logging.info(f"GPU with uid {uid} was locked.")
        raise RuntimeError("All GPUs are currently busy.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    with lock_gpu(uid=0):
        while True:
            time.sleep(10)