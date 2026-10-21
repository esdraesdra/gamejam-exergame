import os
import random
import threading
import time
import urllib.request

import cv2
import mediapipe as mp
import pygame

# pra abrir a janela
pygame.init()
tela = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Game Jam")
relogio = pygame.time.Clock()

verde = (0, 200, 0)
azul = (0, 100, 255)
vermelho = (220, 0, 0)
amarelo = (255, 220, 0)

colunas = [85, 280, 475, 670]
cores = [verde, azul, vermelho, amarelo]
alvos = [
    (pygame.Rect(20, 405, 175, 175), verde),
    (pygame.Rect(215, 405, 175, 175), azul),
    (pygame.Rect(410, 405, 175, 175), vermelho),
    (pygame.Rect(605, 405, 175, 175), amarelo),
]

pontuacao = 0
fonte = pygame.font.Font(None, 48)

velocidade = 1
frequencia_spawn = 0.4
ultimo_spawn = 0 #pra n criar um em cima do outro
quadrados = [] # guarda todos os quadrados na tela

arrastando = None
margem_pegar = 25
offset_x = 0
offset_y = 0


def pegar(pos):
    global arrastando, offset_x, offset_y
    perto = [q for q in quadrados if pygame.Rect(q[0], q[1], 44, 44).inflate(margem_pegar * 2, margem_pegar * 2).collidepoint(pos)]
    if perto:
        quadrado = min(perto, key=lambda q: (q[0] + 22 - pos[0]) ** 2 + (q[1] + 22 - pos[1]) ** 2)
        arrastando = quadrado
        offset_x = quadrado[0] - pos[0]
        offset_y = quadrado[1] - pos[1]


def mover(pos):
    if arrastando:
        arrastando[0] = max(0, min(pos[0] + offset_x, tela.get_width() - 44))
        arrastando[1] = min(pos[1] + offset_y, 405 - 44)


def soltar():
    global arrastando
    arrastando = None


caminho_modelo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gesture_recognizer.task")
url_modelo = "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task"

ultimo_resultado = None
camera_ativa = False


def ao_reconhecer(resultado, imagem, timestamp):
    global ultimo_resultado
    ultimo_resultado = resultado

def ler_camera():
    ultimo_ts = 0
    while camera_ativa:
        ok, frame = camera.read()
        if not ok:
            time.sleep(0.01)
            continue
        rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        ultimo_ts = max(int(time.monotonic() * 1000), ultimo_ts + 1)
        reconhecedor.recognize_async(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ultimo_ts)

camera = cv2.VideoCapture(0)
reconhecedor = None
if camera.isOpened():
    try:
        if not os.path.exists(caminho_modelo):
            urllib.request.urlretrieve(url_modelo, caminho_modelo)
        opcoes = mp.tasks.vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=caminho_modelo),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=1,
            result_callback=ao_reconhecer,
        )
        reconhecedor = mp.tasks.vision.GestureRecognizer.create_from_options(opcoes)
        camera_ativa = True
        thread_camera = threading.Thread(target=ler_camera, daemon=True)
        thread_camera.start()
    except Exception as erro:
        print("Controle por mão desativado:", erro)
else:
    print("Webcam não encontrada, jogando só com o mouse.")

cursor_x = tela.get_width() / 2
cursor_y = tela.get_height() / 2
mao_visivel = False
mao_fechada = False
ultimo_punho = 0
tempo_soltar = 600
tempo_soltar_aberta = 75

rodando = True
while rodando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pegar(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            soltar()
        elif evento.type == pygame.MOUSEMOTION:
            mover(evento.pos)

    resultado = ultimo_resultado
    gesto = "None"
    mao_visivel = bool(resultado and resultado.hand_landmarks)
    if mao_visivel:
        ponto = resultado.hand_landmarks[0][9]
        alvo_x = max(0, min((ponto.x - 0.15) / 0.7, 1)) * tela.get_width()
        alvo_y = max(0, min((ponto.y - 0.15) / 0.7, 1)) * tela.get_height()
        cursor_x += (alvo_x - cursor_x) * 0.4
        cursor_y += (alvo_y - cursor_y) * 0.4
        if resultado.gestures:
            gesto = resultado.gestures[0][0].category_name

    cursor = (int(cursor_x), int(cursor_y))
    agora_mao = pygame.time.get_ticks()
    if gesto == "Closed_Fist":
        ultimo_punho = agora_mao
        if not mao_fechada:
            pegar(cursor)
            mao_fechada = True
    elif mao_fechada:
        sem_punho = agora_mao - ultimo_punho
        if (gesto == "Open_Palm" and sem_punho >= tempo_soltar_aberta) or sem_punho >= tempo_soltar:
            soltar()
            mao_fechada = False
    if mao_fechada and mao_visivel:
        mover(cursor)

    agora = pygame.time.get_ticks()

    if agora - ultimo_spawn >= 1000 / frequencia_spawn:
        livres = [c for c in colunas if not any(abs(q[0] - c) < 44 and q[1] < 0 for q in quadrados)]
        if livres:
            x = random.choice(livres)
            cor = random.choice(cores)
            quadrados.append([x, -44, cor])
            ultimo_spawn = agora

    for quadrado in quadrados:
        if quadrado is not arrastando:
            quadrado[1] += velocidade

    restantes = []
    for quadrado in quadrados:
        if quadrado is arrastando:
            restantes.append(quadrado)
            continue
        if quadrado[1] > 600:
            continue
        caixa = pygame.Rect(quadrado[0], quadrado[1], 44, 44)
        alvo = None
        maior_contato = 0
        for retangulo, cor_alvo in alvos:
            contato = min(caixa.right, retangulo.right) - max(caixa.left, retangulo.left)
            if caixa.bottom >= retangulo.top and contato > maior_contato:
                alvo = cor_alvo
                maior_contato = contato
        if alvo is None:
            restantes.append(quadrado)
        elif quadrado[2] == alvo:
            pontuacao += 100
        else:
            pontuacao -= 50
    quadrados = restantes

    tela.fill((30, 30, 30))
    for retangulo, cor_alvo in alvos:
        pygame.draw.rect(tela, cor_alvo, retangulo)

    for x, y, cor in quadrados:
        pygame.draw.rect(tela, cor, (x, y, 44, 44))

    texto = fonte.render(str(pontuacao), True, (255, 255, 255))
    tela.blit(texto, (tela.get_width() - texto.get_width() - 20, 20))

    if mao_visivel:
        if mao_fechada:
            pygame.draw.circle(tela, (255, 255, 255), cursor, 15)
        else:
            pygame.draw.circle(tela, (255, 255, 255), cursor, 15, 3)

    print(quadrados)
    
    pygame.display.flip()
    relogio.tick(60)

camera_ativa = False
camera.release()
if reconhecedor:
    reconhecedor.close()
pygame.quit()