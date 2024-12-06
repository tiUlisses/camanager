from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    rtsp_url = db.Column(db.String(255), nullable=False)
    agrupamento = db.Column(db.String(80), nullable=True)
    container_id = db.Column(db.String(255), nullable=True)  # Identificador do contêiner


class Map(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    camera_positions = db.relationship('CameraMapPosition', backref='map_relation', lazy=True)
    gateway_positions = db.relationship('GatewayMapPosition', backref='map_relation', lazy=True)


class CameraMapPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer, db.ForeignKey('map.id'), nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)
    pos_x = db.Column(db.Float, nullable=False)
    pos_y = db.Column(db.Float, nullable=False)

    camera = db.relationship('Camera', backref='camera_positions')


class Gateway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mac = db.Column(db.String(17), unique=True, nullable=False)
    sector = db.Column(db.String(100), nullable=True)

    # Alterado o backref para evitar colisão com o modelo LocationLog
    logs = db.relationship('LocationLog', backref='gateway_relation', lazy=True)


class GatewayMapPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer, db.ForeignKey('map.id'), nullable=False)
    gateway_id = db.Column(db.Integer, db.ForeignKey('gateway.id'), nullable=False)
    pos_x = db.Column(db.Float, nullable=False)
    pos_y = db.Column(db.Float, nullable=False)

    gateway = db.relationship('Gateway', backref='gateway_positions')


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(100), nullable=True)
    ibeacon_mac = db.Column(db.String(17), unique=True, nullable=False)

    logs = db.relationship('LocationLog', backref='person_relation', lazy=True)


class LocationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    gateway_id = db.Column(db.Integer, db.ForeignKey('gateway.id'), nullable=False)
    entry_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Interval, nullable=True)

    def close_log(self):
        """Fecha o log atualizando o horário de saída e a duração."""
        if not self.exit_time:
            self.exit_time = datetime.utcnow()
            self.duration = self.exit_time - self.entry_time
