import os
import signal
import sys
from flask import Flask, request, jsonify
from models import db, Camera, Map, CameraMapPosition
from config import Config
from ffmpeg_manager import start_ffmpeg_container, stop_ffmpeg_container
from flask_cors import CORS
import logging
from log_config import setup_logging
import cv2  # Biblioteca OpenCV para validação de RTSP
from dotenv import load_dotenv
import shutil
import re
import unicodedata
import uuid
import json
# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar logs
setup_logging()
logger = logging.getLogger(__name__)

# Configurar Flask
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config.from_object(Config)
db.init_app(app)

# Função para normalizar os nomes, removendo acentos e caracteres especiais
def sanitize_name(name):
    # Remove acentos
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    # Substitui espaços e caracteres especiais por sublinhados
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    return name

# Inicializar banco de dados
with app.app_context():
    db.create_all()
    logger.info("Banco de dados inicializado com sucesso.")

    # Reiniciar contêineres para as câmeras já registradas no banco de dados
    cameras = Camera.query.all()
    for camera in cameras:
        if camera.container_id:
            logger.info(f"Reiniciando contêiner FFmpeg para câmera {camera.id}.")
            stop_ffmpeg_container(camera.container_id)
            camera.container_id = start_ffmpeg_container(camera.id, camera.name, camera.rtsp_url)
            db.session.commit()

# Diretório de saída
OUTPUT_DIR = os.getenv("CAMERAS_OUTPUT_DIR", "/var/www/html/cameras")

# Rota para adicionar uma nova câmera
@app.route('/api/cameras', methods=['POST'])
def add_camera():
    data = request.get_json()
    name = data.get('name')
    rtsp_url = data.get('rtsp_url')
    agrupamento = data.get('agrupamento')

    if not name or not rtsp_url or not agrupamento:
        logger.warning("Nome, URL RTSP ou Agrupamento ausentes na requisição.")
        return jsonify({"error": "Nome, URL RTSP e Agrupamento são obrigatórios"}), 400

    # Validar se já existe uma câmera com o mesmo nome e agrupamento
    existing_camera = Camera.query.filter_by(name=name, agrupamento=agrupamento).first()
    if existing_camera:
        logger.warning(f"Câmera com nome {name} e agrupamento {agrupamento} já existe.")
        return jsonify({"error": "Câmera com o mesmo nome e agrupamento já existe"}), 400

    # Validar a conexão com a URL RTSP
    logger.info(f"Validando conexão RTSP para {name}...")
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        logger.error(f"Falha ao conectar ao fluxo RTSP: {rtsp_url}")
        return jsonify({'error': 'Não foi possível conectar ao fluxo RTSP. Verifique a URL.'}), 400

    ret, _ = cap.read()
    cap.release()
    if not ret:
        logger.error(f"Fluxo RTSP inválido ou inacessível: {rtsp_url}")
        return jsonify({'error': 'Não foi possível ler do fluxo RTSP. Verifique a URL.'}), 400

    # Criar e salvar a nova câmera no banco de dados
    camera = Camera(name=name, rtsp_url=rtsp_url, agrupamento=agrupamento)
    db.session.add(camera)
    db.session.commit()
    logger.info(f"Câmera {name} adicionada com sucesso.")

    # Iniciar o contêiner Docker para processar o fluxo de câmera
    logger.info(f"Iniciando contêiner FFmpeg para câmera {camera.id}.")
    camera.container_id = start_ffmpeg_container(camera.id, camera.name, camera.rtsp_url)
    db.session.commit()

    return jsonify({"message": "Câmera adicionada com sucesso"}), 201

