from flask_sqlalchemy import SQLAlchemy

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

class CameraMapPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer, db.ForeignKey('map.id'), nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)
    pos_x = db.Column(db.Float, nullable=False)
    pos_y = db.Column(db.Float, nullable=False)

    # Relacionamento com o modelo Camera
    camera = db.relationship('Camera', backref='camera_positions')

    # Relações
    map = db.relationship('Map', back_populates='camera_positions')
    camera = db.relationship('Camera')
