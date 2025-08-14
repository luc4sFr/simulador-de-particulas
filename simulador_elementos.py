import random
import pygame
import json

# --- CARREGAMENTO DAS PROPRIEDADES ---
def carregar_propriedades(caminho_arquivo='config.json'):
    """
    Carrega as propriedades dos elementos de um arquivo JSON.
    Isso permite que o comportamento dos elementos seja modificado sem alterar o código.
    """
    with open(caminho_arquivo, 'r') as f:
        return json.load(f)

# Dicionário central que armazena todas as propriedades carregadas do JSON.
propriedades_elementos = carregar_propriedades()

# --- CONFIGURAÇÕES GLOBAIS ---
ESCALA = 2  # Fator de zoom. Cada partícula será um quadrado de ESCALA x ESCALA pixels.
todos_elementos = {}  # Dicionário para armazenar todas as partículas na grade, usando coordenadas (x,y) como chaves.
alterado = {}  # Dicionário para rastrear as células que foram atualizadas em um quadro, otimizando o redesenho.
FPS = 120  # Quadros por segundo desejados para a simulação.

# Variáveis globais para as dimensões da tela em unidades de grade (pixels / ESCALA).
TelaX = 0
TelaY = 0

def definir_dimensoes_tela(largura, altura):
    """Atualiza as dimensões da tela para o módulo de elementos, usado para verificar limites."""
    global TelaX, TelaY
    TelaX = largura
    TelaY = altura

# --- DEFINIÇÃO DE CORES ---
# Paletas de cores para os diferentes elementos. Algumas são fixas, outras são listas para variação.
COR_VAZIO = (0, 0, 0)
COR_ELEMENTO_AREIA = (255, 255, 85)
COR_ELEMENTO_AREIA_MOLHADA = (255, 170, 0)
COR_METAL = (192, 192, 192)
COR_PEDRA = (85, 85, 85)
COR_VIDRO = (200, 220, 230)
COR_PLANTA = (40, 180, 60)
COR_VAPOR = (211, 211, 211)
PALETA_AGUA = [(85, 85, 255), (100, 100, 255), (70, 70, 230)]
PALETA_ACIDO = [(85, 255, 85), (120, 255, 120), (50, 230, 50)]
PALETA_GAS = [(170, 0, 170), (180, 50, 180), (160, 0, 160)]
PALETA_FOGO = [(255, 69, 0), (255, 100, 0), (255, 140, 0)]
PALETA_LAVA = [(255, 125, 85), (255, 100, 0), (255, 200, 0)]

# --- TIPOS DE ELEMENTOS ---
# Categorias para classificar o comportamento geral dos elementos.
TIPO_SOLIDO = 1
TIPO_LIQUID = 2
TIPO_GASOSO = 3

