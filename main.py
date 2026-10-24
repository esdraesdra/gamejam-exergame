import random
from pathlib import Path

import cv2
import pygame

from config import carregar_config
from pes.controle import ControlePes, mover, quadrado_em
from pes.rastreador import RastreadorPes

# Constantes da interface
TAXA_QUADROS = 60
TITULO_JANELA = "Catalixo"
FONTE_PONTUACAO_TAMANHO_BASE = 32
FONTE_AVISO_TAMANHO_BASE = 19
MARGEM_UI_BASE = 13
RAIO_PE_BASE = 10
FONTE_HUD_TAMANHO_BASE = 24
GRADE_FONTE_HUD = 8
MARGEM_INTERNA_UI_BASE = 4
OPACIDADE_FUNDO_UI = 102
LARGURA_BASE = 640
ALTURA_BASE = 400
CAMINHO_FONTE_HUD = Path(__file__).resolve().parent / "assets" / "fonts" / "PressStart2P-Regular.ttf"

# Cores da interface e dos alvos
COR_VERDE = (0, 200, 0)
COR_AZUL = (0, 100, 255)
COR_VERMELHA = (220, 0, 0)
COR_AMARELA = (255, 220, 0)
CORES_ALVOS = (COR_AZUL, COR_VERMELHA, COR_AMARELA, COR_VERDE)
TIPO_ITEM_POR_COR = {
    COR_VERDE: "vidro",
    COR_AMARELA: "metal",
    COR_AZUL: "papel",
    COR_VERMELHA: "plastico",
}
COR_FUNDO = (30, 30, 30)
COR_BRANCA = (255, 255, 255)
COR_TEXTO = (200, 200, 200)
COR_CINZA = (128, 128, 128)
COR_PRETA = (0, 0, 0)

# Constantes da área e das regras do jogo

TAMANHO_ITEM_SPRITE = 64
MARGEM_PEGAR_BASE = 17
VELOCIDADE_QUADRADO_BASE = 2 / 3
FREQUENCIA_SPAWN = 0.4
PONTOS_ACERTO = 100
PENALIDADE_ERRO = 50
TEMPO_JOGO = 90
TEMPO_BOTAO_PE = 3
QUANTIDADE_LIXEIRAS = 4
ESPACAMENTO_SPRITE = 32
LARGURA_LIXEIRA_SPRITE = 192
ALTURA_LIXEIRA_SPRITE = 160
TOPO_HITBOX_LIXEIRA_SPRITE = 75
FONTE_PONTUACAO_TAMANHO = None
FONTE_AVISO_TAMANHO = None
MARGEM_UI = None
FONTE_HUD_TAMANHO = None
MARGEM_INTERNA_UI = None
RAIO_PE = None
MARGEM_PEGAR = None
VELOCIDADE_QUADRADO = None
TAMANHO_ITEM = None
ESPACAMENTO = None
LARGURA_LIXEIRA = None
ALTURA_LIXEIRA = None
ALTURA_HITBOX_LIXEIRA = None
SPRITES_ITENS = {}
SPRITES_LIXEIRAS = {}
IMAGEM_FUNDO = None
SPRITES_CAMINHOES = {}

# multiplicador de pontos

multiplicadorAcertos = 3
multiplicadorMax = 5
multiplicadorEspacamentoBase = 10
multiplicadorEspacamento = None

