from enum import Enum


class MethodType(Enum):
    HTTP = "http"
    HEADLESS = "headless"
    NON_HEADLESS = "non_headless"


class RunsStatus(Enum):
    COMPLETED = "completed"
    FAILED = "failed"
