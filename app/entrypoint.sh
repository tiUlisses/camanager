#!/bin/sh

# Criar diretórios necessários
mkdir -p /usr/share/nginx/html/streams/output /usr/share/nginx/html/uploads

# Verificar se o diretório frontend_build existe e fazer o link simbólico
if [ -d /mnt/frontend_build ]; then
  ln -sf /mnt/frontend_build/* /usr/share/nginx/html/
fi

# Iniciar o Nginx
nginx -g 'daemon off;'