def configurar_escala(largura, altura):
    global TAMANHO_ITEM, ESPACAMENTO, LARGURA_LIXEIRA, ALTURA_LIXEIRA, ALTURA_HITBOX_LIXEIRA
    global FONTE_PONTUACAO_TAMANHO, FONTE_AVISO_TAMANHO, MARGEM_UI, RAIO_PE
    global MARGEM_PEGAR, VELOCIDADE_QUADRADO, multiplicadorEspacamento
    global FONTE_HUD_TAMANHO, MARGEM_INTERNA_UI

    escala = min(largura / LARGURA_BASE, altura / ALTURA_BASE)
    escala_lixeira = min(
        escala,
        largura / (
            QUANTIDADE_LIXEIRAS * LARGURA_LIXEIRA_SPRITE
            + (QUANTIDADE_LIXEIRAS + 1) * ESPACAMENTO_SPRITE
        ),
    )

    FONTE_PONTUACAO_TAMANHO = round(FONTE_PONTUACAO_TAMANHO_BASE * escala)
    FONTE_AVISO_TAMANHO = round(FONTE_AVISO_TAMANHO_BASE * escala)
    MARGEM_UI = round(MARGEM_UI_BASE * escala)
    FONTE_HUD_TAMANHO = round(FONTE_HUD_TAMANHO_BASE * escala / GRADE_FONTE_HUD) * GRADE_FONTE_HUD
    MARGEM_INTERNA_UI = round(MARGEM_INTERNA_UI_BASE * escala)
    RAIO_PE = round(RAIO_PE_BASE * escala)
    MARGEM_PEGAR = round(MARGEM_PEGAR_BASE * escala)
    VELOCIDADE_QUADRADO = VELOCIDADE_QUADRADO_BASE * escala
    multiplicadorEspacamento = round(multiplicadorEspacamentoBase * escala)

    TAMANHO_ITEM = round(TAMANHO_ITEM_SPRITE * escala)
    ESPACAMENTO = round(ESPACAMENTO_SPRITE * escala_lixeira)
    LARGURA_LIXEIRA = round(LARGURA_LIXEIRA_SPRITE * escala_lixeira)
    ALTURA_LIXEIRA = round(ALTURA_LIXEIRA_SPRITE * escala_lixeira)
    ALTURA_HITBOX_LIXEIRA = ALTURA_LIXEIRA - round(TOPO_HITBOX_LIXEIRA_SPRITE * escala_lixeira)

def criar_alvos(largura, altura):
    """Cria hitboxes um pouco mais baixas que os sprites das lixeiras."""
    posicoes = separar_itens_horizontalmente(
        QUANTIDADE_LIXEIRAS,
        LARGURA_LIXEIRA,
        ALTURA_LIXEIRA,
        ESPACAMENTO,
        largura,
        altura,
    )
    return [
        (
            pygame.Rect(
                x,
                y + ALTURA_LIXEIRA - ALTURA_HITBOX_LIXEIRA,
                LARGURA_LIXEIRA,
                ALTURA_HITBOX_LIXEIRA,
            ),
            cor,
        )
        for (x, y), cor in zip(posicoes, CORES_ALVOS)
    ]


def lixeira_tocada(quadrado, alvos):
    """Retorna a cor do alvo com maior contato."""
    caixa = pygame.Rect(
        quadrado[0],
        quadrado[1],
        TAMANHO_ITEM,
        TAMANHO_ITEM,
    )
    alvo_tocado = None
    maior_contato = 0

    for retangulo, cor_alvo in alvos:
        contato = min(caixa.right, retangulo.right) - max(
            caixa.left, retangulo.left
        )
        if caixa.colliderect(retangulo) and contato > maior_contato:
            alvo_tocado = cor_alvo
            maior_contato = contato

    return alvo_tocado


def processar_eventos(
    lixos,
    controle,
    arrastando_mouse,
    largura,
    altura,
    pausado=False,
):
    """Processa eventos de saída e interação com o mouse."""
    rodando = True
    reiniciar = False

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
            reiniciar = True
        elif pausado:
            continue
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            arrastando_mouse = quadrado_em(
                evento.pos,
                lixos,
                controle.carregados(),
                TAMANHO_ITEM,
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
                TAMANHO_ITEM,
                largura,
                altura,
            )

    return rodando, arrastando_mouse, reiniciar


