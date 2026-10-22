import cv2
from ttea.util import PathConfig
from ttea.model import CalibrationPoint
from ttea.service import CalibrationService

# pra puxar as config do console do ttea

CONTROL_WIDTH, CONTROL_HEIGHT = 640, 480


def carregar_config():
    config = {
        "screen_position": 0,
        "camera_position": 0,
        "backend_camera": cv2.CAP_ANY,
        "model": PathConfig.model("pose_landmarker_full.task"),
        "detection_position": 0.5,
        "detection_presence": 0.5,
        "detection_tracking": 0.5,
        "calibration_point": [(0, 0), (CONTROL_WIDTH, 0), (0, CONTROL_HEIGHT), (CONTROL_WIDTH, CONTROL_HEIGHT)],
    }
    
    calibracao = CalibrationService()
        
    config["screen_position"] = calibracao.get_screen_info()["screen_position"]
    config["camera_position"] = calibracao.get_camera_info()["camera_position"]
    config["backend_camera"] = calibracao.get_opencv_capture_backend()
    ponto = calibracao.find_by_id_calibration_point(CalibrationPoint.ID_VALUE)
    if ponto:
        config["calibration_point"] = [
            (ponto.pointx1, ponto.pointy1),
            (ponto.pointx2, ponto.pointy2),
            (ponto.pointx3, ponto.pointy3),
            (ponto.pointx4, ponto.pointy4),
        ]
    config["model"] = PathConfig.model(calibracao.get_mediapipe_model_desktop())
    config["detection_position"] = calibracao.get_mediapipe_detection_position()
    config["detection_presence"] = calibracao.get_mediapipe_detection_presence()
    config["detection_tracking"] = calibracao.get_mediapipe_detection_tracking()
    
    return config