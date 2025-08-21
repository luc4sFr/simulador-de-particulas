import sys
import math
from simulador_elementos import *
import simulador_elementos

# --- FUNÇÕES AUXILIARES ---
def salvar_propriedades_para_json(caminho_arquivo='config.json'):
    with open(caminho_arquivo, 'w') as f:
        json.dump(simulador_elementos.propriedades_elementos, f, indent=2)
    print(f"Propriedades salvas em {caminho_arquivo}")

def verifica_posicao_livre(x, y):
    return todos_elementos.get((x, y)) is None

def desenhar_elemento(tipo, x, y, raio):
    """Desenha um círculo de um tipo de elemento na grade, centrado em (x, y)."""
    raio = int(raio)
    for dx in range(-raio, raio + 1):
        for dy in range(-raio, raio + 1):
            if dx*dx + dy*dy <= raio*raio:
                nx, ny = x + dx, y + dy
                if verifica_posicao_livre(nx, ny):
                    todos_elementos[(nx, ny)] = tipo(nx, ny, todos_elementos, superficie)

# --- VARIÁVEIS GLOBAIS DO MENU ---
menu_scroll_offset = 0 # Armazena o deslocamento vertical (rolagem) do menu.
total_content_height = 0 # Armazena a altura total do conteúdo do menu para calcular a rolagem.