def gerar_quadrado(lixos, colunas, agora, ultimo_spawn):
    """Gera um item reciclável aleatório em uma coluna livre."""
    intervalo_spawn = 1000 / FREQUENCIA_SPAWN
    if agora - ultimo_spawn < intervalo_spawn:
        return ultimo_spawn

    colunas_livres = [
        coluna
        for coluna in colunas
        if not any(
            abs(quadrado[0] - coluna) < TAMANHO_ITEM
            and quadrado[1] < 0
            for quadrado in lixos
        )
    ]
    if not colunas_livres:
        return ultimo_spawn

    cor = random.choice(CORES_ALVOS)
    tipo = TIPO_ITEM_POR_COR[cor]
    numero_sprite = random.randint(1, 2)
    caminho_sprite = f"./assets/{tipo}-{numero_sprite}.png"
    if caminho_sprite not in SPRITES_ITENS:
        imagem = pygame.image.load(caminho_sprite).convert_alpha()
        SPRITES_ITENS[caminho_sprite] = pygame.transform.scale(
            imagem, (TAMANHO_ITEM, TAMANHO_ITEM)
        )

    lixos.append([
        random.choice(colunas_livres),
        -TAMANHO_ITEM,
        cor,
        SPRITES_ITENS[caminho_sprite],
    ])
    return agora


def atualizar_lixos(
    lixos,
    controle,
    ocupados,
    arrastando_mouse,
    alvos,
    altura,
    pontuacao,
    multiplicador,
    acertos
):
    """Move os lixos, trata colisões e atualiza a pontuação."""
    restantes = []

    for quadrado in lixos:
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
            pontuacao += PONTOS_ACERTO * multiplicador
            acertos+=1
            if acertos == multiplicadorAcertos:
                multiplicador = min(multiplicador + 1, multiplicadorMax)
                acertos = 0

        else:
            pontuacao = max(0, pontuacao - PENALIDADE_ERRO)
            multiplicador = 1
            acertos = 0

        controle.soltar(quadrado)
        if arrastando_mouse is quadrado:
            arrastando_mouse = None

    return restantes, pontuacao, arrastando_mouse, multiplicador, acertos

def separar_itens_horizontalmente(
    quantidade,
    largura,
    altura,
    espacamento,
    largura_tela,
    altura_tela,
):
    """Centraliza itens horizontalmente e os alinha à base da tela."""
    largura_total = (quantidade * largura + (quantidade - 1 ) * espacamento)
    margem_esquerda = (largura_tela - largura_total) // 2

    itens = []

    for i in range(quantidade):
        x = margem_esquerda + i * (
            largura + espacamento
        )

        y = altura_tela - altura

        itens.append((x, y))

    return itens

def desenhar_lixeiras(tela):
    """Desenha as lixeiras na parte inferior da tela"""
    largura_tela, altura_tela = tela.get_size()
    posicoes = separar_itens_horizontalmente(
        QUANTIDADE_LIXEIRAS,
        LARGURA_LIXEIRA,
        ALTURA_LIXEIRA,
        ESPACAMENTO,
        largura_tela,
        altura_tela,
    )

    for indice, pos in enumerate(posicoes):
        num_sprite = indice + 1
        chave = (num_sprite, LARGURA_LIXEIRA, ALTURA_LIXEIRA)
        if chave not in SPRITES_LIXEIRAS:
            caminho = (
                Path(__file__).resolve().parent
                / "assets"
                / f"lixeira-{num_sprite}.png"
            )
            imagem = pygame.image.load(str(caminho)).convert_alpha()
            SPRITES_LIXEIRAS[chave] = pygame.transform.scale(
                imagem, (LARGURA_LIXEIRA, ALTURA_LIXEIRA)
            )

        tela.blit(SPRITES_LIXEIRAS[chave], pos)