# --- CLASSE BASE PARA TODAS AS PARTÍCULAS ---
class Particula:
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        """Construtor base para uma partícula."""
        self.x = x  # Posição da partícula no eixo X.
        self.y = y  # Posição da partícula no eixo Y.
        self.todos_elementos = todos_elementos  # Referência ao dicionário global de elementos.
        self.superficie = SUPERFICIE  # Superfície do Pygame onde a partícula será desenhada.

    def draw(self, x, y, cor):
        """Desenha a partícula na superfície como um retângulo preenchido."""
        self.superficie.fill(cor, pygame.Rect(x * ESCALA, y * ESCALA, ESCALA, ESCALA))

    def verifica_exclusao(self, x, y):
        """Verifica se a partícula está fora dos limites da tela e a remove se estiver."""
        if not 0 <= self.x < TelaX or not 0 <= self.y < TelaY:
            self.draw(x, y, COR_VAZIO)  # Apaga o rastro da partícula.
            if (x, y) in self.todos_elementos:
                 del self.todos_elementos[(x, y)]  # Remove do dicionário de elementos.
            return True
        return False

    def verifica_alvo(self, x, y):
        """Verifica se a posição de destino (x, y) está vazia."""
        return self.todos_elementos.get((x, y)) is None

    def goto(self, novo_x, novo_y, overwrite_chance=0.0):
        """
        Tenta mover a partícula para uma nova posição (novo_x, novo_y).
        Contém a lógica central de interações entre diferentes tipos de partículas.
        """
        global alterado
        alvo = self.todos_elementos.get((novo_x, novo_y))

        # --- LÓGICA DE INTERAÇÃO ENTRE ELEMENTOS ---
        # Cada bloco 'if' verifica os tipos da partícula atual (self) e da partícula alvo
        # para aplicar uma regra de interação específica.

        if isinstance(self, Acido) and isinstance(alvo, Vidro):
            overwrite_chance = 0.0  # Ácido não pode corroer Vidro.

        if isinstance(self, Fogo) and isinstance(alvo, Madeira):
            # Fogo transforma Madeira em Carvão e se extingue.
            self.todos_elementos[(alvo.x, alvo.y)] = Carvao(alvo.x, alvo.y, self.todos_elementos, self.superficie)
            self.vida = 0
            return False

        if isinstance(self, Fogo) and isinstance(alvo, Planta):
            # Fogo queima Planta, com chance de virar Cinzas.
            if random.random() < propriedades_elementos["Planta"]["chance_cinzas"]:
                self.todos_elementos[(alvo.x, alvo.y)] = Cinzas(alvo.x, alvo.y, self.todos_elementos, self.superficie)
            else:
                self.draw(alvo.x, alvo.y, COR_VAZIO)
                if (alvo.x, alvo.y) in self.todos_elementos:
                    del self.todos_elementos[(alvo.x, alvo.y)]
            # Propaga o fogo para uma célula vizinha vazia.
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0: continue
                    nx, ny = alvo.x + dx, alvo.y + dy
                    if self.verifica_alvo(nx, ny):
                        self.todos_elementos[(nx, ny)] = Fogo(nx, ny, self.todos_elementos, self.superficie)
                        break
            self.vida = 0
            return False

        if isinstance(self, Agua) and isinstance(alvo, Areia):
            # Água molha a Areia.
            if not alvo.is_wet:
                alvo.is_wet = True
                alvo.cor = COR_ELEMENTO_AREIA_MOLHADA
                alvo.draw(novo_x, novo_y, alvo.cor)
            return False

        if isinstance(self, Areia) and isinstance(alvo, Agua):
            # Areia ao cair na Água, se torna molhada e a substitui.
            self.is_wet = True
            self.cor = COR_ELEMENTO_AREIA_MOLHADA
            overwrite_chance = 1.0

        if isinstance(self, Areia) and self.is_wet and isinstance(alvo, Areia) and not alvo.is_wet and random.random() < 0.08:
            # Areia molhada pode molhar areia seca adjacente.
            alvo.is_wet = True
            alvo.cor = COR_ELEMENTO_AREIA_MOLHADA
            alvo.draw(novo_x, novo_y, alvo.cor)
            return False

        if isinstance(self, Lava) and isinstance(alvo, Agua):
            # Lava em contato com a Água esfria e transforma a Água em Vapor.
            self.cool_down()
            self.todos_elementos[(alvo.x, alvo.y)] = Vapor(alvo.x, alvo.y, self.todos_elementos, self.superficie)
            return False

        if isinstance(self, Agua) and isinstance(alvo, Lava):
            # Água em contato com a Lava evapora e a Lava esfria.
            alvo.cool_down()
            alvo.draw(novo_x, novo_y, alvo.cor)
            self.todos_elementos[(self.x, self.y)] = Vapor(self.x, self.y, self.todos_elementos, self.superficie)
            return False
            
        if isinstance(self, Agua) and isinstance(alvo, Carvao):
            # Água apaga o Carvão, transformando-o em Cinzas.
            self.todos_elementos[(alvo.x, alvo.y)] = Cinzas(alvo.x, alvo.y, self.todos_elementos, self.superficie)
            self.draw(self.x, self.y, COR_VAZIO) # A água desaparece.
            if (self.x, self.y) in self.todos_elementos:
                del self.todos_elementos[(self.x, self.y)]
            return False
            
        # Lógica de propagação de calor/frio na Lava.
        if isinstance(self, Lava) and self.is_cool and isinstance(alvo, Lava) and not alvo.is_cool and random.random() < 0.08:
            alvo.cool_down()
            alvo.draw(novo_x, novo_y, alvo.cor)
            return False

        if isinstance(self, Lava) and not self.is_cool and isinstance(alvo, Lava) and alvo.is_cool and random.random() < 0.08:
            alvo.heat_up()
            alvo.draw(novo_x, novo_y, alvo.cor)
            return False

        if isinstance(self, Fogo) and isinstance(alvo, Gas):
            # Gás é inflamável e explode em fogo.
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = alvo.x + dx, alvo.y + dy
                    if self.todos_elementos.get((nx, ny)) is None:
                        self.todos_elementos[(nx, ny)] = Fogo(nx, ny, self.todos_elementos, self.superficie)
            self.draw(alvo.x, alvo.y, COR_VAZIO)
            if self.todos_elementos.get((alvo.x, alvo.y)) == alvo:
                del self.todos_elementos[(alvo.x, alvo.y)]
            self.vida = 0
            return False

        # --- LÓGICA DE MOVIMENTO PADRÃO ---
        if alvo is None or random.random() < overwrite_chance:
            (x_antigo, y_antigo) = (self.x, self.y)
            # Remove a partícula da posição antiga.
            if (x_antigo, y_antigo) in self.todos_elementos and self.todos_elementos[(x_antigo, y_antigo)] == self:
                del self.todos_elementos[(x_antigo, y_antigo)]
            self.draw(x_antigo, y_antigo, COR_VAZIO) # Limpa a tela na posição antiga.
            
            # Atualiza para a nova posição.
            (self.x, self.y) = (novo_x, novo_y)
            self.todos_elementos[(novo_x, novo_y)] = self
            self.draw(novo_x, novo_y, self.cor) # Desenha na nova posição.
            
            # Marca ambas as posições como alteradas para o redesenho.
            alterado[(x_antigo, y_antigo)] = True
            alterado[(novo_x, novo_y)] = True
            return True # Retorna True para indicar que o movimento ocorreu.
        else:
            return False # Retorna False se o movimento foi bloqueado.


