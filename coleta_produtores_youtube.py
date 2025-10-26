#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
coleta_produtores_youtube.py (v1.0 - Focado em Produtores)

Este script é um pipeline de dados focado em descobrir produtores de "type beat"
no YouTube e classificá-los por popularidade.

O fluxo de trabalho é:
1. Busca vídeos de "type beat" no YouTube (usando cache).
2. Coleta descrições e contagem de views de cada vídeo.
3. Extrai nomes de produtores das descrições (ex: "prod. by", beatstars.com).
4. Agrega as visualizações de cada produtor para criar um ranking de popularidade.
5. Filtra esse ranking, mantendo apenas os produtores na "classe média-alta"
    (definido como entre o 60º e 80º percentil de popularidade).
6. Salva a lista final de PRODUTORES e suas pontuações em um arquivo JSON.
"""

import os
import re
import json
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from collections import defaultdict
import traceback

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO DAS CHAVES DE API ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# --- CONFIGURAÇÃO DA BUSCA ---
TERMOS_BUSCA = [
    # Gêneros Principais
    "trap type beat", "trapsoul type beat", "r&b type beat",
    "uk drill type beat", "drill type beat", "ny drill type beat",
    "lofi type beat", "dark trap type beat", "neo soul type beat",
    "chill drill type beat", "jazz type beat",

    # Artistas (Trap / Drill)
    "drake type beat", "travis scott type beat", "future type beat",
    "gunna type beat", "lil baby type beat", "don toliver type beat",
    "21 savage type beat", "pop smoke type beat", "central cee type beat",
    "guetts type beat", "skepta type beat", "sainte type beat",
    "kendrick lamar type beat", "playboi carti type beat",

    # Artistas (R&B / Moody)
    "partynextdoor type beat", "6lack type beat", "bryson tiller type beat",
    "the weeknd type beat", "brent faiyaz type beat", "sza type beat",
    "summer walker type beat", "ojerime type beat", "jorja smith type beat",
    "giveon type beat"
]

MAX_VIDEOS_POR_TERMO = 25
ARQUIVO_SAIDA_JSON = "produtores_youtube_filtrados.json"
CACHE_FILE = "youtube_cache.json"
CACHE_EXPIRATION_SECONDS = 86400  # 24 horas


def buscar_videos_youtube(youtube_client, termos_busca):
    """
    Busca vídeos no YouTube com CACHE e retorna os OBJETOS de vídeo.
    """
    # Tenta carregar do cache primeiro
    if os.path.exists(CACHE_FILE):
        file_mod_time = os.path.getmtime(CACHE_FILE)
        if (time.time() - file_mod_time) < CACHE_EXPIRATION_SECONDS:
            print(f"Carregando resultados do cache ('{CACHE_FILE}')...")
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)

    print(
        f"Iniciando busca no YouTube por {len(termos_busca)} termos (sem cache válido)...")
    video_items_completos = []
    video_ids = set()
    quota_exceeded = False

    for termo in termos_busca:
        if quota_exceeded:
            break
        try:
            print(f"Buscando por: '{termo}'")
            search_request = youtube_client.search().list(
                q=termo,
                part="id",
                type="video",
                order="viewCount",
                maxResults=MAX_VIDEOS_POR_TERMO
            )
            search_response = search_request.execute()
            ids_encontrados = {item['id']['videoId']
                               for item in search_response.get("items", [])}
            video_ids.update(ids_encontrados)
            time.sleep(0.5)

        except HttpError as e:
            if 'quotaExceeded' in str(e):
                print(
                    f"ERRO DE COTA: A cota da API do YouTube foi excedida. Continuando com os {len(video_ids)} IDs já coletados.")
                quota_exceeded = True
            else:
                print(f"Erro na busca do YouTube para '{termo}': {e}")
            continue

    video_ids_list = list(video_ids)
    print(
        f"Total de {len(video_ids_list)} IDs de vídeo únicos encontrados. Buscando detalhes...")

    if not video_ids_list:
        return []

    # Busca os detalhes em lotes
    batch_size = 50
    for i in range(0, len(video_ids_list), batch_size):
        if quota_exceeded and i > 0:
            break
        try:
            batch_ids = video_ids_list[i:i+batch_size]
            video_request = youtube_client.videos().list(
                part="snippet,statistics",
                id=",".join(batch_ids)
            )
            video_response = video_request.execute()
            video_items_completos.extend(video_response.get("items", []))

        except HttpError as e:
            if 'quotaExceeded' in str(e):
                print(
                    "ERRO DE COTA: A cota da API do YouTube foi excedida durante a busca de detalhes.")
                quota_exceeded = True
            else:
                print(f"Erro ao buscar detalhes dos vídeos: {e}")
            continue

    print(
        f"Total de {len(video_items_completos)} detalhes de vídeo coletados.")

    # Salva os resultados no cache
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(video_items_completos, f, indent=4, ensure_ascii=False)
        print(f"Resultados da busca salvos em '{CACHE_FILE}'.")
    except IOError as e:
        print(f"Erro ao salvar o arquivo de cache: {e}")

    return video_items_completos


def extrair_e_filtrar_produtores(video_items):
    """
    Usa RegEx para encontrar produtores e os filtra por popularidade (view count).
    Retorna uma lista de dicionários com nome e score de views.
    """
    print("Extraindo nomes de produtores e calculando popularidade...")
    producer_regex = re.compile(
        r"(?:prod\.\s*by|prod\.)\s*[:\-]?\s*([^\n\r(]+)|"
        r"beatstars\.com/([a-zA-Z0-9_-]+)",
        re.IGNORECASE
    )
    produtor_view_counts = defaultdict(int)

    for item in video_items:
        desc = item['snippet']['description']
        view_count = int(item['statistics'].get('viewCount', 0))

        matches = producer_regex.finditer(desc)
        for match in matches:
            nome_sujo = match.group(1) or match.group(2)
            if nome_sujo:
                nome_limpo = re.sub(r"[@\(\)\[\]\{\}]", "", nome_sujo).strip()
                if len(nome_limpo) > 3 and "type beat" not in nome_limpo.lower():
                    produtor_view_counts[nome_limpo] += view_count

    if not produtor_view_counts:
        print("Nenhum produtor encontrado com os critérios de RegEx.")
        return []

    print(
        f"Encontrados {len(produtor_view_counts)} produtores únicos. Calculando ranking...")

    # --- FILTRO DE POPULARIDADE (60º-80º Percentil) ---
    sorted_producers = sorted(produtor_view_counts.items(),
                              key=lambda item: item[1],
                              reverse=True)
    total_producers = len(sorted_producers)

    # Calcula os índices para a "margem" (entre 60% e 80% do ranking)
    percentil_80_index = int(total_producers * 0.20)
    percentil_60_index = int(total_producers * 0.40)

    # Pega a "fatia" de produtores entre esses índices
    produtores_filtrados_tuplas = sorted_producers[percentil_80_index:percentil_60_index]

    # Converte para um formato JSON mais legível
    produtores_filtrados_json = [
        {"produtor": nome, "score_popularidade_views": views}
        for nome, views in produtores_filtrados_tuplas
    ]

    print(f"Ranking: {total_producers} produtores no total.")
    print(f"Filtrando para a 'margem 60-80'.")
    print(
        f"Mantendo {len(produtores_filtrados_json)} produtores na lista final.")

    return produtores_filtrados_json


def salvar_resultados(produtores, arquivo_saida):
    """
    Salva a lista final de PRODUTORES em um arquivo JSON.
    """
    print(f"Salvando {len(produtores)} produtores em '{arquivo_saida}'...")
    try:
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(produtores, f, indent=4, ensure_ascii=False)
        print("Arquivo salvo com sucesso!")
    except IOError as e:
        print(f"Erro ao salvar arquivo: {e}")


def main():
    """
    Função principal para orquestrar o processo.
    """
    print("Iniciando script 'coleta_produtores_youtube.py' (v1.0)...")

    if not YOUTUBE_API_KEY:
        print("="*50)
        print("ERRO: Por favor, configure sua chave 'YOUTUBE_API_KEY' no arquivo .env.")
        print("="*50)
        return

    try:
        youtube_client = build("youtube", "v3",
                               developerKey=YOUTUBE_API_KEY,
                               cache_discovery=False,
                               static_discovery=False)
    except Exception as e:
        print(f"Erro ao inicializar cliente da API do YouTube: {e}")
        print(traceback.format_exc())
        return

    # Etapa 1: Buscar vídeos (com stats)
    video_items = buscar_videos_youtube(youtube_client, TERMOS_BUSCA)
    if not video_items:
        print("Nenhum vídeo encontrado. Encerrando.")
        return

    # Etapa 2: Extrair e FILTRAR produtores por popularidade
    produtores_filtrados = extrair_e_filtrar_produtores(video_items)
    if not produtores_filtrados:
        print("Nenhum produtor passou no filtro de popularidade. Encerrando.")
        return

    # Etapa 3: Salvar resultados
    salvar_resultados(produtores_filtrados, ARQUIVO_SAIDA_JSON)

    print("Processo concluído com sucesso.")


if __name__ == "__main__":
    main()