def desenhar_fundo(tela):
    """Desenha o fundo do jogo, carregando e escalando a imagem sob demanda."""
    global IMAGEM_FUNDO

    tamanho_tela = tela.get_size()
    if IMAGEM_FUNDO is None or IMAGEM_FUNDO.get_size() != tamanho_tela:
        caminho = Path(__file__).resolve().parent / "assets" / "background.png"
        imagem = pygame.image.load(str(caminho)).convert()
        IMAGEM_FUNDO = pygame.transform.scale(imagem, tamanho_tela)

    tela.blit(IMAGEM_FUNDO, (0, 0))


def desenhar_caminhao(tela, numero):
    """Desenha um caminhão no topo, escalado à largura da tela."""
    tamanho_tela = tela.get_size()
    chave = (numero, tamanho_tela)
    if chave not in SPRITES_CAMINHOES:
        caminho = (
            Path(__file__).resolve().parent
            / "assets"
            / f"caminhao-{numero}.png"
        )
        imagem = pygame.image.load(str(caminho)).convert_alpha()
        altura = round(imagem.get_height() * tamanho_tela[0] / imagem.get_width())
        SPRITES_CAMINHOES[chave] = pygame.transform.scale(
            imagem, (tamanho_tela[0], altura)
        )

    tela.blit(SPRITES_CAMINHOES[chave], (0, 0))


def desenhar_fundo_texto(tela, retangulo):
    fundo = pygame.Surface(retangulo.size, pygame.SRCALPHA)
    fundo.fill((*COR_PRETA, OPACIDADE_FUNDO_UI))
    tela.blit(fundo, retangulo.topleft)


def renderizar_texto_3d(fonte, texto, cor):
    return fonte.render(texto, False, cor), fonte.render(texto, False, COR_PRETA)


def desenhar_jogo(
    tela,
    lixos,
    controle,
    pontuacao,
    multiplicador,
    tempo,
    fonte_hud,
    largura
):
    """Desenha o jogo e os indicadores de controle pelos pés."""
    desenhar_fundo(tela)
    desenhar_caminhao(tela, 1)

    desenhar_lixeiras(tela)

    for x, y, _, sprite in lixos:
        tela.blit(sprite, (int(x), int(y)))

    desenhar_caminhao(tela, 2)

    texto_pontuacao, sombra_pontuacao = renderizar_texto_3d(
        fonte_hud, str(pontuacao), COR_BRANCA
    )
    texto_tempo, sombra_tempo = renderizar_texto_3d(
        fonte_hud, tempo, COR_BRANCA
    )
    texto_multiplicador, sombra_multiplicador = renderizar_texto_3d(
        fonte_hud, f"x{multiplicador}", COR_AMARELA
    )
    x_multiplicador = largura - texto_multiplicador.get_width() - MARGEM_UI
    caixa_multiplicador = texto_multiplicador.get_rect(
        topleft=(x_multiplicador, MARGEM_UI)
    )
    caixa_pontuacao = texto_pontuacao.get_rect(
        topright=(x_multiplicador - multiplicadorEspacamento, MARGEM_UI)
    )
    caixa_tempo = texto_tempo.get_rect(topleft=(MARGEM_UI, MARGEM_UI))

    for fundo in (caixa_tempo, caixa_pontuacao.union(caixa_multiplicador)):
        desenhar_fundo_texto(
            tela,
            fundo.inflate(2 * MARGEM_INTERNA_UI, 2 * MARGEM_INTERNA_UI),
        )

    pixel_fonte = FONTE_HUD_TAMANHO // GRADE_FONTE_HUD
    textos = (
        (texto_multiplicador, sombra_multiplicador, caixa_multiplicador),
        (texto_pontuacao, sombra_pontuacao, caixa_pontuacao),
        (texto_tempo, sombra_tempo, caixa_tempo),
    )
    for _, sombra, caixa in textos:
        tela.blit(sombra, caixa.move(pixel_fonte, pixel_fonte))
    for texto, _, caixa in textos:
        tela.blit(texto, caixa)

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

    pygame.display.flip()