# --- CLASSES DE ELEMENTOS ESPECÍFICOS ---
# Cada classe define o comportamento de um elemento através do metodo `update`.

class Vidro(Particula):
    """Elemento sólido e estático com efeito de transparência."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_SOLIDO
        self.cor_base = COR_VIDRO
        self.cor = self.cor_base
        self.fator_transparencia = 0.6  # Quão transparente o vidro é.
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)

    def update(self):
        """Atualiza a cor do vidro com base na cor da partícula abaixo dele para simular transparência."""
        vizinho = self.todos_elementos.get((self.x, self.y + 1), Vazio(self.todos_elementos, self.superficie))
        cor_vizinho = vizinho.cor if vizinho.cor is not None else COR_VAZIO
        # Mistura a cor base do vidro com a cor do vizinho.
        nova_cor_r = int(self.cor_base[0] * self.fator_transparencia + cor_vizinho[0] * (1 - self.fator_transparencia))
        nova_cor_g = int(self.cor_base[1] * self.fator_transparencia + cor_vizinho[1] * (1 - self.fator_transparencia))
        nova_cor_b = int(self.cor_base[2] * self.fator_transparencia + cor_vizinho[2] * (1 - self.fator_transparencia))
        nova_cor = (nova_cor_r, nova_cor_g, nova_cor_b)
        # Redesenha apenas se a cor mudar para otimizar.
        if self.cor != nova_cor:
            self.cor = nova_cor
            self.draw(self.x, self.y, self.cor)

class Madeira(Particula):
    """Elemento sólido e estático que pode ser queimado."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_SOLIDO
        self.cor = tuple(propriedades_elementos["Madeira"]["cor"])
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)
    def update(self):
        """A madeira não faz nada por si só, apenas reage a outros elementos."""
        pass

