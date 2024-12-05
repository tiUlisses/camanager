#!/bin/bash

# Parar o script ao encontrar erros
set -e

# Definir o nome das imagens Docker
APP_IMAGE_NAME="app_image"
NGINX_IMAGE_NAME="nginx_image"
FFMPEG_IMAGE_NAME="ffmpeg"

echo "===== Construindo as imagens Docker ====="

# Construir a imagem Docker da aplicação
docker build -t $APP_IMAGE_NAME -f Dockerfile .

# Construir a imagem Docker do Nginx
docker build -t $NGINX_IMAGE_NAME -f Dockerfile.nginx .

# Construir a imagem Docker do FFmpeg
docker build -t $FFMPEG_IMAGE_NAME -f Dockerfile.ffmpeg .

echo "===== Imagens construídas com sucesso ====="

echo "===== Iniciando o Docker Compose ====="

# Rodar o docker-compose
docker-compose up

echo "===== Aplicação está rodando ====="