def atualizar_janela_camera(rastreador):
    """Exibe o frame mais recente da câmera, se estiver disponível."""
    captura = rastreador.pegar_frame()
    if captura is not None:
        cv2.imshow("webcam", captura)
        cv2.waitKey(1)

def reiniciar_jogo():
    pontuacao = 0
    multiplicador = 1
    acertos = 0
    lixos = []
    ultimo_spawn = 0
    horario_inicio = pygame.time.get_ticks() / 1000
    arrastando_mouse = None
    esta_pausado = False

    return (
        pontuacao,
        multiplicador,
        acertos,
        lixos,
        ultimo_spawn,
        horario_inicio,
        arrastando_mouse,
        esta_pausado,
    )

def criar_botoes(largura, altura, rotulo_principal, centro_y):
    botao_largura = largura // 3
    botao_altura = altura // 5
    espacamento = largura // 12
    esquerda = (largura - 2 * botao_largura - espacamento) // 2
    topo = centro_y - botao_altura // 2
    return [
        (pygame.Rect(esquerda, topo, botao_largura, botao_altura), rotulo_principal, True),
        (
            pygame.Rect(esquerda + botao_largura + espacamento, topo, botao_largura, botao_altura),
            "Sair",
            False,
        ),
    ]

def desenhar_menu(tela, botoes, progresso, controle, fonte, textos):
    tela.fill(COR_FUNDO)

    for imagem, posicao in textos:
        tela.blit(imagem, posicao)

    for retangulo, texto, _ in botoes:
        pygame.draw.rect(tela, COR_CINZA, retangulo)
        rotulo = fonte.render(texto, True, COR_BRANCA)
        tela.blit(rotulo, rotulo.get_rect(center=retangulo.center))

    for pe in controle.pes:
        if not pe["ativo"]:
            continue

        centro = (int(pe["x"]), int(pe["y"]))
        pygame.draw.circle(tela, COR_BRANCA, centro, RAIO_PE, 4)
        for (retangulo, _, _), tempo in zip(botoes, progresso):
            if tempo > 0 and retangulo.collidepoint(centro):
                fim = 2 * 3.14159 * min(tempo / TEMPO_BOTAO_PE, 1)
                caixa = pygame.Rect(0, 0, RAIO_PE * 3, RAIO_PE * 3)
                caixa.center = centro
                pygame.draw.arc(tela, COR_AMARELA, caixa, 0, fim, 6)

    pygame.display.flip()

def executar_menu(tela, rastreador, controle, botoes, textos):
    fonte = pygame.font.Font(None, FONTE_PONTUACAO_TAMANHO)
    relogio = pygame.time.Clock()
    progresso = [0.0 for _ in botoes]

    while True:
        dt = relogio.tick(TAXA_QUADROS) / 1000

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            if evento.type == pygame.KEYDOWN and evento.key in (
                pygame.K_ESCAPE,
                pygame.K_q,
            ):
                return False
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_r:
                return True
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for retangulo, _, acao in botoes:
                    if retangulo.collidepoint(evento.pos):
                        return acao

        controle.atualizar(rastreador.pes_na_tela(), dt, [])

        for indice, (retangulo, _, acao) in enumerate(botoes):
            pisado = any(
                pe["ativo"] and retangulo.collidepoint(pe["x"], pe["y"])
                for pe in controle.pes
            )
            progresso[indice] = progresso[indice] + dt if pisado else 0.0
            if progresso[indice] >= TEMPO_BOTAO_PE:
                return acao

        desenhar_menu(tela, botoes, progresso, controle, fonte, textos)
        atualizar_janela_camera(rastreador)

