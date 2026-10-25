import json
import math
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
MARGEM_UI_BASE = 13
RAIO_PE_BASE = 10
FONTE_HUD_TAMANHO_BASE = 18
FONTE_TITULO_TAMANHO_BASE = 24
FONTE_FIM_TAMANHO_BASE = 16
FONTE_MENSAGEM_TAMANHO_BASE = 11
GRADE_FONTE_HUD = 8
MARGEM_INTERNA_UI_BASE = 4
OPACIDADE_FUNDO_UI = 102
AMPLITUDE_PENDULO = 10
AMPLITUDE_PENDULO_TITULO = 3
AMPLITUDE_PENDULO_LOGO = 6
PERIODO_PENDULO = 1.2
LARGURA_BASE = 640
ALTURA_BASE = 400
CAMINHO_FONTE_HUD = Path(__file__).resolve().parent / "assets" / "fonts" / "PressStart2P-Regular.ttf"
CAMINHO_MENSAGENS = Path(__file__).resolve().parent / "assets" / "mensagens.json"
CAMINHO_FUNDO_MENU = Path(__file__).resolve().parent / "assets" / "background-menu.png"
CAMINHO_ICONE_TEMPO = Path(__file__).resolve().parent / "assets" / "timer.png"
CAMINHO_SPRITE_BOTAO_VERDE = Path(__file__).resolve().parent / "assets" / "box-button-green.png"
CAMINHO_SPRITE_BOTAO_VERMELHO = Path(__file__).resolve().parent / "assets" / "box-button-red.png"
CAMINHO_LOGO_MUNDO = Path(__file__).resolve().parent / "assets" / "logo-world.png"
CAMINHO_LOGO_TEXTO = Path(__file__).resolve().parent / "assets" / "logo-text.png"
CAMINHO_SOM_ACERTO = Path(__file__).resolve().parent / "assets" / "pontos.wav"
CAMINHO_SOM_ERRO = Path(__file__).resolve().parent / "assets" / "perde-pontos.wav"

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
COR_PRETA = (0, 0, 0)
LINHAS_CREDITOS = (
    (("Feito em 10 dias por", COR_BRANCA),),
    (("Esdras Gabriel Alves e Gustavo de Paula Gorges", COR_VERMELHA),),
    (("para a ", COR_BRANCA), ("3ª ExerGame Jam", COR_VERDE)),
)
SPRITE_BOTAO_POR_COR = {
    COR_VERDE: CAMINHO_SPRITE_BOTAO_VERDE,
    COR_VERMELHA: CAMINHO_SPRITE_BOTAO_VERMELHO,
}

# Constantes da área e das regras do jogo

TAMANHO_ITEM_SPRITE = 64
MARGEM_PEGAR_BASE = 17
VELOCIDADE_QUADRADO_BASE = 2 / 3
AUMENTO_VELOCIDADE_BASE = 1 / 6
VELOCIDADE_FUNDO_MENU_BASE = 10
MOSTRAR_FUNDO_MENU = False
USAR_SPRITE_BOTAO = True
CORTE_SPRITE_BOTAO = 16
AMPLIACAO_EXTRA_FUNDO_MENU = 1
FREQUENCIA_SPAWN = 0.4
PONTOS_ACERTO = 100
PENALIDADE_ERRO = 50
TEMPO_JOGO = 90
INTERVALO_DIFICULDADE = 30
TEMPO_BOTAO_PE = 3
QUANTIDADE_LIXEIRAS = 4
ESPACAMENTO_SPRITE = 32
LARGURA_LIXEIRA_SPRITE = 192
ALTURA_LIXEIRA_SPRITE = 160
TOPO_HITBOX_LIXEIRA_SPRITE = 75
MARGEM_UI = None
FONTE_HUD_TAMANHO = None
FONTE_TITULO_TAMANHO = None
FONTE_FIM_TAMANHO = None
FONTE_MENSAGEM_TAMANHO = None
MARGEM_INTERNA_UI = None
RAIO_PE = None
MARGEM_PEGAR = None
VELOCIDADE_QUADRADO = None
AUMENTO_VELOCIDADE = None
ESCALA_TELA = None
VELOCIDADE_FUNDO_MENU = None
TAMANHO_ITEM = None
ESPACAMENTO = None
LARGURA_LIXEIRA = None
ALTURA_LIXEIRA = None
ALTURA_HITBOX_LIXEIRA = None
SPRITES_ITENS = {}
SPRITES_LIXEIRAS = {}
IMAGEM_FUNDO = None
SPRITES_CAMINHOES = {}
SPRITES_ICONES = {}
SPRITES_BOTOES = {}
SONS = {}