def desenhar_menu_propriedades(tela, fonte_titulo, fonte_normal):
    """Desenha o menu de edição de propriedades na tela."""
    global menu_scroll_offset, total_content_height

    # Define a área principal do menu.
    menu_rect = pygame.Rect(50, 50, 480, 700)
    # A área visível onde o conteúdo pode rolar (viewport).
    viewport_rect = menu_rect.inflate(0, -80)
    viewport_rect.top += 40

    # Desenha o fundo semitransparente e a borda do menu.
    fundo_menu = pygame.Surface((menu_rect.width, menu_rect.height), pygame.SRCALPHA)
    fundo_menu.fill((30, 30, 30, 230))
    tela.blit(fundo_menu, (menu_rect.x, menu_rect.y))
    pygame.draw.rect(tela, (200, 200, 200), menu_rect, 2)

    # Dicionário para armazenar as áreas clicáveis (botões) e suas identificações.
    botoes_clicaveis = {}
    
    # Desenha as partes estáticas do menu (título e botão salvar).
    titulo_render = fonte_titulo.render("Editor de Propriedades (P)", True, (255, 255, 255))
    tela.blit(titulo_render, (menu_rect.x + 10, menu_rect.y + 15))
    btn_salvar_rect = pygame.Rect(menu_rect.right - 110, menu_rect.top + 10, 100, 30)
    pygame.draw.rect(tela, (60, 180, 240), btn_salvar_rect)
    pygame.draw.rect(tela, (255, 255, 255), btn_salvar_rect, 2)
    tela.blit(fonte_normal.render("Salvar", True, (255, 255, 255)), (btn_salvar_rect.x + 25, btn_salvar_rect.y + 7))
    botoes_clicaveis[("acao", "salvar")] = btn_salvar_rect

    # --- LÓGICA DE ROLAGEM E DESENHO DO CONTEÚDO DINÂMICO ---
    
    # Define uma área de clipping para que o conteúdo não seja desenhado fora do viewport.
    tela.set_clip(viewport_rect)
    
    y_pos_inicial = viewport_rect.top
    y_offset = y_pos_inicial + menu_scroll_offset # A posição Y inicial do conteúdo é ajustada pela rolagem.
    
    # Itera sobre cada elemento e suas propriedades no dicionário carregado.
    for elemento, props in simulador_elementos.propriedades_elementos.items():
        elemento_render = fonte_titulo.render(f"--- {elemento} ---", True, (255, 255, 0))
        tela.blit(elemento_render, (menu_rect.x + 15, y_offset))
        y_offset += 35

        for prop_nome, valor in props.items():
            # Caso especial para a propriedade "cor".
            if prop_nome == "cor":
                cor_atual = tuple(valor)
                # Desenha uma amostra da cor.
                pygame.draw.rect(tela, cor_atual, (menu_rect.x + 20, y_offset, 50, 25))
                pygame.draw.rect(tela, (255,255,255), (menu_rect.x + 20, y_offset, 50, 25), 1)
                y_offset += 35
                
                # Cria controles +/- para cada canal de cor (R, G, B).
                for i, canal in enumerate(["R", "G", "B"]):
                    texto_canal = f"{canal}: {valor[i]}"
                    tela.blit(fonte_normal.render(texto_canal, True, (255,255,255)), (menu_rect.x + 40, y_offset))
                    btn_menos_rect = pygame.Rect(menu_rect.x + 350, y_offset, 25, 25)
                    btn_mais_rect = pygame.Rect(menu_rect.x + 390, y_offset, 25, 25)
                    pygame.draw.rect(tela, (200, 50, 50), btn_menos_rect)
                    tela.blit(fonte_normal.render("-", True, (255,255,255)), (btn_menos_rect.x + 8, btn_menos_rect.y + 4))
                    pygame.draw.rect(tela, (50, 200, 50), btn_mais_rect)
                    tela.blit(fonte_normal.render("+", True, (255,255,255)), (btn_mais_rect.x + 7, btn_mais_rect.y + 4))
                    botoes_clicaveis[(elemento, prop_nome, i, "menos")] = btn_menos_rect
                    botoes_clicaveis[(elemento, prop_nome, i, "mais")] = btn_mais_rect
                    y_offset += 35
            else: # Para todas as outras propriedades (numéricas).
                texto_prop = f"{prop_nome.replace('_', ' ').title()}: {valor:.2f}" if isinstance(valor, float) else f"{prop_nome.replace('_', ' ').title()}: {valor}"
                prop_render = fonte_normal.render(texto_prop, True, (255, 255, 255))
                tela.blit(prop_render, (menu_rect.x + 20, y_offset))
                # Cria controles +/- para a propriedade.
                btn_menos_rect = pygame.Rect(menu_rect.x + 350, y_offset, 25, 25)
                btn_mais_rect = pygame.Rect(menu_rect.x + 390, y_offset, 25, 25)
                pygame.draw.rect(tela, (200, 50, 50), btn_menos_rect)
                tela.blit(fonte_normal.render("-", True, (255, 255, 255)), (btn_menos_rect.x + 8, btn_menos_rect.y + 4))
                pygame.draw.rect(tela, (50, 200, 50), btn_mais_rect)
                tela.blit(fonte_normal.render("+", True, (255, 255, 255)), (btn_mais_rect.x + 7, btn_mais_rect.y + 4))
                botoes_clicaveis[(elemento, prop_nome, "menos")] = btn_menos_rect
                botoes_clicaveis[(elemento, prop_nome, "mais")] = btn_mais_rect
                y_offset += 40
        y_offset += 15

    # Reseta o clipping para permitir o desenho no resto da tela.
    tela.set_clip(None)

    # Calcula a altura total do conteúdo para a lógica da barra de rolagem.
    total_content_height = y_offset - (y_pos_inicial + menu_scroll_offset)

    # Desenha a barra de rolagem apenas se o conteúdo for maior que a área visível.
    if total_content_height > viewport_rect.height:
        scrollbar_bg_rect = pygame.Rect(menu_rect.right - 12, viewport_rect.top, 8, viewport_rect.height)
        pygame.draw.rect(tela, (50, 50, 50), scrollbar_bg_rect, border_radius=4)
        
        # Calcula a altura e posição da alça da barra de rolagem.
        handle_height = viewport_rect.height * (viewport_rect.height / total_content_height)
        handle_height = max(20, handle_height) # Altura mínima para a alça.
        
        scroll_ratio = -menu_scroll_offset / (total_content_height - viewport_rect.height)
        handle_y = viewport_rect.top + (viewport_rect.height - handle_height) * scroll_ratio
        
        scrollbar_handle_rect = pygame.Rect(menu_rect.right - 12, handle_y, 8, handle_height)
        pygame.draw.rect(tela, (150, 150, 150), scrollbar_handle_rect, border_radius=4)

    return botoes_clicaveis


# --- INICIALIZAÇÃO DO PYGAME ---