def executar_tela_inicial(tela, rastreador, controle):
    largura, altura = tela.get_size()
    botoes = criar_botoes(largura, altura, "Novo Jogo", altura // 2)
    return executar_menu(tela, rastreador, controle, botoes, [])

def executar_menu_fim(tela, rastreador, controle, pontuacao, fonte_pontuacao, fonte_aviso):
    largura, altura = tela.get_size()
    texto_fim = fonte_aviso.render("Fim de jogo!", True, COR_BRANCA)
    texto_pontuacao = fonte_pontuacao.render(
        f"Pontuação final: {pontuacao}", True, COR_BRANCA
    )
    textos = [
        (texto_fim, ((largura - texto_fim.get_width()) // 2, altura // 3)),
        (
            texto_pontuacao,
            ((largura - texto_pontuacao.get_width()) // 2, altura // 2),
        ),
    ]
    botoes = criar_botoes(largura, altura, "Recomeçar", altura * 3 // 4)
    return executar_menu(tela, rastreador, controle, botoes, textos)

def executar_jogo(tela, rastreador, controle):
    """Executa o loop principal do jogo."""
    largura, altura = tela.get_size()
    alvos = criar_alvos(largura, altura)
    colunas = [retangulo.centerx - TAMANHO_ITEM // 2 for retangulo, _ in alvos]
    relogio = pygame.time.Clock()
    horario_inicio = pygame.time.get_ticks() / 1000
    fonte_pontuacao = pygame.font.Font(None, FONTE_PONTUACAO_TAMANHO)
    fonte_aviso = pygame.font.Font(None, FONTE_AVISO_TAMANHO)
    fonte_hud = pygame.font.Font(str(CAMINHO_FONTE_HUD), FONTE_HUD_TAMANHO)
    rodando = True

    pontuacao, multiplicador, acertos, lixos, ultimo_spawn, horario_inicio, arrastando_mouse, esta_pausado = reiniciar_jogo()

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

        rodando, arrastando_mouse, reiniciar = processar_eventos(
            lixos,
            controle,
            arrastando_mouse,
            largura,
            altura,
            esta_pausado,
        )

        if reiniciar:
            pontuacao, multiplicador, acertos, lixos, ultimo_spawn, horario_inicio, arrastando_mouse, esta_pausado = reiniciar_jogo()

        if esta_pausado:
            for quadrado in controle.carregados():
                controle.soltar(quadrado)
            if executar_menu_fim(tela, rastreador, controle, pontuacao, fonte_pontuacao, fonte_aviso):
                pontuacao, multiplicador, acertos, lixos, ultimo_spawn, horario_inicio, arrastando_mouse, esta_pausado = reiniciar_jogo()
            else:
                rodando = False
        else:
            outros = (
                [arrastando_mouse] if arrastando_mouse is not None else []
            )
            controle.atualizar(
                rastreador.pes_na_tela(),
                dt,
                lixos,
                outros,
            )

            agora = pygame.time.get_ticks()
            ultimo_spawn = gerar_quadrado(lixos, colunas, agora, ultimo_spawn)

            ocupados = controle.carregados() + outros
            lixos, pontuacao, arrastando_mouse, multiplicador, acertos = atualizar_lixos(
                lixos,
                controle,
                ocupados,
                arrastando_mouse,
                alvos,
                altura,
                pontuacao,
                multiplicador,
                acertos
            )

            desenhar_jogo(
                tela,
                lixos,
                controle,
                pontuacao,
                multiplicador,
                tempo,
                fonte_hud,
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
        configurar_escala(largura, altura)

        rastreador = RastreadorPes(config, largura, altura)
        rastreador.iniciar()
        controle = ControlePes(
            TAMANHO_ITEM,
            MARGEM_PEGAR,
            largura,
            altura,
        )

        if executar_tela_inicial(tela, rastreador, controle):
            executar_jogo(tela, rastreador, controle)
    finally:
        if rastreador is not None:
            rastreador.parar()
        cv2.destroyAllWindows()
        pygame.quit()


if __name__ == "__main__":
    main()
