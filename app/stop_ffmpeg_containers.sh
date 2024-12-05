#!/bin/bash

# Obtém todos os containers FFmpeg em execução que estão relacionados ao projeto
containers=$(docker ps --filter "ancestor=ffmpeg_image_name" --format "{{.ID}}")

# Para cada container encontrado, executa o comando para parar
for container in $containers; do
  echo "Parando container FFmpeg ID: $container"
  docker stop $container
done
