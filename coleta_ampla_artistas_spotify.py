import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time
import random
import string  # <--- NOVO IMPORT (para a busca por letras 'a', 'b', 'c'...)

# ------------------------
# CONFIGURAÇÃO INICIAL
# ------------------------
# ATENÇÃO: Substitua pelas suas credenciais
CLIENT_ID = "70c610b908d54e42ad164635aba7d732"
CLIENT_SECRET = "2b7952eb17e043f49f0d7ca31b1af81c"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

# ------------------------
# FUNÇÃO PRINCIPAL DE BUSCA (--- ALTERAÇÃO ---)
# ------------------------


def search_artists_by_query(query, country, min_followers=0, max_followers=2000, max_popularity=25):
    """
    Busca artistas no Spotify usando um 'query', 'country' (market),
    e aplica filtros de seguidores e popularidade.

    Esta função agora implementa PAGINAÇÃO para buscar todos os resultados.
    """
    artists_found = []

    try:
        # 1. Faz a primeira busca (primeira página)
        #    Note o uso de 'market=country' para focar a busca nesse país
        results = sp.search(q=query, type='artist', limit=50, market=country)

        # 2. Inicia o loop de paginação
        while results:
            # 3. Itera pelos artistas da PÁGINA ATUAL
            for artist in results['artists']['items']:
                followers = artist['followers']['total']
                popularity = artist['popularity']

                # 4. Aplica seus filtros
                if min_followers <= followers <= max_followers and popularity <= max_popularity:
                    artists_found.append({
                        "name": artist['name'],
                        "id": artist['id'],
                        "followers": followers,
                        "popularity": popularity,
                        "genres": ", ".join(artist['genres']),
                        "url": artist['external_urls']['spotify'],
                        "country_search": country  # País onde a busca foi feita
                    })

            # 5. Lógica de Paginação:
            #    Verifica se o Spotify retornou um link para a 'próxima' página
            if results['artists']['next']:
                try:
                    # O sp.next() usa o link da 'próxima' página para buscar os novos resultados
                    results = sp.next(results['artists'])
                except Exception as e:
                    # Em caso de erro (ex: rate limit), para a busca DESTE termo
                    print(
                        f"  -> Erro ao buscar próxima página para '{query}': {e}. Parando esta busca.")
                    results = None  # Força a saída do loop 'while'
            else:
                # Se não há 'next', saímos do loop
                results = None

    except Exception as e:
        # Erro na busca inicial (ex: termo inválido, problema de autenticação)
        print(f"  ❌ Erro na busca inicial por '{query}' em {country}: {e}")
        return []  # Retorna lista vazia para este termo

    return artists_found

# ------------------------
# GERADOR DE TERMOS DE BUSCA (--- ALTERAÇÃO ---)
# ------------------------


def generate_search_terms():
    """
    Gera uma lista de (termo, país) para uma busca exaustiva.
    """

    # 1. Gêneros principais e sub-gêneros
    genres = [
        "rapper", "trap", "drill", "hip hop", "rnb", "afrobeats",
        "pluggnb", "phonk", "boom bap", "lo-fi rap", "alt-rnb", "neo-soul",
        "uk drill", "ny drill", "indie rap", "conscious hip hop"
    ]

    # 2. Modificadores
    modifiers = ["underground", "indie", "upcoming", "local", "unsigned"]

    # 3. Países (mercados)
    # Adicione mais conforme sua necessidade
    countries = ["US", "BR", "NG", "FR", "MX", "IN", "ZA",
                 "GB", "DE", "CA", "ES", "AU", "CO", "JP", "IT", "PL"]

    search_terms = []  # Lista de tuplas (termo, país)

    # Combina Gêneros x Países
    for country in countries:
        for genre in genres:
            search_terms.append((genre, country))

    # Combina Modificador + Gênero x Países
    for country in countries:
        for mod in modifiers:
            # Ex: "underground hip hop", "indie rapper"
            search_terms.append((f"{mod} rapper", country))
            search_terms.append((f"{mod} trap", country))
            search_terms.append((f"{mod} rnb", country))

    # 4. Estratégia Curinga (Letras) x Países
    # Isso gera muitas buscas, mas é ótimo para "varrer" o banco de dados
    for country in countries:
        for char in string.ascii_lowercase:  # 'a', 'b', 'c', ...
            search_terms.append((char, country))

    # 5. Termos específicos por idioma (Exemplos)
    search_terms.append(("rapper br", "BR"))
    search_terms.append(("trap br", "BR"))
    search_terms.append(("rap nacional", "BR"))
    search_terms.append(("funk consciente", "BR"))
    search_terms.append(("rappeur français", "FR"))
    search_terms.append(("rap francais", "FR"))
    search_terms.append(("rap mexicano", "MX"))
    search_terms.append(("deutschrap", "DE"))

    # Remove duplicatas exatas de (termo, país)
    return list(set(search_terms))

