import os
import signal
import sys
from flask import Flask, request, jsonify
from models import db, Camera, Map, CameraMapPosition, Gateway, Person, GatewayMapPosition
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
import threading
import time
import paho.mqtt.client as mqtt


# Inicialização de estados globais
active_gateways = {}
gateway_last_seen = {}  # Mantém controle de mensagens recentes por gateway
BUFFER_TIME = 5  # Segundos para considerar uma pessoa "fora do local"
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

#Def dos Logs para rastreio
def close_inactive_logs():
    with app.app_context():
        now = datetime.utcnow()
        threshold_time = now - timedelta(seconds=3)

        # Encontra logs inativos
        inactive_logs = LocationLog.query.filter(
            LocationLog.exit_time == None,
            LocationLog.entry_time < threshold_time
        ).all()

        for log in inactive_logs:
            log.exit_time = now
            log.duration = log.exit_time - log.entry_time
            db.session.commit()

#Def de Registro dos Logs
def register_movement(person, gateway):
    now = datetime.utcnow()

    # Verificar se já existe um log ativo
    active_log = LocationLog.query.filter_by(
        person_id=person.id,
        gateway_id=gateway.id,
        exit_time=None
    ).first()

    if active_log:
        # Atualizar o horário de saída
        active_log.exit_time = now
        active_log.duration = active_log.exit_time - active_log.entry_time
        db.session.commit()
    else:
        # Criar novo log
        new_log = LocationLog(
            person_id=person.id,
            gateway_id=gateway.id,
            entry_time=now
        )
        db.session.add(new_log)
        db.session.commit()

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
        logger.error(f"Erro ao carregar as posições: {e}")
        return jsonify({"error": "Formato inválido para posições"}), 400

    # Criar o mapa no banco de dados
    new_map = Map(name=name, image_url=image_path)
    db.session.add(new_map)
    db.session.commit()

    # Processar posições
    for pos in positions_data:
        if pos['type'] == 'camera':
            # Adicionar posição de câmera
            camera_position = CameraMapPosition(
                map_id=new_map.id,
                camera_id=pos['id'],
                pos_x=pos['pos_x'],
                pos_y=pos['pos_y']
            )
            db.session.add(camera_position)
        elif pos['type'] == 'gateway':
            # Adicionar posição de gateway
            gateway_position = GatewayMapPosition(
                map_id=new_map.id,
                gateway_id=pos['id'],
                pos_x=pos['pos_x'],
                pos_y=pos['pos_y']
            )
            db.session.add(gateway_position)

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
            "pos_x": camera_position.pos_x,
            "pos_y": camera_position.pos_y
        })

    gateways_data = []
    manager = GatewayPeopleManager()  # Obter a instância Singleton
    for gateway_position in map.gateway_positions:
        gateway = gateway_position.gateway
        gateways_data.append({
            "gateway_id": gateway.id,
            "name": gateway.name,
            "pos_x": gateway_position.pos_x,
            "pos_y": gateway_position.pos_y,
            "people": manager.get_people_by_gateway(gateway.mac)
        })

    return jsonify({
        "map_id": map.id,
        "name": map.name,
        "image_url": map.image_url,
        "cameras": cameras_data,
        "gateways": gateways_data
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


### GATEWAYS MQTT ###
@app.route('/api/people/<int:person_id>/logs', methods=['GET'])
def get_person_logs(person_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    try:
        if not start_date or not end_date:
            return jsonify({"error": "start_date e end_date são obrigatórios"}), 400

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        logs = LocationLog.query.filter(
            LocationLog.person_id == person_id,
            LocationLog.entry_time >= start_date,
            LocationLog.entry_time < end_date
        ).all()

        log_data = [
            {
                "gateway": log.gateway.name,
                "entry_time": log.entry_time.isoformat(),
                "exit_time": log.exit_time.isoformat() if log.exit_time else None,
                "duration": str(log.duration) if log.duration else None
            }
            for log in logs
        ]

        return jsonify(log_data), 200

    except Exception as e:
        logger.error(f"Erro ao buscar logs: {e}")
        return jsonify({"error": "Erro ao buscar logs"}), 500


@app.route('/api/gateways/<int:gateway_id>', methods=['GET'])
def get_gateway_details(gateway_id):
    gateway = Gateway.query.get(gateway_id)
    if not gateway:
        return jsonify({"error": "Gateway não encontrado"}), 404

    # Buscando pessoas associadas a este gateway
    people_logs = LocationLog.query.filter_by(gateway_id=gateway_id).all()

    people_data = []
    for log in people_logs:
        person = log.person
        duration = log.exit_time - log.entry_time if log.exit_time else None
        people_data.append({
            "id": person.id,
            "name": person.name,
            "sector": person.sector,
            "duration": str(duration) if duration else "Presente",
        })

    return jsonify({
        "gateway": {
            "id": gateway.id,
            "name": gateway.name,
            "mac": gateway.mac,
            "sector": gateway.sector,
        },
        "people": people_data
    })


@app.route('/api/gateway-people/<string:gateway_mac>', methods=['GET'])
def get_people_by_gateway(gateway_mac):
    manager = GatewayPeopleManager()
    people = manager.get_people_by_gateway(gateway_mac)
    return jsonify(people), 200

@app.route('/api/gateway-people', methods=['GET'])
def get_all_gateway_people():
    manager = GatewayPeopleManager()
    data = manager.get_all_data()
    return jsonify(data), 200

# Configuração MQTT
BROKER = 'mosquitto'
PORT = 1883
TOPIC = '/gw/+/status'

# Certifique-se de declarar e inicializar a variável global `gateway_people` no início
# Inicialize a variável global fora de qualquer função
class GatewayPeopleManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GatewayPeopleManager, cls).__new__(cls)
            cls._instance.gateway_people = {}
        return cls._instance

    def add_person_to_gateway(self, gateway_mac, person):
        gateway_mac = gateway_mac.lower()
        if gateway_mac not in self.gateway_people:
            self.gateway_people[gateway_mac] = []
        if not any(p['id'] == person['id'] for p in self.gateway_people[gateway_mac]):
            self.gateway_people[gateway_mac].append(person)

    def remove_inactive_people(self, gateway_mac):
        gateway_mac = gateway_mac.lower()
        now = time.time()
        self.gateway_people[gateway_mac] = [
            person for person in self.gateway_people.get(gateway_mac, [])
            if now - gateway_last_seen.get((gateway_mac, person['ibeacon_mac']), 0) <= BUFFER_TIME
        ]

    def get_people_by_gateway(self, gateway_mac):
        return self.gateway_people.get(gateway_mac.lower(), [])

    def get_all_data(self):
        return self.gateway_people

def register_movement(person, gateway):
    now = datetime.utcnow()

    active_log = LocationLog.query.filter_by(
        person_id=person.id,
        gateway_id=gateway.id,
        exit_time=None
    ).first()

    if active_log:
        # Atualiza tempo final de log e duração
        active_log.exit_time = now
        active_log.duration = active_log.exit_time - active_log.entry_time
    else:
        # Cria novo log de movimentação
        new_log = LocationLog(
            person_id=person.id,
            gateway_id=gateway.id,
            entry_time=now
        )
        db.session.add(new_log)

    db.session.commit()

def close_inactive_logs():
    with app.app_context():
        now = datetime.utcnow()
        threshold_time = now - timedelta(seconds=BUFFER_TIME)

        # Atualiza logs inativos
        inactive_logs = LocationLog.query.filter(
            LocationLog.exit_time == None,
            LocationLog.entry_time < threshold_time
        ).all()

        for log in inactive_logs:
            log.exit_time = now
            log.duration = log.exit_time - log.entry_time
            db.session.commit()

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        topic = msg.topic
        gateway_mac = topic.split('/')[2].lower()

        logger.info(f"Mensagem recebida do gateway {gateway_mac}: {payload}")

        with app.app_context():
            manager = GatewayPeopleManager()

            for entry in payload:
                if entry.get("type") == "iBeacon":
                    ibeacon_mac = entry.get("mac")
                    person = Person.query.filter_by(ibeacon_mac=ibeacon_mac).first()
                    if person:
                        # Atualiza última vez vista
                        gateway_last_seen[(gateway_mac, ibeacon_mac)] = time.time()

                        # Adiciona pessoa ao gateway
                        manager.add_person_to_gateway(gateway_mac, {
                            "id": person.id,
                            "name": person.name,
                            "sector": person.sector,
                            "ibeacon_mac": ibeacon_mac
                        })

                        # Registra movimentação
                        gateway = Gateway.query.filter_by(mac=gateway_mac).first()
                        if gateway:
                            register_movement(person, gateway)

            # Remove pessoas inativas
            manager.remove_inactive_people(gateway_mac)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem MQTT: {e}")



def mqtt_listener():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.subscribe(TOPIC)
    client.loop_forever()       


@app.route('/api/gateways/active', methods=['GET'])
def list_active_gateways():
    now = time.time()
    active_list = [mac for mac, timestamp in active_gateways.items() if now - timestamp <= 5]
    return jsonify(active_list)

# Rota para cadastrar um gateway
@app.route('/api/gateways/register', methods=['POST'])
def register_gateway():
    data = request.json
    name = data.get('name')
    mac = data.get('mac')
    sector = data.get('sector')

    if not name or not mac:
        return jsonify({"error": "Nome e MAC são obrigatórios"}), 400

    # Verificar se o gateway já existe
    gateway = Gateway.query.filter_by(mac=mac).first()
    if gateway:
        return jsonify({"error": "Gateway já registrado"}), 400

    # Criar novo gateway
    new_gateway = Gateway(name=name, mac=mac, sector=sector)
    db.session.add(new_gateway)
    db.session.commit()
    return jsonify({"message": "Gateway registrado com sucesso"}), 201

# Rota para listar gateways registrados
@app.route('/api/gateways', methods=['GET'])
def list_gateways():
    gateways = Gateway.query.all()
    return jsonify([{"id": g.id, "name": g.name, "mac": g.mac, "sector": g.sector} for g in gateways])

@app.route('/api/gateways/delete/<int:id>', methods=['DELETE'])
def delete_gateway(id):
    # Verifica se o gateway existe no banco
    gateway = Gateway.query.get(id)
    if not gateway:
        return jsonify({"error": "Gateway não encontrado"}), 404

    # Deleta o gateway
    db.session.delete(gateway)
    db.session.commit()
    return jsonify({"message": "Gateway deletado com sucesso"}), 200

@app.route('/api/people/register', methods=['POST'])
def register_person():
    data = request.json
    name = data.get('name')
    sector = data.get('sector')
    ibeacon_mac = data.get('ibeacon_mac')

    if not name or not ibeacon_mac:
        return jsonify({"error": "Nome e MAC do iBeacon são obrigatórios"}), 400

    # Verificar se o MAC já está associado
    existing_person = Person.query.filter_by(ibeacon_mac=ibeacon_mac).first()
    if existing_person:
        return jsonify({"error": "MAC do iBeacon já associado a outra pessoa"}), 400

    # Criar nova pessoa
    new_person = Person(name=name, sector=sector, ibeacon_mac=ibeacon_mac)
    db.session.add(new_person)
    db.session.commit()

    return jsonify({
        "message": "Pessoa cadastrada com sucesso",
        "person": {
            "id": new_person.id,
            "name": new_person.name,
            "sector": new_person.sector,
            "ibeacon_mac": new_person.ibeacon_mac
        }
    }), 201

@app.route('/api/people', methods=['GET'])
def list_people():
    people = Person.query.all()
    return jsonify([
        {"id": p.id, "name": p.name, "sector": p.sector, "ibeacon_mac": p.ibeacon_mac}
        for p in people
    ])

@app.route('/api/people/update/<int:id>', methods=['PUT'])
def update_person(id):
    person = Person.query.get(id)
    if not person:
        return jsonify({"error": "Pessoa não encontrada"}), 404

    data = request.json
    name = data.get('name')
    sector = data.get('sector')
    ibeacon_mac = data.get('ibeacon_mac')

    # Atualiza os campos fornecidos
    if name:
        person.name = name
    if sector:
        person.sector = sector
    if ibeacon_mac:
        # Verifica se o novo MAC está associado a outra pessoa
        existing_person = Person.query.filter_by(ibeacon_mac=ibeacon_mac).first()
        if existing_person and existing_person.id != id:
            return jsonify({"error": "MAC do iBeacon já associado a outra pessoa"}), 400
        person.ibeacon_mac = ibeacon_mac

    db.session.commit()
    return jsonify({
        "message": "Pessoa atualizada com sucesso",
        "person": {
            "id": person.id,
            "name": person.name,
            "sector": person.sector,
            "ibeacon_mac": person.ibeacon_mac
        }
    }), 200

@app.route('/api/people/delete/<int:id>', methods=['DELETE'])
def delete_person(id):
    person = Person.query.get(id)
    if not person:
        return jsonify({"error": "Pessoa não encontrada"}), 404

    db.session.delete(person)
    db.session.commit()
    return jsonify({"message": "Pessoa deletada com sucesso"}), 200

# Associa sinais de interrupção (Ctrl+C ou término do programa) ao método de limpeza
signal.signal(signal.SIGINT, stop_all_containers)
signal.signal(signal.SIGTERM, stop_all_containers)

def mqtt_listener():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.subscribe(TOPIC)
    client.loop_forever()

if __name__ == '__main__':
    mqtt_thread = threading.Thread(target=mqtt_listener)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    app.run(debug=True, host="0.0.0.0", port=5000)