# Rota para atualizar uma câmera existente
@app.route('/api/cameras/<int:camera_id>', methods=['PUT'])
def update_camera(camera_id):
    data = request.get_json()
    camera = Camera.query.get(camera_id)

    if not camera:
        logger.warning(f"Câmera com ID {camera_id} não encontrada.")
        return jsonify({"error": "Câmera não encontrada"}), 404

    name = data.get('name')
    rtsp_url = data.get('rtsp_url')
    agrupamento = data.get('agrupamento')

    if rtsp_url:
        # Validar a conexão com a URL RTSP
        logger.info(f"Validando conexão RTSP para atualização da câmera {camera.name}...")
        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            logger.error(f"Falha ao conectar ao fluxo RTSP: {rtsp_url}")
            return jsonify({'error': 'Não foi possível conectar ao fluxo RTSP. Verifique a URL.'}), 400

        ret, _ = cap.read()
        cap.release()
        if not ret:
            logger.error(f"Fluxo RTSP inválido ou inacessível: {rtsp_url}")
            return jsonify({'error': 'Não foi possível ler do fluxo RTSP. Verifique a URL.'}), 400

    # Parar e remover o contêiner antigo, se necessário
    if camera.container_id:
        stop_ffmpeg_container(camera.container_id)

    # Atualizar os dados da câmera
    if name:
        camera.name = name
    if rtsp_url:
        camera.rtsp_url = rtsp_url
    if agrupamento:
        camera.agrupamento = agrupamento

    # Iniciar o contêiner Docker para processar o fluxo de câmera atualizado
    camera.container_id = start_ffmpeg_container(camera.id, camera.name, camera.rtsp_url)
    db.session.commit()

    logger.info(f"Câmera {camera.name} atualizada com sucesso.")
    return jsonify({"message": "Câmera atualizada com sucesso"}), 200

# Rota para listar todas as câmeras
@app.route('/api/cameras', methods=['GET'])
def list_cameras():
    cameras = Camera.query.all()
    cameras_data = [{
        "id": camera.id,
        "name": camera.name,
        "rtsp_url": camera.rtsp_url,
        "agrupamento": camera.agrupamento
    } for camera in cameras]

    return jsonify(cameras_data), 200

# Rota para deletar uma câmera existente
@app.route('/api/cameras/<int:camera_id>', methods=['DELETE'])
def delete_camera(camera_id):
    camera = Camera.query.get(camera_id)

    if not camera:
        logger.warning(f"Câmera com ID {camera_id} não encontrada.")
        return jsonify({"error": "Câmera não encontrada"}), 404

    # Parar o contêiner Docker associado à câmera
    if camera.container_id:
        stop_ffmpeg_container(camera.container_id)

    # Remover a câmera do banco de dados
    db.session.delete(camera)
    db.session.commit()
    logger.info(f"Câmera {camera.name} removida com sucesso.")

    # Remover diretório de saída da câmera
    output_dir = os.path.join(OUTPUT_DIR, str(camera_id))
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
            logger.info(f"Diretório {output_dir} removido com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao remover o diretório {output_dir}: {e}")

    return jsonify({"message": "Câmera removida com sucesso"}), 200

