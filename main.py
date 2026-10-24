import random

import cv2
import pygame

from config import carregar_config
from pes.controle import ControlePes, mover, quadrado_em
from pes.rastreador import RastreadorPes

# Constantes da interface
TAXA_QUADROS = 60
TITULO_JANELA = "Catalixo"
FONTE_PONTUACAO_TAMANHO = 96
FONTE_AVISO_TAMANHO = 56
MARGEM_UI = 40
RAIO_PE = 30

# Cores da interface e dos alvos
COR_VERDE = (0, 200, 0)
COR_AZUL = (0, 100, 255)
COR_VERMELHA = (220, 0, 0)
COR_AMARELA = (255, 220, 0)
CORES_ALVOS = (COR_VERDE, COR_AZUL, COR_VERMELHA, COR_AMARELA)
COR_FUNDO = (30, 30, 30)
COR_BRANCA = (255, 255, 255)
COR_TEXTO = (200, 200, 200)

# Constantes da área e das regras do jogo

ALVO_ALTURA = 170
ALVO_ESPACAMENTO = 80
TAMANHO_QUADRADO = 88
MARGEM_PEGAR = 50
VELOCIDADE_QUADRADO = 2
FREQUENCIA_SPAWN = 0.4
PONTOS_ACERTO = 100
PENALIDADE_ERRO = 50
TEMPO_JOGO = 90

def criar_alvos(largura, altura):
    """Cria os retângulos-alvo na parte inferior da tela."""
    alvo_largura = (largura - (len(CORES_ALVOS) + 1) * ALVO_ESPACAMENTO) // len(CORES_ALVOS)
    return [
        (
            pygame.Rect(
                ALVO_ESPACAMENTO + indice * (alvo_largura + ALVO_ESPACAMENTO),
                altura - ALVO_ALTURA - ALVO_ESPACAMENTO,
                alvo_largura,
                ALVO_ALTURA,
            ),
            cor,
        )
        for indice, cor in enumerate(CORES_ALVOS)
    ]


def lixeira_tocada(quadrado, alvos):
    """Retorna a cor do alvo com maior contato."""
    caixa = pygame.Rect(
        quadrado[0],
        quadrado[1],
        TAMANHO_QUADRADO,
        TAMANHO_QUADRADO,
    )
    alvo_tocado = None
    maior_contato = 0

    for retangulo, cor_alvo in alvos:
        contato = min(caixa.right, retangulo.right) - max(
            caixa.left, retangulo.left
        )
        if caixa.bottom >= retangulo.top and contato > maior_contato:
            alvo_tocado = cor_alvo
            maior_contato = contato

    return alvo_tocado


def processar_eventos(
    quadrados,
    controle,
    arrastando_mouse,
    largura,
    altura,
    pausado=False,
):
    """Processa eventos de saída e interação com o mouse."""
    rodando = True

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.KEYDOWN and evento.key in (
            pygame.K_ESCAPE,
            pygame.K_q,
        ):
            rodando = False
        elif evento.type == pygame.KEYDOWN and evento.key in (
                    pygame.K_r,
        ):
            pass
        elif pausado:
            continue
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            arrastando_mouse = quadrado_em(
                evento.pos,
                quadrados,
                controle.carregados(),
                TAMANHO_QUADRADO,
                MARGEM_PEGAR,
            )
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            arrastando_mouse = None
        elif (
            evento.type == pygame.MOUSEMOTION
            and arrastando_mouse is not None
        ):
            mover(
                arrastando_mouse,
                evento.pos,
                TAMANHO_QUADRADO,
                largura,
                altura,
            )

    return rodando, arrastando_mouse


def gerar_quadrado(quadrados, colunas, agora, ultimo_spawn):
    """Adiciona um quadrado em uma coluna livre quando chega a hora."""
    intervalo_spawn = 1000 / FREQUENCIA_SPAWN
    if agora - ultimo_spawn < intervalo_spawn:
        return ultimo_spawn

    colunas_livres = [
        coluna
        for coluna in colunas
        if not any(
            abs(quadrado[0] - coluna) < TAMANHO_QUADRADO
            and quadrado[1] < 0
            for quadrado in quadrados
        )
    ]
    if not colunas_livres:
        return ultimo_spawn

    quadrados.append(
        [
            random.choice(colunas_livres),
            -TAMANHO_QUADRADO,
            random.choice(CORES_ALVOS),
        ]
    )
    return agora


