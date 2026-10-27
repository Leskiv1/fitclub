"""Metaclass for the Singleton pattern."""

from threading import Lock
from typing import Any, ClassVar


class SingletonMeta(type):
    """GoF: Singleton — every class with this metaclass has exactly one instance per process.

    Calling the class returns the same object every time; the lock makes the first creation thread-safe
    (uvicorn handles requests in a thread pool).
    """

    _instances: ClassVar[dict[type, Any]] = {}
    _lock: ClassVar[Lock] = Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:  # double-checked: another thread may have created it meanwhile
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
