# GPU Lock
This package manages GPU access between users, to stop us from accidentaly starting a process on a GPU that another user is currently using for their research. This approach is superior to using nvidia-smi as a GPU will remain locked even if we are not using the GPU during brief interruptions in our scripts (for example finding a new set of hyperparameters when running hyperparameter optimization). 

This package manages GPU access between users by placing files in /var/tmp/gpu_locks. It automatically sets CUDA_VISIBLE_DEVICES to the uids of the GPUs you hold locks for. All of the locking is consensus based - it only works if everyone is using this library. Having a lock does not systematically stop another user from using the GPU you "locked".

## Installation:
You can install this package using pip:
```shell
pip install git+https://github.com/idsc-frazzoli/gpu_lock.git
```

## Updating
As this package is still under development we may sometimes push changes to this repo. You can install these updates using:
```shell
pip install --upgrade git+https://github.com/idsc-frazzoli/gpu_lock.git
```

## Usage:
GPU locks use the python "with" sytax. This will automatically create a lock and close it after your script ends, even if errors occurr. For example, if you want to aquire a lock on a single GPU:
```python
from gpu_lock import lock_gpu

if __name__=="__main__":
    with lock_gpu() as lock:
        print(f"Locked GPUS {lock.uid}")
        # your existing code goes here, do stuff with the GPU.
```
Behind the scenes this attempts to create locks on all GPUs and returns the first lock that can be aquired.
If you want to attempt to aquire a lock on multiple (i.e. 3) GPUs:
```python
from gpu_lock import lock_gpu

if __name__=="__main__":
    with lock_gpu(n=3) as lock:
        print(f"Locked GPUS {lock.uid}")
        # your existing code goes here, do stuff with the GPU.
```

## How does this work?
The basic system behind is very simple: If you want to acquire a lock on a GPU with uid {i} the library checks if the file /var/tmp/gpu_locks/gpu_{i}.json exists. If it does not exist the lock will be aquired by creating a new lockfile. If the file exists the library will parse it and check for the following conditions:
- If your current pid created the lock, the old lock will be removed and you will be allowed to create a new lockfile.
- If the "owner" process PID is dead, the old lockfile will be removed and you will create a new lockfile.
- In all other cases you will not be allowed to create a lockfile and a RumtimeError will be raised.

Since we cannot be sure that all users will immidately be using this library we use a python wrapper to parse GPU utilization from nvidia-smi and only acquire a lock on GPUs which are not busy.

## Lockfiles
Lockfiles are just JSON files that contain information such as your username and the time you created the lock. For example:
``` json
{
    "user": "hetzell", 
    "time": 1579317555, 
    "id": 0, 
    "owner": 22982
}
```
Importantly the lockfile also contains the PID of the process that created the lock. The lockfile will be treated as stale if the owner process is no longer alive. Stale lockfiles will be ignored and overwritten by other users requesting the resource subsequently.
