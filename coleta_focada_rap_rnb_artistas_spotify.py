import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time
import random
import string

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
# PARÂMETROS DE FILTRO (--- NOVO ---)
# ------------------------
# Definimos nossos filtros aqui para fácil ajuste
FILTERS_CONFIG = {
    'min_popularity': 1,     # Mínimo 1 (para garantir que estão ativos)
    'max_popularity': 15,    # Máximo 15 (seu alvo "underground")
    'max_followers': 2000,   # Máximo de seguidores

    # Lista de gêneros que, se encontrados, farão o artista ser IGNORADO
    # Usamos strings parciais (ex: 'house' bloqueia 'deep house', 'afro house', etc.)
    'forbidden_genres': [
        'house', 'afrobeat', 'afrobeats', 'edm', 'techno',
        'electro', 'pop', 'indie pop', 'brazilian pop', 'funk carioca'
        # Adicione mais gêneros que você queira excluir explicitamente
    ]
}

# ------------------------
# FUNÇÃO PRINCIPAL DE BUSCA (--- ALTERAÇÃO ---)
# ------------------------


def search_artists_by_query(query, country, filters):
    """
    Busca artistas no Spotify usando 'query', 'country' (market),
    e aplica filtros RÍGIDOS de popularidade, seguidores E exclusão de gênero.
    """
    artists_found = []

    try:
        results = sp.search(q=query, type='artist', limit=50, market=country)

        while results:
            for artist in results['artists']['items']:
                popularity = artist['popularity']
                followers = artist['followers']['total']
                artist_genres = artist['genres']  # Esta é uma lista de strings

                # 1. Aplicar filtros numéricos (pop e followers)
                if not (filters['min_popularity'] <= popularity <= filters['max_popularity'] and
                        followers <= filters['max_followers']):
                    continue  # Pula este artista (não bate com os números)

                # 2. Aplicar filtro de EXCLUSÃO de gênero (--- NOVO ---)
                is_forbidden = False
                for genre_str in artist_genres:
                    # Usamos .lower() para garantir a correspondência
                    genre_lower = genre_str.lower()
                    for forbidden in filters['forbidden_genres']:
                        if forbidden in genre_lower:
                            is_forbidden = True
                            break  # Encontrou um gênero proibido, para de verificar
                    if is_forbidden:
                        break  # Pula para fora do loop de gêneros

                if is_forbidden:
                    continue  # Pula este artista (contém gênero proibido)

                # 3. Se passou em AMBOS os filtros, adicione à lista
                artists_found.append({
                    "name": artist['name'],
                    "id": artist['id'],
                    "followers": followers,
                    "popularity": popularity,
                    "genres": ", ".join(artist_genres),
                    "url": artist['external_urls']['spotify'],
                    "country_search": country
                })

            # Lógica de Paginação
            if results['artists']['next']:
                try:
                    results = sp.next(results['artists'])
                except Exception as e:
                    print(
                        f"  -> Erro ao buscar próxima página para '{query}': {e}. Parando esta busca.")
                    results = None
            else:
                results = None

    except Exception as e:
        print(f"  ❌ Erro na busca inicial por '{query}' em {country}: {e}")
        return []

    return artists_found

# ------------------------
# GERADOR DE TERMOS DE BUSCA (--- ALTERAÇÃO ---)
# ------------------------