# ------------------------
# SALVAR DADOS EM CSV (--- SEM ALTERAÇÃO ---)
# ------------------------


def save_artist_data(artists, filename="artists_database.csv"):
    """
    Salva uma lista de artistas em um CSV, evitando duplicatas de ID.
    """
    df = pd.DataFrame(artists)
    if df.empty:
        return  # Não faz nada se a lista de artistas estiver vazia

    try:
        # Tenta ler o arquivo CSV existente
        existing_df = pd.read_csv(filename)
        # Concatena o novo DataFrame com o existente
        combined_df = pd.concat([existing_df, df])
    except FileNotFoundError:
        # Se o arquivo não existe, o novo DataFrame é o DataFrame combinado
        combined_df = df

    # Remove duplicatas com base no 'id' do artista, mantendo a primeira ocorrência
    combined_df = combined_df.drop_duplicates(subset=["id"], keep='first')

    # Salva o DataFrame limpo de volta no CSV
    combined_df.to_csv(filename, index=False)

# ------------------------
# LOOP PRINCIPAL (--- ALTERAÇÃO ---)
# ------------------------


def main():
    """
    Loop principal robusto:
    1. Gera os termos de busca.
    2. Embaralha os termos.
    3. Itera por cada termo, busca os artistas e SALVA imediatamente.
    4. Lida com erros por busca, sem travar o script inteiro.
    """

    terms = generate_search_terms()
    total_terms = len(terms)
    print(
        f"✅ Configuração pronta. Total de {total_terms} buscas únicas a realizar.")

    # Embaralhar a lista é bom para não fazer muitas buscas seguidas
    # no mesmo 'market' (país), distribuindo a carga.
    random.shuffle(terms)

    # 'enumerate' nos dá um contador 'i'
    for i, (term, country) in enumerate(terms):

        # Imprime o progresso
        print(f"\n🔍 Buscando ({i+1}/{total_terms}): '{term}' em {country}...")

        try:
            # Chama a função de busca (que agora é paginada)
            artists = search_artists_by_query(term, country)

            if artists:
                print(
                    f"  -> Encontrou {len(artists)} novos artistas. Salvando no CSV...")
                # Salva os resultados desta busca IMEDIATAMENTE
                save_artist_data(artists)
            else:
                print("  -> Nenhum artista encontrado com esses filtros.")

        except Exception as e:
            # Captura erros inesperados durante a busca ou salvamento
            print(f"  ❌ ERRO GRAVE na busca por '{term}' em {country}: {e}")
            print("  Continuando para o próximo termo...")

        # O 'sleep' é CRUCIAL para evitar Rate Limiting (Erro 429) da API
        time.sleep(random.uniform(1.0, 3.0))  # Um delay entre 1 e 3 segundos

    print("\n\n✅ Processo de coleta concluído! O arquivo 'artists_database.csv' está atualizado.")


if __name__ == "__main__":
    main()