class Carvao(Particula):
    """
    Sólido que resulta da queima da madeira.
    Pode gerar fogo espontaneamente e se transforma em cinzas com o tempo.
    """
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_SOLIDO
        self.cor = (50, 50, 50)
        # Propriedades carregadas do config.json
        self.vida = propriedades_elementos["Carvao"]["vida"]
        self.chance_gerar_fogo = propriedades_elementos["Carvao"]["chance_gerar_fogo"]
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)

    def update(self):
        """O carvão tem uma vida útil, pode gerar fogo e transformar madeira adjacente."""
        # Com uma pequena chance, transforma madeira vizinha em carvão.
        if random.random() < 0.005:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0: continue
                    vizinho = self.todos_elementos.get((self.x + dx, self.y + dy))
                    if isinstance(vizinho, Madeira):
                        self.todos_elementos[(vizinho.x, vizinho.y)] = Carvao(vizinho.x, vizinho.y, self.todos_elementos, self.superficie)

        self.vida -= 1
        # Chance de criar uma partícula de fogo em um local adjacente vazio.
        if random.random() < self.chance_gerar_fogo:
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            if dx != 0 or dy != 0:
                vizinho_x, vizinho_y = self.x + dx, self.y + dy
                if self.verifica_alvo(vizinho_x, vizinho_y):
                    self.todos_elementos[(vizinho_x, vizinho_y)] = Fogo(vizinho_x, vizinho_y, self.todos_elementos, self.superficie)
        # Quando a vida acaba, transforma-se em Cinzas.
        if self.vida <= 0:
            self.todos_elementos[(self.x, self.y)] = Cinzas(self.x, self.y, self.todos_elementos, self.superficie)
            return

class Cinzas(Particula):
    """Elemento sólido leve que se comporta de forma parecida com a areia."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_SOLIDO
        self.cor = tuple(propriedades_elementos["Cinzas"]["cor"])
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)
    def update(self):
        """Tenta cair, priorizando o movimento vertical."""
        if self.verifica_exclusao(self.x, self.y): return
        updates, direcao_horizontal = 0, random.randint(0, 1) * 2 - 1
        if random.random() > 0.05: direcao_horizontal = 0 # Baixa chance de se mover lateralmente.
        while updates < 2:
            if self.goto(self.x, self.y + 2): updates += 2 # Tenta cair 2 pixels.
            elif self.goto(self.x, self.y + 1): updates += 1 # Tenta cair 1 pixel.
            if self.goto(self.x + direcao_horizontal, self.y): pass
            updates += 2

class Metal(Particula):
    """Elemento sólido, pesado e imóvel."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_SOLIDO
        self.cor = COR_METAL
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)
    def update(self):
        """Metal não se atualiza."""
        pass

class Agua(Particula):
    """Elemento líquido que flui para baixo e para os lados."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_LIQUID
        self.cor = random.choice(PALETA_AGUA)
        self.velocidade_descida = propriedades_elementos["Agua"]["velocidade_descida"]
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)
    def update(self):
        """A água pode fazer uma planta crescer e flui para baixo."""
        # Pequena chance de se transformar em Planta se tocar em outra Planta.
        if random.random() < 0.01:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0: continue
                    if isinstance(self.todos_elementos.get((self.x + dx, self.y + dy)), Planta):
                        self.todos_elementos[(self.x, self.y)] = Planta(self.x, self.y, self.todos_elementos, self.superficie)
                        return

        if self.verifica_exclusao(self.x, self.y): return
        # Animação de cor.
        if random.random() < 0.2:
            self.cor = random.choice(PALETA_AGUA)
            self.draw(self.x, self.y, self.cor)
            
        updates, direcao_horizontal = 0, random.randint(0, 1) * 2 - 1
        if random.random() > 0.9: direcao_horizontal = 0 # Alta chance de não se espalhar.
        
        # A velocidade de descida afeta o número de tentativas de movimento.
        while updates < self.velocidade_descida:
            if self.goto(self.x, self.y + 1): # Tenta mover para baixo.
                updates += 1
                if self.goto(self.x, self.y + 1): updates += 1 # Tenta mover para baixo novamente (aceleração).
            if self.goto(self.x + direcao_horizontal, self.y): pass # Tenta mover para os lados.
            elif self.goto(self.x - direcao_horizontal, self.y): direcao_horizontal *= -1 # Tenta o outro lado.
            updates += 0.67

class Acido(Particula):
    """Líquido que dissolve a maioria dos outros elementos."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_LIQUID
        self.cor = random.choice(PALETA_ACIDO)
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)
    def update(self):
        if self.verifica_exclusao(self.x, self.y): return
        # Animação de cor.
        if random.random() < 0.2:
            self.cor = random.choice(PALETA_ACIDO)
            self.draw(self.x, self.y, self.cor)
        
        chance_dissolve = propriedades_elementos["Acido"]["chance_dissolve"]
        updates, direcao_horizontal = 0, random.randint(0, 1) * 2 - 1
        if random.random() > 0.9: direcao_horizontal = 0
        
        # Lógica de movimento similar à da água, mas com a chance de dissolver o que toca.
        while updates < 2:
            if self.goto(self.x, self.y + 1, chance_dissolve):
                updates += 1
                if self.goto(self.x, self.y + 1, chance_dissolve): updates += 1
            if self.goto(self.x + direcao_horizontal, self.y, chance_dissolve): pass
            elif self.goto(self.x - direcao_horizontal, self.y, chance_dissolve):
                direcao_horizontal *= -1
            updates += 1

