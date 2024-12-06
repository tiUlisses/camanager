import os
import docker
from docker.errors import NotFound, APIError

client = docker.from_env()

def start_ffmpeg_container(camera_id, camera_name, rtsp_url):
    # Usar um identificador único baseado em UUID para o nome do container
    container_name = f"ffmpeg_{camera_id}"
    output_dir = f"/tmp/output/{camera_id}"  # Diretório no host baseado no ID da câmera
    container_output_dir = f"/output/{camera_id}"  # Diretório no container baseado no ID da câmera

    # Certifique-se de que o diretório de saída no host existe
    os.makedirs(output_dir, exist_ok=True)

    # Montagem do volume de maneira consistente para garantir a sincronização
    volume_mapping = {
        output_dir: {'bind': container_output_dir, 'mode': 'rw'}
    }

    # Certifique-se de que a pasta seja criada dentro do volume no container
    client.containers.run(
        "alpine",  # Usar uma imagem leve para criar o diretório
        command=["mkdir", "-p", container_output_dir],
        volumes=volume_mapping,
        remove=True  # Remove o container imediatamente após a execução
    )

    # Iniciar o contêiner FFmpeg com a configuração correta
    container = client.containers.run(
        "ffmpeg",  # Nome da imagem do FFmpeg
        command=[
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "32k",
            "-f", "hls",
            "-hls_time", "2",
            "-hls_list_size", "5",
            "-hls_flags", "delete_segments",
            f"{container_output_dir}/stream.m3u8"  # Arquivo de saída
        ],
        name=container_name,
        detach=True,
        volumes=volume_mapping,
        user='root',
        auto_remove=True 
    )

    return container.id

def stop_ffmpeg_container(container_id):
    try:
        container = client.containers.get(container_id)
        if container.status == "removing":
            # Se o contêiner já está sendo removido, apenas ignore
            print(f"Contêiner {container_id} já está em processo de remoção.")
            return
        
        container.stop()
        container.remove()
        print(f"Contêiner {container_id} removido com sucesso.")
    except NotFound:
        print(f"Contêiner {container_id} não encontrado.")
    except APIError as e:
        print(f"Erro ao tentar remover o contêiner {container_id}: {e}")