def atualizar_quadrados(
    quadrados,
    controle,
    ocupados,
    arrastando_mouse,
    alvos,
    altura,
    pontuacao,
):
    """Move os quadrados, trata colisões e atualiza a pontuação."""
    restantes = []

    for quadrado in quadrados:
        carregado = any(quadrado is item for item in ocupados)
        if not carregado:
            quadrado[1] += VELOCIDADE_QUADRADO
        if quadrado[1] > altura:
            continue

        cor_alvo = lixeira_tocada(quadrado, alvos)
        if cor_alvo is None:
            restantes.append(quadrado)
            continue

        if quadrado[2] == cor_alvo:
            pontuacao += PONTOS_ACERTO
        else:
            pontuacao = max(0, pontuacao - PENALIDADE_ERRO)

        controle.soltar(quadrado)
        if arrastando_mouse is quadrado:
            arrastando_mouse = None

    return restantes, pontuacao, arrastando_mouse

def desenhar_menu_fim(tela, pontuacao, fonte_pontuacao, fonte_aviso, largura, altura):
    """Desenha a tela de fim de jogo com a pontuação final."""
    tela.fill(COR_FUNDO)

    texto_fim = fonte_aviso.render(
        "Fim de jogo!", True, COR_BRANCA
    )
    texto_pontuacao = fonte_pontuacao.render(
        f"Pontuação final: {pontuacao}", True, COR_BRANCA
    )
    aviso_reiniciar = fonte_aviso.render(
        "Pressione R para reiniciar ou Q para sair.", True, COR_TEXTO
    )

    tela.blit(
        texto_fim,
        (
            (largura - texto_fim.get_width()) // 2,
            altura // 3,
        ),
    )
    tela.blit(
        texto_pontuacao,
        (
            (largura - texto_pontuacao.get_width()) // 2,
            altura // 2,
        ),
    )
    tela.blit(
        aviso_reiniciar,
        (
            (largura - aviso_reiniciar.get_width()) // 2,
            altura * 2 // 3,
        ),
    )

    pygame.display.flip()

def desenhar_jogo(
    tela,
    alvos,
    quadrados,
    controle,
    pontuacao,
    tempo,
    fonte_pontuacao,
    fonte_aviso,
    camera_ativa,
    largura
):
    """Desenha o jogo e os indicadores de controle pelos pés."""
    tela.fill(COR_FUNDO)

    for retangulo, cor_alvo in alvos:
        pygame.draw.rect(tela, cor_alvo, retangulo)

    for x, y, cor in quadrados:
        pygame.draw.rect(
            tela,
            cor,
            (int(x), int(y), TAMANHO_QUADRADO, TAMANHO_QUADRADO),
        )

    texto_pontuacao = fonte_pontuacao.render(
        str(pontuacao), True, COR_BRANCA
    )
    texto_tempo = fonte_pontuacao.render(
        tempo, True, COR_BRANCA
    )
    tela.blit(
        texto_pontuacao,
        (
            largura - texto_pontuacao.get_width() - MARGEM_UI,
            MARGEM_UI,
        ),
    )
    tela.blit(
        texto_tempo,
        (
            MARGEM_UI,
            MARGEM_UI
        ),
    )

    for pe in controle.pes:
        if not pe["ativo"]:
            continue

        centro = (int(pe["x"]), int(pe["y"]))
        if pe["carregando"] is not None:
            pygame.draw.circle(tela, COR_BRANCA, centro, RAIO_PE)
        else:
            pygame.draw.circle(tela, COR_BRANCA, centro, RAIO_PE, 4)
            if pe["tempo"] > 0:
                fim = (
                    2
                    * 3.14159
                    * min(pe["tempo"] / controle.tempo_pegar, 1)
                )
                caixa = pygame.Rect(0, 0, RAIO_PE * 3, RAIO_PE * 3)
                caixa.center = centro
                pygame.draw.arc(tela, COR_AMARELA, caixa, 0, fim, 6)

    if not camera_ativa:
        aviso = fonte_aviso.render(
            "Câmera não encontrada: use o mouse", True, COR_TEXTO
        )
        tela.blit(aviso, (20, 20))

    pygame.display.flip()