# multiplicador de pontos

multiplicadorAcertos = 3
multiplicadorMax = 5
multiplicadorEspacamentoBase = 10
multiplicadorEspacamento = None

def tamanho_fonte_pixel(base, escala):
    return round(base * escala / GRADE_FONTE_HUD) * GRADE_FONTE_HUD

def configurar_escala(largura, altura):
    global TAMANHO_ITEM, ESPACAMENTO, LARGURA_LIXEIRA, ALTURA_LIXEIRA, ALTURA_HITBOX_LIXEIRA
    global MARGEM_UI, RAIO_PE
    global MARGEM_PEGAR, VELOCIDADE_QUADRADO, AUMENTO_VELOCIDADE, multiplicadorEspacamento
    global FONTE_HUD_TAMANHO, FONTE_TITULO_TAMANHO, FONTE_FIM_TAMANHO, FONTE_MENSAGEM_TAMANHO, MARGEM_INTERNA_UI
    global ESCALA_TELA, VELOCIDADE_FUNDO_MENU

    escala = min(largura / LARGURA_BASE, altura / ALTURA_BASE)
    ESCALA_TELA = escala
    escala_lixeira = min(
        escala,
        largura / (
            QUANTIDADE_LIXEIRAS * LARGURA_LIXEIRA_SPRITE
            + (QUANTIDADE_LIXEIRAS + 1) * ESPACAMENTO_SPRITE
        ),
    )

    MARGEM_UI = round(MARGEM_UI_BASE * escala)
    FONTE_HUD_TAMANHO = tamanho_fonte_pixel(FONTE_HUD_TAMANHO_BASE, escala)
    FONTE_TITULO_TAMANHO = tamanho_fonte_pixel(FONTE_TITULO_TAMANHO_BASE, escala)
    FONTE_FIM_TAMANHO = tamanho_fonte_pixel(FONTE_FIM_TAMANHO_BASE, escala)
    FONTE_MENSAGEM_TAMANHO = tamanho_fonte_pixel(FONTE_MENSAGEM_TAMANHO_BASE, escala)
    MARGEM_INTERNA_UI = round(MARGEM_INTERNA_UI_BASE * escala)
    RAIO_PE = round(RAIO_PE_BASE * escala)
    MARGEM_PEGAR = round(MARGEM_PEGAR_BASE * escala)
    VELOCIDADE_QUADRADO = VELOCIDADE_QUADRADO_BASE * escala
    AUMENTO_VELOCIDADE = AUMENTO_VELOCIDADE_BASE * escala
    multiplicadorEspacamento = round(multiplicadorEspacamentoBase * escala)
    VELOCIDADE_FUNDO_MENU = VELOCIDADE_FUNDO_MENU_BASE * escala

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
    acertos,
    velocidade,
):
    """Move os lixos, trata colisões e atualiza a pontuação."""
    restantes = []

    for quadrado in lixos:
        carregado = any(quadrado is item for item in ocupados)
        if not carregado:
            quadrado[1] += velocidade
        if quadrado[1] > altura:
            continue

        cor_alvo = lixeira_tocada(quadrado, alvos)
        if cor_alvo is None:
            restantes.append(quadrado)
            continue

        if quadrado[2] == cor_alvo:
            pontuacao += PONTOS_ACERTO * multiplicador
            tocar_som(CAMINHO_SOM_ACERTO)
            acertos+=1
            if acertos == multiplicadorAcertos:
                multiplicador = min(multiplicador + 1, multiplicadorMax)
                acertos = 0

        else:
            pontuacao = max(0, pontuacao - PENALIDADE_ERRO)
            tocar_som(CAMINHO_SOM_ERRO)
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


