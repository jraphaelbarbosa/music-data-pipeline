# Music Data Pipeline (Spotify & YouTube) 🎵

Este repositório contém um pipeline de dados (ETL) em Python focado na coleta e estruturação de informações sobre artistas e produtores musicais.

Este projeto foi construído com um **propósito duplo**:
1.  **Como Projeto Isolado:** Servir como uma ferramenta robusta e independente para qualquer pessoa que precise de um banco de dados unificado sobre artistas (Spotify) e produtores (YouTube).
2.  **Como Módulo Fundacional:** Ser o motor de coleta de dados (a "camada de dados") para um projeto maior de Machine Learning, o **BeatMachAI**.

**Status do Projeto:** 🚀 v1.0 - Funcional 🚀

## O Problema (O Porquê)

Informações sobre o ecossistema musical são fragmentadas. Artistas estão no Spotify, mas os produtores emergentes (especialmente de "type beats") estão no YouTube. Para qualquer análise de dados séria sobre prospecção musical, é preciso unificar essas fontes.

## A Solução (O Quê)

Este repositório contém uma suíte de scripts Python de ETL (Extração, Transformação, Carga) para coletar e estruturar esses dados:

### Scripts Incluídos

1.  **`coleta_ampla_artistas_spotify.py`**
    * **O que faz:** Conecta-se à API do Spotify e coleta uma lista abrangente de artistas baseada em uma ampla gama de gêneros musicais.
    * **Resultado:** Gera um arquivo `artists_database.csv` com artistas-alvo.

2.  **`coleta_focada_rap_rnb_artistas_spotify.py`**
    * **O que faz:** Uma versão focada do coletor, otimizada para buscar artistas especificamente dentro dos nichos de Rap, R&B, Trap e gêneros relacionados.
    * **Resultado:** Gera um arquivo `artists_database_rap_rnb.csv` com uma lista filtrada de artistas de alta relevância.

3.  **`coleta_produtores_youtube.py`**
    * **O que faz:** Conecta-se à API do YouTube para encontrar vídeos de "type beat", extrai os nomes dos produtores e calcula um "score de popularidade" baseado nas visualizações agregadas.
    * **Resultado:** Gera um arquivo `produtores_youtube_filtrados.json` com uma lista de produtores filtrados (no "ponto ideal" de popularidade 60-80%), prontos para análise.

## 🛠️ Tecnologias Utilizadas

* **Python 3**
* **Spotipy:** Cliente Python para a API do Spotify.
* **Google API Client:** Cliente Python para a API v3 do YouTube.
* **Dotenv:** Para gerenciamento de chaves de API.

## 🏁 Como Executar

1.  Clone o repositório:
    ```bash
    git clone [https://github.com/seu-usuario/music-data-pipeline.git](https://github.com/jraphaelbarbosa/music-data-pipeline.git)
    cd music-data-pipeline
    ```
2.  Crie e ative um ambiente virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```
3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
4.  Crie um arquivo `.env` na raiz do projeto e adicione suas chaves:
    ```
    SPOTIPY_CLIENT_ID='SUA_CHAVE_SPOTIFY'
    SPOTIPY_CLIENT_SECRET='SEU_SEGREDO_SPOTIFY'
    YOUTUBE_API_KEY='SUA_CHAVE_YOUTUBE'
    ```
5.  Execute o script desejado:
    ```bash
    python coleta_ampla_artistas_spotify.py
    ```

---

## 🔗 Relação com o BeatMachAI (O Contexto Principal)

Este pipeline é o primeiro módulo essencial do **BeatMachAI**, um sistema de recomendação de música que estou desenvolvendo.

**O intuito do BeatMachAI é:**
Ajudar produtores musicais a encontrar os artistas certos para seus beats. Ele funcionará da seguinte forma:

1.  Um produtor fará o upload do seu beat na aplicação.
2.  Usando análise de áudio (com `librosa`) e Machine Learning, o BeatMachAI irá analisar a "sonoridade" (BPM, energia, "dançabilidade", etc.) do beat.
3.  Ele então irá comparar esse perfil sonoro com o perfil dos artistas e produtores que foram coletados por **este pipeline**.
4.  O resultado será uma lista de "matches" perfeitos, conectando o produtor ao artista certo.

Este `music-data-pipeline` tem a missão crítica de fornecer os dados limpos e estruturados que alimentarão os modelos de recomendação do BeatMachAI.

## 🗺️ Roadmap (Próximos Passos do Pipeline)

Este pipeline continuará evoluindo para fornecer dados ainda mais ricos. A próxima grande funcionalidade planejada é:

* [ ] **Análise de Comentários do YouTube:** Desenvolver um script para analisar os comentários de vídeos de "type beat" usando NLP (Processamento de Linguagem Natural) para identificar artistas independentes que demonstram interesse ativo (ex: "mano, me manda esse beat", "posso usar?"), criando uma lista de leads ultra-qualificados.