def atualizar_janela_camera(rastreador):
    """Exibe o frame mais recente da câmera, se estiver disponível."""
    captura = rastreador.pegar_frame()
    if captura is not None:
        cv2.imshow("webcam", captura)
        cv2.waitKey(1)


def executar_jogo(tela, rastreador, controle, camera_ativa):
    """Executa o loop principal do jogo."""
    largura, altura = tela.get_size()
    alvos = criar_alvos(largura, altura)
    colunas = [retangulo.centerx - TAMANHO_QUADRADO // 2 for retangulo, _ in alvos]
    relogio = pygame.time.Clock()
    horario_inicio = pygame.time.get_ticks() / 1000
    fonte_pontuacao = pygame.font.Font(None, FONTE_PONTUACAO_TAMANHO)
    fonte_aviso = pygame.font.Font(None, FONTE_AVISO_TAMANHO)

    pontuacao = 0
    ultimo_spawn = 0
    quadrados = []
    arrastando_mouse = None
    rodando = True
    esta_pausado = False

    while rodando:
        dt = relogio.tick(TAXA_QUADROS) / 1000
        horario_atual = pygame.time.get_ticks() / 1000
        segundo_passados = min(
            horario_atual - horario_inicio,
            TEMPO_JOGO,
        )

        if segundo_passados >= TEMPO_JOGO:
            esta_pausado = True

        minutos, segundos = divmod(segundo_passados, 60)
        tempo = f"{int(minutos):02d}:{int(segundos):02d}"

        rodando, arrastando_mouse = processar_eventos(
            quadrados,
            controle,
            arrastando_mouse,
            largura,
            altura,
            esta_pausado,
        )

        if esta_pausado:
            desenhar_menu_fim(
                tela,
                pontuacao,
                fonte_pontuacao,
                fonte_aviso,
                largura,
                altura
            )
        else:
            outros = (
                [arrastando_mouse] if arrastando_mouse is not None else []
            )
            controle.atualizar(
                rastreador.pes_na_tela(),
                dt,
                quadrados,
                outros,
            )

            agora = pygame.time.get_ticks()
            ultimo_spawn = gerar_quadrado(quadrados, colunas, agora, ultimo_spawn)

            ocupados = controle.carregados() + outros
            quadrados, pontuacao, arrastando_mouse = atualizar_quadrados(
                quadrados,
                controle,
                ocupados,
                arrastando_mouse,
                alvos,
                altura,
                pontuacao,
            )

            desenhar_jogo(
                tela,
                alvos,
                quadrados,
                controle,
                pontuacao,
                tempo,
                fonte_pontuacao,
                fonte_aviso,
                camera_ativa,
                largura,
            )
        atualizar_janela_camera(rastreador)


def main():
    """Inicializa os recursos e inicia o jogo."""
    config = carregar_config()
    pygame.init()
    rastreador = None

    try:
        tela = pygame.display.set_mode(
            (config["screen_width"], config["screen_height"]),
            pygame.FULLSCREEN,
            display=config["screen_position"],
        )
        pygame.display.set_caption(TITULO_JANELA)
        largura, altura = tela.get_size()

        rastreador = RastreadorPes(config, largura, altura)
        camera_ativa = rastreador.iniciar()
        controle = ControlePes(
            TAMANHO_QUADRADO,
            MARGEM_PEGAR,
            largura,
            altura,
        )

        executar_jogo(tela, rastreador, controle, camera_ativa)
    finally:
        if rastreador is not None:
            rastreador.parar()
        cv2.destroyAllWindows()
        pygame.quit()


if __name__ == "__main__":
    main()