def criar_fundo_texto(tamanho):
    fundo = pygame.Surface(tamanho, pygame.SRCALPHA)
    fundo.fill((*COR_PRETA, OPACIDADE_FUNDO_UI))
    return fundo


def desenhar_fundo_texto(tela, retangulo):
    tela.blit(criar_fundo_texto(retangulo.size), retangulo.topleft)


def renderizar_texto_3d(fonte, texto, cor):
    return fonte.render(texto, False, cor), fonte.render(texto, False, COR_PRETA)


def renderizar_texto_3d_com_borda(fonte, texto, cor, espessura):
    texto_cor, texto_preto = renderizar_texto_3d(fonte, texto, cor)
    return aplicar_borda_3d(texto_cor, texto_preto, espessura)


def renderizar_linha_colorida(fonte, partes, espessura):
    imagens = [fonte.render(texto, False, cor) for texto, cor in partes]
    texto_cor = pygame.Surface(
        (sum(imagem.get_width() for imagem in imagens), fonte.get_height()), pygame.SRCALPHA
    )
    x = 0
    for imagem in imagens:
        texto_cor.blit(imagem, (x, 0))
        x += imagem.get_width()
    texto_preto = fonte.render("".join(texto for texto, _ in partes), False, COR_PRETA)
    return aplicar_borda_3d(texto_cor, texto_preto, espessura)


def aplicar_borda_3d(texto_cor, texto_preto, espessura):
    largura, altura = texto_cor.get_size()
    contorno = pygame.Surface((largura + 2 * espessura, altura + 2 * espessura), pygame.SRCALPHA)
    for dx in (-espessura, 0, espessura):
        for dy in (-espessura, 0, espessura):
            contorno.blit(texto_preto, (espessura + dx, espessura + dy))
    com_borda = contorno.copy()
    com_borda.blit(texto_cor, (espessura, espessura))
    return com_borda, contorno


def angulo_pendulo(amplitude):
    return amplitude * math.sin(
        2 * math.pi * pygame.time.get_ticks() / 1000 / PERIODO_PENDULO
    )


def posicionar_pendulo(caixa, imagem_girada, angulo, ponto_giro="midtop"):
    pivo = pygame.math.Vector2(getattr(caixa, ponto_giro))
    centro = pivo + (pygame.math.Vector2(caixa.center) - pivo).rotate(-angulo)
    return imagem_girada.get_rect(center=(round(centro.x), round(centro.y)))


def montar_nine_slice(imagem, tamanho, corte, ampliacao):
    largura, altura = tamanho
    largura_imagem, altura_imagem = imagem.get_size()
    borda = corte * ampliacao
    colunas = (
        (0, corte, 0, borda),
        (corte, largura_imagem - 2 * corte, borda, largura - 2 * borda),
        (largura_imagem - corte, corte, largura - borda, borda),
    )
    linhas = (
        (0, corte, 0, borda),
        (corte, altura_imagem - 2 * corte, borda, altura - 2 * borda),
        (altura_imagem - corte, corte, altura - borda, borda),
    )
    resultado = pygame.Surface(tamanho, pygame.SRCALPHA)
    for origem_x, largura_pedaco, destino_x, largura_destino in colunas:
        for origem_y, altura_pedaco, destino_y, altura_destino in linhas:
            pedaco = imagem.subsurface((origem_x, origem_y, largura_pedaco, altura_pedaco))
            resultado.blit(
                pygame.transform.scale(pedaco, (largura_destino, altura_destino)),
                (destino_x, destino_y),
            )
    return resultado


