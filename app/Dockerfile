FROM python:3.10

WORKDIR /app

# Copiar todos os arquivos para o contêiner
COPY . .

# Instalar dependências do sistema para OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

# Dar permissão de execução ao script stop_ffmpeg_containers.sh
RUN chmod +x stop_ffmpeg_containers.sh

# Instalar dependências do Python
RUN pip install -r requirements.txt

CMD ["bash", "-c", "trap './stop_ffmpeg_containers.sh' EXIT; python app.py"]