def generate_search_terms():
    """
    Gera uma lista de (termo, país) focada em Rap, Trap, R&B e subgêneros.
    """

    # Gêneros FOCADOS (Rap, R&B, Soul)
    genres = [
        "rapper", "trap", "drill", "hip hop", "rnb",
        "trapsoul", "neo soul", "uk drill", "boom bap",
        "lo-fi rap", "alt-rnb", "indie rap", "conscious hip hop",
        "underground hip hop", "indie rapper", "upcoming trap artist"
    ]

    # --- ALTERAÇÃO AQUI: Lista de países atualizada ---
    # Países (mercados) com cenas de Rap/R&B/Trap relevantes
    countries = [
        "US",  # Estados Unidos
        "BR",  # Brasil
        "GB",  # Reino Unido (UK)
        "FR",  # França
        "DE",  # Alemanha
        "CA",  # Canadá
        "AU",  # Austrália
        "NG",  # Nigéria (Filtro de exclusão vai limpar os não-rap)
        "ZA",  # África do Sul
        "NL",  # Holanda
        "ES",  # Espanha
        "IT",  # Itália
        "MX",  # México
        "CO",  # Colômbia
        "JP",  # Japão
        "KR",  # Coreia do Sul
        "NZ",  # Nova Zelândia
        "IE",  # Irlanda
        "SE",  # Suécia
        "PL"  # Polônia
    ]

    search_terms = []

    # Combina Gêneros Focados x Países
    for country in countries:
        for genre in genres:
            search_terms.append((genre, country))

    # Estratégia Curinga (Letras) x Países
    for country in countries:
        for char in string.ascii_lowercase:  # 'a', 'b', 'c', ...
            search_terms.append((char, country))

    # Termos específicos por idioma (Exemplos)
    search_terms.append(("rapper br", "BR"))
    search_terms.append(("trap br", "BR"))
    search_terms.append(("rap nacional", "BR"))
    search_terms.append(("rappeur français", "FR"))
    search_terms.append(("rap francais", "FR"))
    search_terms.append(("rap mexicano", "MX"))
    search_terms.append(("deutschrap", "DE"))

    return list(set(search_terms))

# ------------------------
# SALVAR DADOS EM CSV (Sem alteração na lógica)
# ------------------------


def save_artist_data(artists, filename="artists_database.csv"):
    df = pd.DataFrame(artists)
    if df.empty:
        return

    try:
        existing_df = pd.read_csv(filename)
        combined_df = pd.concat([existing_df, df])
    except FileNotFoundError:
        combined_df = df

    combined_df = combined_df.drop_duplicates(subset=["id"], keep='first')
    combined_df.to_csv(filename, index=False)

# ------------------------
# LOOP PRINCIPAL (--- ALTERAÇÃO ---)
# ------------------------


def main():

    # --- NOVO ---
    # Define o nome do arquivo para esta coleta específica
    OUTPUT_FILENAME = "artists_database_rap_rnb.csv"

    print("Iniciando coleta focada (Rap/R&B/Soul)...")
    print(f"Resultados serão salvos em: {OUTPUT_FILENAME}")
    print(
        f"Filtros aplicados: Popularidade ({FILTERS_CONFIG['min_popularity']}-{FILTERS_CONFIG['max_popularity']}), Seguidores (Max: {FILTERS_CONFIG['max_followers']})")
    print(f"Gêneros proibidos: {FILTERS_CONFIG['forbidden_genres']}")

    terms = generate_search_terms()
    total_terms = len(terms)
    print(f"Total de {total_terms} buscas únicas a realizar.")

    random.shuffle(terms)

    for i, (term, country) in enumerate(terms):

        print(f"\n🔍 Buscando ({i+1}/{total_terms}): '{term}' em {country}...")

        try:
            # Passa os filtros para a função de busca
            artists = search_artists_by_query(term, country, FILTERS_CONFIG)

            if artists:
                print(
                    f"  -> Encontrou {len(artists)} novos artistas. Salvando no CSV...")
                # Salva no arquivo específico
                save_artist_data(artists, filename=OUTPUT_FILENAME)
            else:
                print("  -> Nenhum artista encontrado com esses filtros.")

        except Exception as e:
            print(f"  ❌ ERRO GRAVE na busca por '{term}' em {country}: {e}")
            print("  Continuando para o próximo termo...")

        # Delay para evitar Rate Limiting (Erro 429) da API
        time.sleep(random.uniform(1.0, 3.0))

    print(
        f"\n\n✅ Processo de coleta focado concluído! O arquivo '{OUTPUT_FILENAME}' está atualizado.")


if __name__ == "__main__":
    main()