def imagem_botao(cor, tamanho):
    chave = (cor, tamanho)
    if chave not in SPRITES_BOTOES:
        sprite = pygame.image.load(str(SPRITE_BOTAO_POR_COR[cor])).convert_alpha()
        ampliacao = max(1, int(ESCALA_TELA))
        botao = montar_nine_slice(sprite, tamanho, CORTE_SPRITE_BOTAO, ampliacao)
        sombra = botao.copy()
        sombra.fill((*COR_PRETA, 255), special_flags=pygame.BLEND_RGBA_MULT)
        SPRITES_BOTOES[chave] = (botao, sombra)
    return SPRITES_BOTOES[chave]


def tocar_som(caminho):
    if not pygame.mixer.get_init():
        return
    if caminho not in SONS:
        SONS[caminho] = pygame.mixer.Sound(str(caminho))
    SONS[caminho].play()


def carregar_icone_tempo(altura_texto):
    if altura_texto not in SPRITES_ICONES:
        imagem = pygame.image.load(str(CAMINHO_ICONE_TEMPO)).convert_alpha()
        ampliacao = max(1, round(altura_texto / imagem.get_height()))
        SPRITES_ICONES[altura_texto] = pygame.transform.scale(
            imagem, (imagem.get_width() * ampliacao, imagem.get_height() * ampliacao)
        )
    return SPRITES_ICONES[altura_texto]


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

    pixel_fonte = FONTE_HUD_TAMANHO // GRADE_FONTE_HUD
    texto_pontuacao, sombra_pontuacao = renderizar_texto_3d_com_borda(
        fonte_hud, str(pontuacao), COR_BRANCA, pixel_fonte
    )
    texto_tempo, sombra_tempo = renderizar_texto_3d_com_borda(
        fonte_hud, tempo, COR_BRANCA, pixel_fonte
    )
    texto_multiplicador, sombra_multiplicador = renderizar_texto_3d_com_borda(
        fonte_hud, f"x{multiplicador}", COR_AMARELA, pixel_fonte
    )
    x_multiplicador = largura - texto_multiplicador.get_width() - MARGEM_UI
    caixa_multiplicador = texto_multiplicador.get_rect(
        topleft=(x_multiplicador, MARGEM_UI)
    )
    caixa_pontuacao = texto_pontuacao.get_rect(
        topright=(x_multiplicador - multiplicadorEspacamento, MARGEM_UI)
    )
    icone_tempo = carregar_icone_tempo(texto_tempo.get_height())
    caixa_icone = icone_tempo.get_rect(
        midleft=(MARGEM_UI, MARGEM_UI + (texto_tempo.get_height() - pixel_fonte) // 2)
    )
    caixa_tempo = texto_tempo.get_rect(topleft=(caixa_icone.right + pixel_fonte, MARGEM_UI))

    for fundo in (caixa_icone.union(caixa_tempo), caixa_pontuacao.union(caixa_multiplicador)):
        desenhar_fundo_texto(
            tela,
            fundo.inflate(2 * MARGEM_INTERNA_UI, 2 * MARGEM_INTERNA_UI),
        )

    angulo = angulo_pendulo(AMPLITUDE_PENDULO)
    texto_multiplicador = pygame.transform.rotate(texto_multiplicador, angulo)
    sombra_multiplicador = pygame.transform.rotate(sombra_multiplicador, angulo)
    caixa_pendulo = posicionar_pendulo(caixa_multiplicador, texto_multiplicador, angulo)

    textos = (
        (texto_multiplicador, sombra_multiplicador, caixa_pendulo),
        (texto_pontuacao, sombra_pontuacao, caixa_pontuacao),
        (texto_tempo, sombra_tempo, caixa_tempo),
    )
    for _, sombra, caixa in textos:
        tela.blit(sombra, caixa.move(pixel_fonte, pixel_fonte))
    for texto, _, caixa in textos:
        tela.blit(texto, caixa)
    tela.blit(icone_tempo, caixa_icone)

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

def criar_botoes(largura, altura, rotulo_principal, centro_y, cores):
    botao_largura = largura // 3
    botao_altura = altura // 5
    espacamento = largura // 12
    esquerda = (largura - 2 * botao_largura - espacamento) // 2
    topo = centro_y - botao_altura // 2
    return [
        (
            pygame.Rect(esquerda, topo, botao_largura, botao_altura),
            rotulo_principal,
            True,
            cores[0],
        ),
        (
            pygame.Rect(esquerda + botao_largura + espacamento, topo, botao_largura, botao_altura),
            "Sair",
            False,
            cores[1],
        ),
    ]

def desenhar_fundo_rolando(tela, ladrilho):
    largura, altura = tela.get_size()
    largura_ladrilho, altura_ladrilho = ladrilho.get_size()
    deslocamento = int(pygame.time.get_ticks() / 1000 * VELOCIDADE_FUNDO_MENU)
    inicio_x = -(deslocamento % largura_ladrilho)
    inicio_y = -(deslocamento % altura_ladrilho)
    for x in range(inicio_x, largura, largura_ladrilho):
        for y in range(inicio_y, altura, altura_ladrilho):
            tela.blit(ladrilho, (x, y))

def desenhar_menu(tela, botoes, progresso, controle, fonte, textos, ladrilho_fundo, deslocamento_3d):
    if ladrilho_fundo is None:
        tela.fill(COR_FUNDO)
    else:
        desenhar_fundo_rolando(tela, ladrilho_fundo)

    for imagem, posicao, amplitude, ponto_giro in textos:
        if amplitude:
            angulo = angulo_pendulo(amplitude)
            girada = pygame.transform.rotate(imagem, angulo)
            caixa = imagem.get_rect(topleft=posicao)
            tela.blit(girada, posicionar_pendulo(caixa, girada, angulo, ponto_giro))
        else:
            tela.blit(imagem, posicao)

    for retangulo, texto, _, cor in botoes:
        if USAR_SPRITE_BOTAO:
            imagem, sombra_botao = imagem_botao(cor, retangulo.size)
            tela.blit(sombra_botao, retangulo.move(deslocamento_3d, deslocamento_3d))
            tela.blit(imagem, retangulo)
        else:
            pygame.draw.rect(tela, COR_PRETA, retangulo.move(deslocamento_3d, deslocamento_3d))
            pygame.draw.rect(tela, cor, retangulo)
            pygame.draw.rect(tela, COR_PRETA, retangulo, deslocamento_3d)
        espessura = fonte.get_height() // GRADE_FONTE_HUD
        rotulo, sombra = renderizar_texto_3d_com_borda(fonte, texto, COR_BRANCA, espessura)
        caixa_rotulo = rotulo.get_rect(center=retangulo.center)
        tela.blit(sombra, caixa_rotulo.move(espessura, espessura))
        tela.blit(rotulo, caixa_rotulo)

    for pe in controle.pes:
        if not pe["ativo"]:
            continue

        centro = (int(pe["x"]), int(pe["y"]))
        pygame.draw.circle(tela, COR_BRANCA, centro, RAIO_PE, 4)
        for (retangulo, _, _, _), tempo in zip(botoes, progresso):
            if tempo > 0 and retangulo.collidepoint(centro):
                fim = 2 * 3.14159 * min(tempo / TEMPO_BOTAO_PE, 1)
                caixa = pygame.Rect(0, 0, RAIO_PE * 3, RAIO_PE * 3)
                caixa.center = centro
                pygame.draw.arc(tela, COR_AMARELA, caixa, 0, fim, 6)

    pygame.display.flip()

def executar_menu(tela, rastreador, controle, botoes, textos, fonte, ladrilho_fundo, deslocamento_3d):
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
                for retangulo, _, acao, _ in botoes:
                    if retangulo.collidepoint(evento.pos):
                        return acao

        controle.atualizar(rastreador.pes_na_tela(), dt, [])

        for indice, (retangulo, _, acao, _) in enumerate(botoes):
            pisado = any(
                pe["ativo"] and retangulo.collidepoint(pe["x"], pe["y"])
                for pe in controle.pes
            )
            progresso[indice] = progresso[indice] + dt if pisado else 0.0
            if progresso[indice] >= TEMPO_BOTAO_PE:
                return acao

        desenhar_menu(tela, botoes, progresso, controle, fonte, textos, ladrilho_fundo, deslocamento_3d)
        atualizar_janela_camera(rastreador)

def executar_tela_inicial(tela, rastreador, controle):
    largura, altura = tela.get_size()
    botoes = criar_botoes(
        largura, altura, "Novo Jogo", altura // 2, (COR_VERDE, COR_VERMELHA)
    )
    ampliacao_logo = 2 * max(1, int(ESCALA_TELA))
    camadas_logo = []
    for caminho in (CAMINHO_LOGO_MUNDO, CAMINHO_LOGO_TEXTO):
        imagem = pygame.image.load(str(caminho)).convert_alpha()
        camadas_logo.append(
            pygame.transform.scale(
                imagem,
                (imagem.get_width() * ampliacao_logo, imagem.get_height() * ampliacao_logo),
            )
        )
    posicao_logo = camadas_logo[0].get_rect(center=(largura // 2, botoes[0][0].top // 2)).topleft
    fundo = pygame.transform.scale(
        pygame.image.load(str(CAMINHO_FUNDO_MENU)).convert(), (largura, altura)
    )
    textos = [
        (fundo, (0, 0), 0, None),
        (criar_fundo_texto((largura, altura)), (0, 0), 0, None),
        (camadas_logo[0], posicao_logo, 0, None),
        (camadas_logo[1], posicao_logo, AMPLITUDE_PENDULO_LOGO, "center"),
    ]
    fonte = pygame.font.Font(str(CAMINHO_FONTE_HUD), FONTE_FIM_TAMANHO)
    deslocamento_3d = FONTE_TITULO_TAMANHO // GRADE_FONTE_HUD
    fonte_creditos = pygame.font.Font(str(CAMINHO_FONTE_HUD), FONTE_MENSAGEM_TAMANHO)
    espessura_creditos = fonte_creditos.get_height() // GRADE_FONTE_HUD
    linhas_creditos = [
        renderizar_linha_colorida(fonte_creditos, partes, espessura_creditos)
        for partes in LINHAS_CREDITOS
    ]
    textos += empilhar_linhas(
        linhas_creditos,
        espessura_creditos,
        fonte_creditos.get_height() // 2,
        largura,
        botoes[0][0].bottom + deslocamento_3d,
        altura,
    )
    return executar_menu(
        tela, rastreador, controle, botoes, textos, fonte, None, deslocamento_3d
    )

def carregar_mensagens():
    with open(CAMINHO_MENSAGENS, encoding="utf-8") as arquivo:
        return json.load(arquivo)["mensagens"]

def quebrar_linhas(fonte, texto, largura_maxima):
    linhas = []
    linha = ""
    for palavra in texto.split():
        tentativa = f"{linha} {palavra}".strip()
        if linha and fonte.size(tentativa)[0] > largura_maxima:
            linhas.append(linha)
            linha = palavra
        else:
            linha = tentativa
    if linha:
        linhas.append(linha)
    return linhas

def montar_linhas_texto(fonte, texto, cor, largura_maxima, largura_tela, topo, base):
    espessura = fonte.get_height() // GRADE_FONTE_HUD
    espaco_linhas = fonte.get_height() // 2
    linhas = [
        renderizar_texto_3d_com_borda(fonte, linha, cor, espessura)
        for linha in quebrar_linhas(fonte, texto, largura_maxima - 2 * espessura)
    ]
    return empilhar_linhas(linhas, espessura, espaco_linhas, largura_tela, topo, base)

def empilhar_linhas(linhas, espessura, espaco_linhas, largura_tela, topo, base):
    altura_texto = sum(linha.get_height() for linha, _ in linhas) + espaco_linhas * (len(linhas) - 1)
    y = (topo + base - altura_texto) // 2
    textos = []
    for linha, sombra in linhas:
        x = (largura_tela - linha.get_width()) // 2
        textos.append((sombra, (x + espessura, y + espessura), 0, None))
        textos.append((linha, (x, y), 0, None))
        y += linha.get_height() + espaco_linhas
    return textos

def executar_menu_fim(tela, rastreador, controle, pontuacao, fundo_jogo):
    largura, altura = tela.get_size()
    fonte_titulo = pygame.font.Font(str(CAMINHO_FONTE_HUD), FONTE_TITULO_TAMANHO)
    fonte_fim = pygame.font.Font(str(CAMINHO_FONTE_HUD), FONTE_FIM_TAMANHO)
    fonte_mensagem = pygame.font.Font(str(CAMINHO_FONTE_HUD), FONTE_MENSAGEM_TAMANHO)
    botoes = criar_botoes(
        largura, altura, "Recomeçar", altura * 3 // 4, (COR_VERDE, COR_VERMELHA)
    )
    deslocamento_3d = FONTE_TITULO_TAMANHO // GRADE_FONTE_HUD
    texto_fim, sombra_fim = renderizar_texto_3d_com_borda(
        fonte_titulo, "Fim de jogo!", COR_AMARELA, deslocamento_3d
    )
    espessura_fim = FONTE_FIM_TAMANHO // GRADE_FONTE_HUD
    texto_pontuacao, sombra_pontuacao = renderizar_texto_3d_com_borda(
        fonte_fim, f"Pontuação final: {pontuacao}", COR_AZUL, espessura_fim
    )
    topo_pontuacao = altura // 3 - espessura_fim
    x_pontuacao = (largura - texto_pontuacao.get_width()) // 2
    x_fim, y_fim = (largura - texto_fim.get_width()) // 2, altura // 5 - deslocamento_3d
    textos = [
        (
            sombra_fim,
            (x_fim + deslocamento_3d, y_fim + deslocamento_3d),
            AMPLITUDE_PENDULO_TITULO,
            "midtop",
        ),
        (texto_fim, (x_fim, y_fim), AMPLITUDE_PENDULO_TITULO, "midtop"),
        (
            sombra_pontuacao,
            (x_pontuacao + espessura_fim, topo_pontuacao + espessura_fim),
            0,
            None,
        ),
        (texto_pontuacao, (x_pontuacao, topo_pontuacao), 0, None),
    ]

    largura_mensagem = botoes[1][0].right - botoes[0][0].left
    mensagem = random.choice(carregar_mensagens())
    fim_pontuacao = topo_pontuacao + texto_pontuacao.get_height()
    textos += montar_linhas_texto(
        fonte_mensagem,
        mensagem,
        COR_BRANCA,
        largura_mensagem,
        largura,
        fim_pontuacao,
        botoes[0][0].top,
    )

    textos.insert(0, (criar_fundo_texto((largura, altura)), (0, 0), 0, None))

    ladrilho_fundo = None
    if MOSTRAR_FUNDO_MENU:
        imagem_fundo = pygame.image.load(str(CAMINHO_FUNDO_MENU)).convert()
        ampliacao_fundo = int(ESCALA_TELA) + AMPLIACAO_EXTRA_FUNDO_MENU
        ladrilho_fundo = pygame.transform.scale(
            imagem_fundo,
            (
                imagem_fundo.get_width() * ampliacao_fundo,
                imagem_fundo.get_height() * ampliacao_fundo,
            ),
        )
    else:
        textos.insert(0, (fundo_jogo, (0, 0), 0, None))
    return executar_menu(
        tela, rastreador, controle, botoes, textos, fonte_fim, ladrilho_fundo, deslocamento_3d
    )

def executar_jogo(tela, rastreador, controle):
    """Executa o loop principal do jogo."""
    largura, altura = tela.get_size()
    alvos = criar_alvos(largura, altura)
    colunas = [retangulo.centerx - TAMANHO_ITEM // 2 for retangulo, _ in alvos]
    relogio = pygame.time.Clock()
    horario_inicio = pygame.time.get_ticks() / 1000
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
        nivel = int(segundo_passados // INTERVALO_DIFICULDADE)
        velocidade = VELOCIDADE_QUADRADO + nivel * AUMENTO_VELOCIDADE

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
            if executar_menu_fim(tela, rastreador, controle, pontuacao, tela.copy()):
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
                acertos,
                velocidade,
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