@app.route('/api/maps', methods=['POST'])
def create_map():
    logger.info("Recebendo solicitação para criar um mapa.")

    if 'name' not in request.form or 'map_image' not in request.files:
        logger.warning("Nome do mapa ou imagem não fornecidos na requisição.")
        return jsonify({"error": "Nome e imagem do mapa são obrigatórios"}), 400

    name = request.form['name']
    map_image = request.files['map_image']

    # Salvando a imagem do mapa no servidor
    image_filename = f"{uuid.uuid4()}_{sanitize_name(map_image.filename)}"
    image_path = os.path.join('uploads', 'maps', image_filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    map_image.save(image_path)

    logger.info(f"Imagem do mapa {name} salva com sucesso em {image_path}.")

    positions = request.form.get('positions')
    try:
        positions_data = json.loads(positions)
    except Exception as e:
        logger.error(f"Erro ao carregar as posições das câmeras: {e}")
        return jsonify({"error": "Formato inválido para posições"}), 400

    new_map = Map(name=name, image_url=image_path)
    db.session.add(new_map)
    db.session.commit()

    # Adicionando as posições das câmeras ao mapa
    for pos in positions_data:
        camera_position = CameraMapPosition(
            map_id=new_map.id,
            camera_id=pos['camera_id'],
            pos_x=pos['pos_x'],
            pos_y=pos['pos_y']
        )
        db.session.add(camera_position)

    db.session.commit()

    logger.info(f"Mapa {name} criado com sucesso com ID {new_map.id}.")

    return jsonify({"message": "Mapa criado com sucesso", "map_id": new_map.id}), 201



@app.route('/api/maps/<int:map_id>/cameras', methods=['POST'])
def add_cameras_to_map(map_id):
    map = Map.query.get(map_id)

    if not map:
        return jsonify({"error": "Mapa não encontrado"}), 404

    data = request.get_json()
    cameras = data.get('cameras')

    if not cameras:
        return jsonify({"error": "Lista de câmeras é obrigatória"}), 400

    for cam in cameras:
        camera_id = cam.get('camera_id')
        pos_x = cam.get('pos_x')
        pos_y = cam.get('pos_y')

        camera = Camera.query.get(camera_id)
        if not camera:
            continue

        camera_position = CameraMapPosition(
            map_id=map.id,
            camera_id=camera.id,
            pos_x=pos_x,
            pos_y=pos_y
        )
        db.session.add(camera_position)

    db.session.commit()

    return jsonify({"message": "Câmeras adicionadas ao mapa com sucesso"}), 200

@app.route('/api/maps', methods=['GET'])
def get_maps():
    logger.info("Recebendo solicitação para listar mapas.")
    maps = Map.query.all()
    maps_data = [{
        "id": map.id,
        "name": map.name,
        "image_url": map.image_url
    } for map in maps]

    logger.info(f"Mapas encontrados: {len(maps_data)}")
    return jsonify(maps_data), 200
    
@app.route('/api/maps/<int:map_id>', methods=['GET'])
def get_map(map_id):
    map = Map.query.get(map_id)

    if not map:
        return jsonify({"error": "Mapa não encontrado"}), 404

    cameras_data = []
    for camera_position in map.camera_positions:
        camera = camera_position.camera
        cameras_data.append({
            "camera_id": camera.id,
            "name": camera.name,
            "rtsp_url": camera.rtsp_url,
            "agrupamento": camera.agrupamento,
            "pos_x": camera_position.pos_x,
            "pos_y": camera_position.pos_y
        })

    return jsonify({
        "map_id": map.id,
        "name": map.name,
        "image_url": map.image_url,
        "cameras": cameras_data
    }), 200

@app.route('/api/maps/<int:map_id>', methods=['DELETE'])
def delete_map(map_id):
    map = Map.query.get(map_id)

    if not map:
        return jsonify({"error": "Mapa não encontrado"}), 404

    # Remover as associações das câmeras
    CameraMapPosition.query.filter_by(map_id=map_id).delete()

    # Remover o mapa
    db.session.delete(map)
    db.session.commit()

    return jsonify({"message": "Mapa removido com sucesso"}), 200


# Rota para validar a URL RTSP de uma câmera
@app.route('/api/cameras/validate', methods=['POST'])
def validate_rtsp():
    data = request.get_json()
    rtsp_url = data.get('rtsp_url')

    if not rtsp_url:
        logger.warning("URL RTSP ausente na requisição.")
        return jsonify({"error": "URL RTSP é obrigatória"}), 400

    # Validar a conexão com a URL RTSP
    logger.info(f"Validando conexão RTSP...")
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        logger.error(f"Falha ao conectar ao fluxo RTSP: {rtsp_url}")
        return jsonify({'error': 'Não foi possível conectar ao fluxo RTSP. Verifique a URL.'}), 400

    ret, _ = cap.read()
    cap.release()
    if not ret:
        logger.error(f"Fluxo RTSP inválido ou inacessível: {rtsp_url}")
        return jsonify({'error': 'Não foi possível ler do fluxo RTSP. Verifique a URL.'}), 400

    return jsonify({"message": "URL RTSP válida"}), 200

# Função para parar todos os contêineres ao encerrar a aplicação
def stop_all_containers(signal_received, frame):
    # Parar todos os contêineres criados para câmeras ao finalizar a aplicação
    logger.info("Encerrando todos os contêineres de câmeras...")
    cameras = Camera.query.all()
    for camera in cameras:
        try:
            if camera.container_id:
                stop_ffmpeg_container(camera.container_id)
        except Exception as e:
            logger.error(f"Erro ao parar contêiner {camera.name}: {e}")
    sys.exit(0)

# Associa sinais de interrupção (Ctrl+C ou término do programa) ao método de limpeza
signal.signal(signal.SIGINT, stop_all_containers)
signal.signal(signal.SIGTERM, stop_all_containers)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