class Areia(Particula):
    """Elemento sólido granular que cai em pilhas."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_SOLIDO
        self.cor = COR_ELEMENTO_AREIA
        self.chance_move = propriedades_elementos["Areia"]["chance_move"]
        self.is_wet = False  # Estado para saber se está molhada.
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)
    def update(self):
        """Tenta cair, priorizando o movimento vertical. Se estiver molhada, não se move lateralmente."""
        if self.verifica_exclusao(self.x, self.y): return
        chance_move = 0 if self.is_wet else self.chance_move # Areia molhada é mais "pesada".
        updates, direcao_horizontal = 0, random.randint(0, 1) * 2 - 1
        if random.random() > chance_move: direcao_horizontal = 0
        while updates < 2:
            if random.random() > chance_move: direcao_horizontal = 0
            if self.goto(self.x, self.y + 2): updates += 2
            elif self.goto(self.x, self.y + 1): updates += 1
            if self.goto(self.x + direcao_horizontal, self.y): pass
            updates += 2

class Vazio(Particula):
    """Uma classe placeholder para posições vazias, para evitar erros."""
    def __init__(self, todos_elementos, SUPERFICIE):
        self.cor, self.x, self.y = None, None, None
        super().__init__(self.x, self.y, todos_elementos, SUPERFICIE)
    def update(self): pass

class Gas(Particula):
    """Elemento gasoso que sobe e se espalha."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_GASOSO
        self.cor = random.choice(PALETA_GAS)
        self.velocidade_subida = propriedades_elementos["Gas"]["velocidade_subida"]
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)
    def update(self):
        """Lógica de movimento para cima, oposta à da água."""
        if self.verifica_exclusao(self.x, self.y): return
        if random.random() < 0.2:
            self.cor = random.choice(PALETA_GAS)
            self.draw(self.x, self.y, self.cor)
        updates, direcao_horizontal = 0, random.randint(0, 1) * 2 - 1
        if random.random() > 0.9: direcao_horizontal = 0
        
        while updates < self.velocidade_subida:
            if self.goto(self.x, self.y - 1): # Tenta subir.
                updates += 1
                if self.goto(self.x, self.y - 1): updates += 1
            if self.goto(self.x + direcao_horizontal, self.y): pass
            elif self.goto(self.x - direcao_horizontal, self.y): direcao_horizontal *= -1
            updates += 0.67

