from api.auth import router as auth_router
from api.prediction import router as prediction_router
from api.history import router as history_router
from api.profile import router as profile_router
from api.sensor import router as sensor_router

__all__ = [
    "auth_router",
    "prediction_router",
    "history_router",
    "profile_router",
    "sensor_router"
]
