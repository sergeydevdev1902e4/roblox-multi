import sys
import ctypes
from typing import Optional

MUTEX_NAME = "ROBLOX_singletonMutex"


class SingletonMutex:
    def __init__(self):
        self.handle: Optional[int] = None

    def acquire(self) -> bool:
        if sys.platform != "win32":
            # non-windows runners do not enforce the same win32 mutex
            return True

        kernel32 = ctypes.windll.kernel32
        # CreateMutexW with bInitialOwner=True keeps ownership so roblox can't claim exclusivity
        self.handle = kernel32.CreateMutexW(None, True, MUTEX_NAME)
        if not self.handle:
            return False
        return True

    def release(self):
        if sys.platform == "win32" and self.handle:
            ctypes.windll.kernel32.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
