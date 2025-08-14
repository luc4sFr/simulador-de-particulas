# Simulador de Partículas em Python

Um simulador de física 2D do tipo "falling sand" feito com Pygame, onde diferentes elementos interagem entre si de formas complexas.

## Como Executar

**1. Requisitos:**
* Python 3
* Pygame

Para instalar a biblioteca Pygame, use o comando:
`pip install pygame`

**2. Execução:**
Para iniciar a simulação, execute o script principal no seu terminal:
`python simulador.py`

## Controles

* **Mouse (Clique Esquerdo):** Desenha o elemento selecionado na tela.
* **Roda do Mouse:** Aumenta ou diminui o tamanho do pincel de desenho.
* **Teclas 0-9:** Selecionam um elemento para desenhar (Areia, Água, Fogo, etc.).
* **Tecla P:** Abre/Fecha o menu para editar as propriedades dos elementos.
* **Tecla ESC:** Fecha o simulador.

## Customização

O comportamento dos elementos é definido no arquivo `config.json` e pode ser modificado de duas maneiras:

* **Editor no Jogo:** Pressione 'P' durante a simulação para editar as propriedades. As alterações são salvas no arquivo `config.json` ao fechar o programa.
* **Editor Web:** Abra o arquivo `index.html` em um navegador para carregar, editar e salvar o `config.json` através de uma interface gráfica.

### Feito com base no código de: [Falling-sand](https://github.com/Antiochian/Falling-Sand)