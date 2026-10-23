import random
import cv2
import pygame
from config import carregar_config
from pes.controle import ControlePes, mover, quadrado_em
from pes.rastreador import RastreadorPes

# puxa as config do ttea
config = carregar_config()

# config basica pygame janela
pygame.init()
tela = pygame.display.set_mode((800, 600), display=config["screen_position"])
pygame.display.set_caption("Game Jam")
relogio = pygame.time.Clock()
L, A = tela.get_size()

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
residuo = 44

pontuacao = 0
fonte = pygame.font.Font(None, 48)
fonte_aviso = pygame.font.Font(None, 28)

velocidade = 1
frequencia_spawn = 0.4
ultimo_spawn = 0
quadrados = []

margem_pegar = 25

# detecção dos pés
rastreador = RastreadorPes(config, L, A)
camera_ativa = rastreador.iniciar()
controle = ControlePes(residuo, margem_pegar, L, A)
arrastando_mouse = None


def lixeira_tocada(quadrado):
    caixa = pygame.Rect(quadrado[0], quadrado[1], residuo, residuo)
    alvo = None
    maior_contato = 0
    for retangulo, cor_alvo in alvos:
        contato = min(caixa.right, retangulo.right) - max(caixa.left, retangulo.left)
        if caixa.bottom >= retangulo.top and contato > maior_contato:
            alvo = cor_alvo
            maior_contato = contato
    return alvo


rodando = True
while rodando:
    dt = relogio.tick(60) / 1000
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_q):
            rodando = False
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            arrastando_mouse = quadrado_em(evento.pos, quadrados, controle.carregados(), residuo, margem_pegar)
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            arrastando_mouse = None
        elif evento.type == pygame.MOUSEMOTION and arrastando_mouse is not None:
            mover(arrastando_mouse, evento.pos, residuo, L, A)

    outros = [arrastando_mouse] if arrastando_mouse is not None else []
    controle.atualizar(rastreador.pes_na_tela(), dt, quadrados, outros)

    agora = pygame.time.get_ticks()
    if agora - ultimo_spawn >= 1000 / frequencia_spawn:
        livres = [c for c in colunas if not any(abs(q[0] - c) < residuo and q[1] < 0 for q in quadrados)]
        if livres:
            x = random.choice(livres)
            cor = random.choice(cores)
            quadrados.append([x, -residuo, cor])
            ultimo_spawn = agora

    ocupados = controle.carregados() + outros
    restantes = []
    for quadrado in quadrados:
        carregado = any(quadrado is c for c in ocupados)
        if not carregado:
            quadrado[1] += velocidade
        if quadrado[1] > A:
            continue
        alvo = lixeira_tocada(quadrado)
        if alvo is None:
            restantes.append(quadrado)
            continue
        if quadrado[2] == alvo:
            pontuacao += 100
        else:
            pontuacao -= 50
        controle.soltar(quadrado)
        if arrastando_mouse is quadrado:
            arrastando_mouse = None
    quadrados = restantes

    tela.fill((30, 30, 30))
    for retangulo, cor_alvo in alvos:
        pygame.draw.rect(tela, cor_alvo, retangulo)

    for x, y, cor in quadrados:
        pygame.draw.rect(tela, cor, (int(x), int(y), residuo, residuo))

    texto = fonte.render(str(pontuacao), True, (255, 255, 255))
    tela.blit(texto, (L - texto.get_width() - 20, 20))

    raio = 15
    for pe in controle.pes:
        if not pe["ativo"]:
            continue
        centro = (int(pe["x"]), int(pe["y"]))
        if pe["carregando"] is not None:
            pygame.draw.circle(tela, (255, 255, 255), centro, raio)
        else:
            pygame.draw.circle(tela, (255, 255, 255), centro, raio, 4)
            if pe["tempo"] > 0:
                fim = 2 * 3.14159 * min(pe["tempo"] / controle.tempo_pegar, 1)
                caixa = pygame.Rect(0, 0, raio * 3, raio * 3)
                caixa.center = centro
                pygame.draw.arc(tela, amarelo, caixa, 0, fim, 6)

    if not camera_ativa:
        aviso = fonte_aviso.render("Câmera não encontrada: use o mouse", True, (200, 200, 200))
        tela.blit(aviso, (20, 20))

    pygame.display.flip()

    # mostra a camera em uma janela separada
    captura = rastreador.pegar_frame()
    if captura is not None:
        cv2.imshow("webcam", captura)
        cv2.waitKey(1)

rastreador.parar()
cv2.destroyAllWindows()
pygame.quit()