pygame.init()
# Define um tamanho fixo para a janela, em vez de tela cheia.
TelaX, TelaY = 1280, 720
# Define as dimensões da grade no módulo de elementos.
definir_dimensoes_tela(TelaX // ESCALA, TelaY // ESCALA)
# Cria a janela principal que pode ser redimensionada.
tela = pygame.display.set_mode((TelaX, TelaY), pygame.RESIZABLE) # Adicionada a flag RESIZABLE
pygame.display.set_caption("Simulador de Elementos")

try:
    fundo = pygame.image.load("fundo2.jpg").convert()
    fundo_redimensionado = pygame.transform.scale(fundo, (TelaX, TelaY))
except pygame.error as e:
    print(f"Não foi possível carregar a imagem de fundo: {e}")
    fundo = None 

superficie = tela.copy()
clock = pygame.time.Clock()


# --- VARIÁVEIS DO SIMULADOR ---

elemento_ativo = Metal  # Elemento selecionado para desenhar.
tamanho_caneta = 3  # Raio do pincel de desenho.
todos_elementos[(None, None)] = Vazio(todos_elementos, superficie) # Adiciona um elemento Vazio para evitar erros de chave.
menu_propriedades_visivel = False # Controla a visibilidade do menu.

fonte_interface = pygame.font.SysFont(None, 24)
fonte_menu_titulo = pygame.font.SysFont(None, 32)
fonte_menu_normal = pygame.font.SysFont(None, 28)

last_mx, last_my = None, None # Armazena a última posição do mouse para desenhar linhas contínuas.
mouse_pressionado = False # Estado do botão esquerdo do mouse.

def desenhar_interface_principal():
    """Desenha as informações da interface principal (elementos, caneta, etc.)."""
    opcoes = [
        "1 - Metal", 
        "2 - Agua", 
        "3 - Areia", 
        "4 - Acido", 
        "5 - Gas",
        "6 - Lava", 
        "7 - Fogo", 
        "8 - Vidro", 
        "9 - Madeira", 
        "0 - Planta", 
        f"Caneta: {tamanho_caneta} - {elemento_ativo.__name__}", 
        "P - Propriedades"
    ]
    for i, texto in enumerate(opcoes):
        render = fonte_interface.render(texto, True, (0, 0, 0))
        tela.blit(render, (10, 10 + i * 24))

# --- LOOP PRINCIPAL ---
rodando = True
botoes_menu_clicaveis = {} # Armazena os botões do menu retornados pela função de desenho.

while rodando:
    clock.tick(FPS)
    mx, my = pygame.mouse.get_pos()

    # --- PROCESSAMENTO DE EVENTOS ---
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        elif evento.type == pygame.VIDEORESIZE:
            TelaX, TelaY = evento.size

            tela = pygame.display.set_mode((TelaX, TelaY), pygame.RESIZABLE) # Recria a tela
            superficie = pygame.Surface((TelaX, TelaY), pygame.SRCALPHA)

            if fundo:
                fundo_redimensionado = pygame.transform.scale(fundo, (TelaX, TelaY))
                
            definir_dimensoes_tela(TelaX // ESCALA, TelaY // ESCALA)
            todos_elementos.clear()
        
        elif evento.type == pygame.MOUSEWHEEL:
            # Se o menu estiver visível, a roda do mouse controla a rolagem.
            if menu_propriedades_visivel:
                menu_scroll_offset += evento.y * 25
                viewport_height = 620 # Altura visível do conteúdo do menu.
                # Limita a rolagem para não ultrapassar os limites do conteúdo.
                if total_content_height > viewport_height:
                    max_scroll = total_content_height - viewport_height
                    menu_scroll_offset = max(-max_scroll, min(0, menu_scroll_offset))
                else:
                    menu_scroll_offset = 0
            # Senão, a roda do mouse altera o tamanho da caneta.
            else:
                tamanho_caneta = max(1, tamanho_caneta + evento.y)
        
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                rodando = False
            elif evento.key == pygame.K_p: # Tecla 'P' para alternar o menu.
                menu_propriedades_visivel = not menu_propriedades_visivel
                menu_scroll_offset = 0 # Reseta a rolagem ao abrir.
        
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1: # Clique com botão esquerdo
            if menu_propriedades_visivel:
                # Verifica se o clique foi em algum botão dentro do menu.
                viewport_rect_check = pygame.Rect(50, 90, 480, 620) # Área clicável do menu.
                for chave, rect in botoes_menu_clicaveis.items():
                    if rect.collidepoint(evento.pos) and viewport_rect_check.collidepoint(evento.pos):
                        # Lógica para o botão de salvar.
                        if chave[0] == "acao" and chave[1] == "salvar":
                            salvar_propriedades_para_json()
                        # Lógica para os botões de cor.
                        elif chave[1] == "cor":
                            elemento, _, indice_cor, tipo_btn = chave
                            passo = 1
                            valor_atual = simulador_elementos.propriedades_elementos[elemento]["cor"][indice_cor]
                            novo_valor = valor_atual + passo if tipo_btn == "mais" else valor_atual - passo
                            # Garante que o valor da cor permaneça entre 0 e 255.
                            simulador_elementos.propriedades_elementos[elemento]["cor"][indice_cor] = max(0, min(255, novo_valor))
                        # Lógica para outros botões de propriedades numéricas.
                        else:
                            elemento, prop_nome, tipo_btn = chave
                            valor_atual = simulador_elementos.propriedades_elementos[elemento][prop_nome]
                            passo = 0.01 if isinstance(valor_atual, float) else 1
                            novo_valor = valor_atual + passo if tipo_btn == "mais" else valor_atual - passo
                            # Garante que o valor não seja negativo.
                            if isinstance(valor_atual, float):
                                simulador_elementos.propriedades_elementos[elemento][prop_nome] = round(max(0.0, novo_valor), 2)
                            else:
                                simulador_elementos.propriedades_elementos[elemento][prop_nome] = max(0, int(novo_valor))
            else:
                # Se o menu não estiver visível, o clique ativa o modo de desenho.
                mouse_pressionado = True
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            mouse_pressionado = False
            last_mx, last_my = None, None # Reseta a última posição do mouse.

    teclas = pygame.key.get_pressed()
    
    # --- LÓGICA DE ATUALIZAÇÃO DA SIMULAÇÃO ---
    if not menu_propriedades_visivel:
        # Se o mouse estiver pressionado, desenha elementos.
        if mouse_pressionado:
            if last_mx is None: last_mx, last_my = mx, my
            dx, dy = mx - last_mx, my - last_my
            distancia = math.sqrt(dx**2 + dy**2)
            # Interpola a posição do mouse para criar linhas contínuas em vez de pontos.
            if distancia > 0:
                passos_x, passos_y = dx / distancia, dy / distancia
                for i in range(int(distancia)):
                    inter_x = int(last_mx + passos_x * i)
                    inter_y = int(last_my + passos_y * i)
                    desenhar_elemento(elemento_ativo, inter_x // ESCALA, inter_y // ESCALA, tamanho_caneta)
            desenhar_elemento(elemento_ativo, mx // ESCALA, my // ESCALA, tamanho_caneta)
            last_mx, last_my = mx, my

        # Seleciona o elemento ativo com base nas teclas numéricas.
        if teclas[pygame.K_1]: elemento_ativo = Metal
        if teclas[pygame.K_2]: elemento_ativo = Agua
        if teclas[pygame.K_3]: elemento_ativo = Areia
        if teclas[pygame.K_4]: elemento_ativo = Acido
        if teclas[pygame.K_5]: elemento_ativo = Gas
        if teclas[pygame.K_6]: elemento_ativo = Lava
        if teclas[pygame.K_7]: elemento_ativo = Fogo
        if teclas[pygame.K_8]: elemento_ativo = Vidro
        if teclas[pygame.K_9]: elemento_ativo = Madeira
        if teclas[pygame.K_0]: elemento_ativo = Planta
        
        # Chama o metodo `update` de cada partícula na simulação.
        # Usa `list(todos_elementos.keys())` para criar uma cópia,
        # pois o dicionário pode ser modificado durante a iteração.
        for pos in list(todos_elementos.keys()):
            try:
                todos_elementos[pos].update()
            except KeyError:
                pass

    if fundo:
        tela.blit(fundo_redimensionado, (0, 0))

    # --- DESENHO NA TELA ---
    # Copia a superfície da simulação para a tela principal.
    tela.blit(superficie, (0, 0))

    if menu_propriedades_visivel:
        botoes_menu_clicaveis = desenhar_menu_propriedades(tela, fonte_menu_titulo, fonte_menu_normal)
    else:
        desenhar_interface_principal()
        pygame.draw.circle(tela, (255, 255, 255), (mx, my), tamanho_caneta * ESCALA, 1)

    pygame.display.update()

salvar_propriedades_para_json()
pygame.quit()
sys.exit()