class Lava(Particula):
    """Líquido denso e quente que se comporta como areia, mas pode esfriar e virar pedra."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_SOLIDO # Comporta-se como sólido granular.
        self.cor = random.choice(PALETA_LAVA)
        self.chance_move = propriedades_elementos["Lava"]["chance_move"]
        self.is_cool = False  # Estado para saber se virou pedra.
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)

    def cool_down(self):
        """Esfria a lava, transformando-a em pedra."""
        self.is_cool, self.cor = True, COR_PEDRA

    def heat_up(self):
        """Aquece a pedra, transformando-a de volta em lava."""
        self.is_cool, self.cor = False, random.choice(PALETA_LAVA)

    def update(self):
        """Move-se como areia, a menos que esteja fria (pedra)."""
        if self.verifica_exclusao(self.x, self.y): return
        if not self.is_cool and random.random() < 0.2:
            self.cor = random.choice(PALETA_LAVA)
            self.draw(self.x, self.y, self.cor)

        if random.random() < 0.025:
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            if dx != 0 or dy != 0:
                vizinho_x, vizinho_y = self.x + dx, self.y + dy
                if self.verifica_alvo(vizinho_x, vizinho_y):
                    self.todos_elementos[(vizinho_x, vizinho_y)] = Fogo(vizinho_x, vizinho_y, self.todos_elementos, self.superficie)
            
        chance_move = 0 if self.is_cool else self.chance_move
        updates, direcao_horizontal = 0, random.randint(0, 1) * 2 - 1
        if random.random() > chance_move: direcao_horizontal = 0
        while updates < 2:
            if random.random() > chance_move: direcao_horizontal = 0
            if self.goto(self.x, self.y + 2): updates += 2
            elif self.goto(self.x, self.y + 1): updates += 1
            if self.goto(self.x + direcao_horizontal, self.y): pass
            updates += 2

class Fogo(Particula):
    """Gás com vida útil limitada que sobe e queima outros elementos."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_GASOSO
        self.cor = random.choice(PALETA_FOGO)
        # Vida útil aleatória dentro de um intervalo definido no config.json.
        vida_min = propriedades_elementos["Fogo"]["vida_min"]
        vida_max = propriedades_elementos["Fogo"]["vida_max"]
        self.vida = random.randint(vida_min, vida_max)
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)

    def update(self):
        """O fogo sobe, perde vida a cada quadro e desaparece quando a vida chega a zero."""
        self.vida -= 1
        if self.vida <= 0:
            self.draw(self.x, self.y, COR_VAZIO) # Apaga o fogo.
            if self.todos_elementos.get((self.x, self.y)) == self:
                del self.todos_elementos[(self.x, self.y)]
            return
            
        if random.random() < 0.2:
            self.cor = random.choice(PALETA_FOGO)
            self.draw(self.x, self.y, self.cor)
            
        if self.verifica_exclusao(self.x, self.y): return
        
        # Lógica de movimento para cima, como um gás.
        updates, direcao_horizontal = 0, random.randint(0, 1) * 2 - 1
        if random.random() > 0.9: direcao_horizontal = 0
        while updates < 2:
            if self.goto(self.x, self.y - 1):
                updates += 1
                if self.goto(self.x, self.y - 1): updates += 1
            if self.goto(self.x + direcao_horizontal, self.y): pass
            elif self.goto(self.x - direcao_horizontal, self.y): direcao_horizontal *= -1
            updates += 0.67

class Planta(Particula):
    """Elemento sólido e estático."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_SOLIDO
        self.cor = COR_PLANTA
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)
    def update(self):
        """A planta não faz nada por si só."""
        pass

class Vapor(Particula):
    """Gás com vida útil, gerado pela interação de água e calor."""
    def __init__(self, x, y, todos_elementos, SUPERFICIE):
        self.tipo = TIPO_GASOSO
        self.cor = COR_VAPOR
        self.vida = random.randint(60, 120) # Vida útil em quadros.
        super().__init__(x, y, todos_elementos, SUPERFICIE)
        self.draw(self.x, self.y, self.cor)
    def update(self):
        """O vapor sobe lentamente e desaparece com o tempo."""
        self.vida -= 1
        if self.vida <= 0:
            self.draw(self.x, self.y, COR_VAZIO)
            if self.todos_elementos.get((self.x, self.y)) == self:
                del self.todos_elementos[(self.x, self.y)]
            return
            
        if self.verifica_exclusao(self.x, self.y): return
        
        # Lógica de movimento para cima, mais lento que outros gases.
        updates, direcao_horizontal = 0, random.randint(0, 1) * 2 - 1
        if random.random() > 0.5: direcao_horizontal = 0
        while updates < 0.8: # Velocidade de subida mais baixa.
            if self.goto(self.x, self.y - 1): updates += 1
            if self.goto(self.x + direcao_horizontal, self.y): pass
            elif self.goto(self.x - direcao_horizontal, self.y): direcao_horizontal *= -1
            updates += 0.5