import React, { useEffect, useState, useRef } from 'react';
import { getCameras, createMap } from '../services/api';
import MapCameraIcon from '../components/MapCameraIcon';
import '../styles/cadastrarMapa.css';

function CadastrarMapa() {
  const [cameras, setCameras] = useState([]);
  const [mapName, setMapName] = useState('');
  const [mapImage, setMapImage] = useState(null);
  const [positions, setPositions] = useState({});
  const [draggedCameraId, setDraggedCameraId] = useState(null);
  const mapAreaRef = useRef(null);
  const mapImageRef = useRef(null);

  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const response = await getCameras();
        setCameras(response.data);
      } catch (error) {
        console.error('Erro ao buscar câmeras:', error);
      }
    };
    fetchCameras();
  }, []);

  const handleMapImageChange = (e) => {
    setMapImage(e.target.files[0]);
  };

  const handleSaveMap = async () => {
    const formData = new FormData();
    formData.append('name', mapName);
    formData.append('map_image', mapImage);
    formData.append('positions', JSON.stringify(Object.values(positions)));

    try {
      console.log('Enviando dados para criar um mapa:', formData);
      const response = await createMap(formData);
      console.log('Resposta da API ao criar mapa:', response);
      alert('Mapa salvo com sucesso!');
    } catch (error) {
      console.error('Erro ao salvar mapa:', error);
    }
  };

  const handleDragStart = (cameraId) => {
    setDraggedCameraId(cameraId);
  };

  const handleDragEnd = (event) => {
    if (!draggedCameraId) return;

    const mapElement = mapAreaRef.current;
    const imgElement = mapImageRef.current;
    if (!mapElement || !imgElement) return;

    const mapRect = mapElement.getBoundingClientRect();
    const imgRect = imgElement.getBoundingClientRect();

    // Calculando escala da imagem
    const scaleX = imgRect.width / imgElement.naturalWidth;
    const scaleY = imgRect.height / imgElement.naturalHeight;

    // Coordenadas ajustadas usando a escala da imagem
    const x = (event.clientX - imgRect.left) / scaleX;
    const y = (event.clientY - imgRect.top) / scaleY;

    // Atualizar posição da câmera no estado
    setPositions((prevPositions) => ({
      ...prevPositions,
      [draggedCameraId]: { camera_id: draggedCameraId, pos_x: x, pos_y: y },
    }));

    setDraggedCameraId(null);
  };

  const handleDragOver = (event) => {
    event.preventDefault(); // Permitir que o item seja solto nesta área
  };

  const handleDrop = (event) => {
    event.preventDefault();
    handleDragEnd(event);
  };

  return (
    <div className="cadastrar-mapa-container">
      <h1>Cadastrar Mapa</h1>
      <div className="form-container">
        <input
          type="text"
          placeholder="Nome do Mapa"
          value={mapName}
          onChange={(e) => setMapName(e.target.value)}
        />
        <input type="file" onChange={handleMapImageChange} />
      </div>
      <div className="map-content">
        <div className="camera-list">
          <h3>Câmeras Disponíveis</h3>
          {cameras.map((camera) => (
            <div className="camera-list-item" key={camera.id}>
              <MapCameraIcon
                camera={camera}
                draggable
                onDragStart={() => handleDragStart(camera.id)}
                isInMap={false}
              />
            </div>
          ))}
        </div>
        <div
          className="map-area"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          ref={mapAreaRef}
        >
          {mapImage && (
            <div className="map-preview">
              <img
                src={URL.createObjectURL(mapImage)}
                alt="Mapa"
                className="map-image"
                ref={mapImageRef}
              />
              {Object.entries(positions).map(([cameraId, position]) => (
                <MapCameraIcon
                  key={cameraId}
                  camera={cameras.find((camera) => camera.id === parseInt(cameraId))}
                  isInMap={true}
                  style={{
                    left: `${position.pos_x * (mapImageRef.current?.clientWidth / mapImageRef.current?.naturalWidth)}px`,
                    top: `${position.pos_y * (mapImageRef.current?.clientHeight / mapImageRef.current?.naturalHeight)}px`,
                    position: 'absolute',
                    transform: 'translate(-50%, -50%)',
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>
      <button onClick={handleSaveMap}>Salvar Mapa</button>
    </div>
  );
}

export default CadastrarMapa;
