import time
import pygame


def quadrado_em(pos, quadrados, ocupados, residuo, margem):
    perto = [
        q for q in quadrados
        if not any(q is c for c in ocupados)
        and pygame.Rect(q[0], q[1], residuo, residuo).inflate(margem * 2, margem * 2).collidepoint(pos)
    ]
    if not perto:
        return None
    return min(perto, key=lambda q: (q[0] + residuo / 2 - pos[0]) ** 2 + (q[1] + residuo / 2 - pos[1]) ** 2)


def mover(quadrado, pos, residuo, largura, altura):
    quadrado[0] = max(0, min(pos[0] - residuo / 2, largura - residuo))
    quadrado[1] = max(0, min(pos[1] - residuo / 2, altura - residuo))


class ControlePes:

    def __init__(self, residuo, margem_pegar, largura, altura, tempo_pegar=0.5, tempo_soltar=0.6):
        self.residuo = residuo
        self.margem_pegar = margem_pegar
        self.largura = largura
        self.altura = altura
        self.tempo_pegar = tempo_pegar
        self.tempo_soltar = tempo_soltar
        self.pes = [
            {"x": 0.0, "y": 0.0, "visto": 0.0, "ativo": False, "carregando": None, "mirando": None, "tempo": 0.0},
            {"x": 0.0, "y": 0.0, "visto": 0.0, "ativo": False, "carregando": None, "mirando": None, "tempo": 0.0},
        ]

    def carregados(self):
        return [p["carregando"] for p in self.pes if p["carregando"] is not None]

    def soltar(self, quadrado):
        for pe in self.pes:
            if pe["carregando"] is quadrado:
                pe["carregando"] = None

    def atualizar(self, vistos, dt, quadrados, outros_ocupados=()):
        agora = time.monotonic()

        livres = list(range(len(self.pes)))
        for x, y in vistos:
            i = min(livres, key=lambda i: (self.pes[i]["x"] - x) ** 2 + (self.pes[i]["y"] - y) ** 2 if self.pes[i]["ativo"] else float("inf"))
            livres.remove(i)
            pe = self.pes[i]
            if pe["ativo"]:
                pe["x"] += (x - pe["x"]) * 0.5
                pe["y"] += (y - pe["y"]) * 0.5
            else:
                pe["x"], pe["y"] = x, y
            pe["ativo"] = True
            pe["visto"] = agora

        for pe in self.pes:
            visivel = pe["ativo"] and agora - pe["visto"] < 0.15
            if pe["ativo"] and agora - pe["visto"] >= self.tempo_soltar:
                pe["ativo"] = False
                pe["carregando"] = None
                pe["mirando"] = None
                pe["tempo"] = 0.0
            if not visivel:
                continue
            pos = (pe["x"], pe["y"])
            if pe["carregando"] is not None:
                mover(pe["carregando"], pos, self.residuo, self.largura, self.altura)
                continue
            ocupados = self.carregados() + list(outros_ocupados)
            alvo = quadrado_em(pos, quadrados, ocupados, self.residuo, self.margem_pegar)
            if alvo is not None and alvo is pe["mirando"]:
                pe["tempo"] += dt
                if pe["tempo"] >= self.tempo_pegar:
                    pe["carregando"] = alvo
                    pe["mirando"] = None
                    pe["tempo"] = 0.0
            else:
                pe["mirando"] = alvo
                pe["tempo"] = 0.0
