import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { getMapDetails } from '../services/api';
import MapCameraIcon from '../components/MapCameraIcon';
import Modal from '../components/Modal';
import CameraView from './CameraView';
import '../styles/visualizarMapa.css';

function VisualizarMapa() {
  const { mapId } = useParams();
  const [map, setMap] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCameraId, setSelectedCameraId] = useState(null);
  const mapImageRef = useRef(null);

  useEffect(() => {
    const fetchMapDetails = async () => {
      try {
        const response = await getMapDetails(mapId);
        setMap(response.data);
      } catch (error) {
        console.error('Erro ao buscar detalhes do mapa:', error);
      }
    };
    fetchMapDetails();
  }, [mapId]);

  if (!map) {
    return <div>Carregando...</div>;
  }

  const imageUrl = `/${map.image_url}`;

  const handleCameraClick = (cameraId) => {
    setSelectedCameraId(cameraId);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedCameraId(null);
  };

  return (
    <div className="visualizar-mapa-container">
      <div className="map-preview">
        <img
          src={imageUrl}
          alt="Mapa"
          className="map-image"
          ref={mapImageRef}
        />
        {map.cameras.map((camera) => {
          // Ajustando a posição com base na escala da imagem atual
          const scaleX = mapImageRef.current ? mapImageRef.current.clientWidth / mapImageRef.current.naturalWidth : 1;
          const scaleY = mapImageRef.current ? mapImageRef.current.clientHeight / mapImageRef.current.naturalHeight : 1;

          return (
            <MapCameraIcon
              key={camera.camera_id}
              camera={camera}
              isInMap={true}
              style={{
                left: `${camera.pos_x * scaleX}px`,
                top: `${camera.pos_y * scaleY}px`,
                position: 'absolute',
                transform: 'translate(-50%, -50%)',
                cursor: 'pointer',
              }}
              onClick={() => handleCameraClick(camera.camera_id)}
            />
          );
        })}
      </div>
      {/* Modal para visualização da câmera */}
      <Modal show={isModalOpen} onClose={handleCloseModal}>
        {selectedCameraId && <CameraView cameraId={selectedCameraId} />}
      </Modal>
    </div>
  );
}

export default VisualizarMapa;
