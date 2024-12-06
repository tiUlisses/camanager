import React, { useEffect, useState, useRef } from 'react';
import { getCameras, getGateways, createMap } from '../services/api';
import MapCameraIcon from '../components/MapCameraIcon';
import '../styles/cadastrarMapa.css';

function CadastrarMapa() {
  const [cameras, setCameras] = useState([]);
  const [gateways, setGateways] = useState([]);
  const [mapName, setMapName] = useState('');
  const [mapImage, setMapImage] = useState(null);
  const [positions, setPositions] = useState({});
  const [draggedItem, setDraggedItem] = useState(null);
  const mapAreaRef = useRef(null);
  const mapImageRef = useRef(null);

  useEffect(() => {
    const fetchResources = async () => {
      try {
        const camerasResponse = await getCameras();
        setCameras(camerasResponse.data);

        const gatewaysResponse = await getGateways();
        setGateways(gatewaysResponse.data);
      } catch (error) {
        console.error('Erro ao buscar câmeras ou gateways:', error);
      }
    };
    fetchResources();
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
      const response = await createMap(formData);
      alert('Mapa salvo com sucesso!');
    } catch (error) {
      console.error('Erro ao salvar mapa:', error);
    }
  };

  const handleDragStart = (id, type) => {
    setDraggedItem({ id, type });
  };

  const handleDrop = (event) => {
    if (!draggedItem || !mapImageRef.current) return;

    const imgRect = mapImageRef.current.getBoundingClientRect();
    const scaleX = imgRect.width / mapImageRef.current.naturalWidth;
    const scaleY = imgRect.height / mapImageRef.current.naturalHeight;

    const x = (event.clientX - imgRect.left) / scaleX;
    const y = (event.clientY - imgRect.top) / scaleY;

    setPositions((prev) => ({
      ...prev,
      [`${draggedItem.type}-${draggedItem.id}`]: {
        id: draggedItem.id,
        type: draggedItem.type,
        pos_x: x,
        pos_y: y,
      },
    }));

    setDraggedItem(null);
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
        <div className="item-list">
          <h3>Câmeras Disponíveis</h3>
          {cameras.map((camera) => (
            <div className="item-list-item" key={camera.id}>
              <MapCameraIcon
                camera={camera}
                draggable
                onDragStart={() => handleDragStart(camera.id, 'camera')}
                isInMap={false}
              />
            </div>
          ))}
          <h3>Gateways Disponíveis</h3>
          {gateways.map((gateway) => (
            <div className="item-list-item" key={gateway.id}>
              <MapCameraIcon
                camera={{ ...gateway, name: gateway.name || gateway.mac }}
                draggable
                onDragStart={() => handleDragStart(gateway.id, 'gateway')}
                isInMap={false}
              />
            </div>
          ))}
        </div>
        <div
          className="map-area"
          ref={mapAreaRef}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          {mapImage && (
            <div className="map-preview">
              <img
                src={URL.createObjectURL(mapImage)}
                alt="Mapa"
                className="map-image"
                ref={mapImageRef}
              />
              {Object.entries(positions).map(([key, position]) => (
                <MapCameraIcon
                  key={key}
                  camera={{
                    name:
                      position.type === 'camera'
                        ? cameras.find((cam) => cam.id === position.id)?.name
                        : gateways.find((gw) => gw.id === position.id)?.name,
                  }}
                  isInMap={true}
                  style={{
                    left: `${position.pos_x * (mapImageRef.current.clientWidth / mapImageRef.current.naturalWidth)}px`,
                    top: `${position.pos_y * (mapImageRef.current.clientHeight / mapImageRef.current.naturalHeight)}px`,
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
