# GPU Lock
This python package manages GPU access by placing files in /var/tmp/gpu_locks. A lock is aquired if for a given GPU no lock file exists. GPUs are selected by their ID.
## Usage:
GPU locks use the python "with" sytax. This will automatically create a lock and close it after your script ends, even if errors occurr. For example, if you want to aquire a lock on the GPU with ID 0:
```python
from gpu_lock import lock_gpu

if __name__=="__main__":
    with lock_gpu(uid=0):
        # your existing code goes here, do stuff with the GPU.
```
If you want to attempt to aquire a lock on any GPU (This will fail if all GPUs are busy.)
```python
from gpu_lock import lock_gpu

if __name__=="__main__":
    with lock_gpu():
        # your existing code goes here, do stuff with the GPU.
```

## How does this work?
The basic system behind this is very simple: If you acquire a GPULock it checks if there is a file containing the GPU uid you are requesting in the /var/tmp/gpu_locks directory. If the file does not exist or the owner process is no longer alive or the lock was created by you the old lockfile will be overwritten. Lockfiles are just json file that contain information such as your username and the time you created the lock. For example:
``` json
{
    "user": "hetzell", 
    "time": 1579317555, 
    "id": 0, 
    "owner": 22982
}
```
