import threading
import time
import cv2
import mediapipe as mp
import numpy as np
from config import CONTROL_HEIGHT, CONTROL_WIDTH


class RastreadorPes:

    def __init__(self, config, largura_tela, altura_tela):
        self.config = config
        self.pontos_calibracao = config["calibration_point"]
        self.matriz = cv2.getPerspectiveTransform(
            np.float32(self.pontos_calibracao),
            np.float32([[0, 0], [largura_tela, 0], [0, altura_tela], [largura_tela, altura_tela]]),
        )
        self.trava = threading.Lock()
        self.pes_detectados = []
        self.frame_captura = None
        self.ativo = False
        self.landmarker = None
        self.thread = None
        self.camera = cv2.VideoCapture(config["camera_position"], config["backend_camera"])

    def iniciar(self):
        if not self.camera.isOpened():
            print("Webcam não encontrada, jogando só com o mouse.")
            return False
        try:
            opcoes = mp.tasks.vision.PoseLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=self.config["model"]),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_poses=1,
                min_pose_detection_confidence=self.config["detection_position"],
                min_pose_presence_confidence=self.config["detection_presence"],
                min_tracking_confidence=self.config["detection_tracking"],
            )
            self.landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(opcoes)
        except Exception as erro:
            print("Controle pelos pés desativado:", erro)
            return False
        self.ativo = True
        self.thread = threading.Thread(target=self._ler_camera, daemon=True)
        self.thread.start()
        return True

    def para_tela(self, x, y):
        p = np.float32([[[x * CONTROL_WIDTH, y * CONTROL_HEIGHT]]])
        tx, ty = cv2.perspectiveTransform(p, self.matriz)[0][0]
        return float(tx), float(ty)

    def pes_na_tela(self):
        with self.trava:
            return list(self.pes_detectados)

    def pegar_frame(self):
        with self.trava:
            frame = self.frame_captura
            self.frame_captura = None
        return frame

    def parar(self):
        self.ativo = False
        if self.thread:
            self.thread.join(timeout=1)
        self.camera.release()
        if self.landmarker:
            self.landmarker.close()

    def _ler_camera(self):
        ultimo_ts = 0
        while self.ativo:
            ok, frame = self.camera.read()
            if not ok:
                time.sleep(0.01)
                continue
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ultimo_ts = max(int(time.monotonic() * 1000), ultimo_ts + 1)
            resultado = self.landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ultimo_ts)
            pes = []
            if resultado.pose_landmarks:
                pontos = resultado.pose_landmarks[0]
                for calcanhar, ponta in ((29, 31), (30, 32)):
                    x = (pontos[calcanhar].x + pontos[ponta].x) / 2
                    y = (pontos[calcanhar].y + pontos[ponta].y) / 2
                    pes.append(self.para_tela(x, y))
            with self.trava:
                self.pes_detectados = pes

            h, w = frame.shape[:2]
            escala = (w / CONTROL_WIDTH, h / CONTROL_HEIGHT)
            cantos = [(int(px * escala[0]), int(py * escala[1])) for px, py in self.pontos_calibracao]
            for a, b in ((0, 1), (1, 3), (3, 2), (2, 0)):
                cv2.line(frame, cantos[a], cantos[b], (0, 255, 0), 2)
            if resultado.pose_landmarks:
                for i in (29, 30, 31, 32):
                    p = resultado.pose_landmarks[0][i]
                    cv2.circle(frame, (int(p.x * w), int(p.y * h)), 6, (0, 0, 255), -1)
            with self.trava:
                self.frame_captura = frame