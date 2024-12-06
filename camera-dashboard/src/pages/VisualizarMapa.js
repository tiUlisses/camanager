import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { getMapDetails } from '../services/api';
import MapCameraIcon from '../components/MapCameraIcon';
import MapGatewayIcon from '../components/MapGatewayIcon';
import Modal from '../components/Modal';
import CameraView from './CameraView';
import '../styles/visualizarMapa.css';

function VisualizarMapa() {
  const { mapId } = useParams();
  const [map, setMap] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState(null); // Conteúdo dinâmico do modal
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

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await getMapDetails(mapId);
        setMap(response.data);
      } catch (error) {
        console.error('Erro ao atualizar detalhes do mapa:', error);
      }
    }, 5000); // Atualiza a cada 5 segundos

    return () => clearInterval(interval);
  }, [mapId]);

  if (!map) {
    return <div>Carregando...</div>;
  }

  const imageUrl = `/${map.image_url}`;

  const handleCameraClick = (cameraId) => {
    setModalContent(<CameraView cameraId={cameraId} />);
    setIsModalOpen(true);
  };

  const handleGatewayClick = (gateway) => {
    const gatewayContent = (
      <div>
        <h2>Gateway: {gateway.name}</h2>
        <h3>Pessoas próximas:</h3>
        {gateway.people.length > 0 ? (
          <ul>
            {gateway.people.map((person) => (
              <li key={person.id}>
                {person.name} - Setor: {person.sector}
              </li>
            ))}
          </ul>
        ) : (
          <p>Nenhuma pessoa associada a este gateway no momento.</p>
        )}
      </div>
    );
    setModalContent(gatewayContent);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setModalContent(null);
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
          const scaleX = mapImageRef.current
            ? mapImageRef.current.clientWidth / mapImageRef.current.naturalWidth
            : 1;
          const scaleY = mapImageRef.current
            ? mapImageRef.current.clientHeight / mapImageRef.current.naturalHeight
            : 1;

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
        {map.gateways.map((gateway) => {
          const scaleX = mapImageRef.current
            ? mapImageRef.current.clientWidth / mapImageRef.current.naturalWidth
            : 1;
          const scaleY = mapImageRef.current
            ? mapImageRef.current.clientHeight / mapImageRef.current.naturalHeight
            : 1;

          return (
            <MapGatewayIcon
              key={gateway.gateway_id}
              gateway={gateway}
              peopleCount={gateway.people.length} // Passa a quantidade de pessoas
              style={{
                left: `${gateway.pos_x * scaleX}px`,
                top: `${gateway.pos_y * scaleY}px`,
                position: 'absolute',
                transform: 'translate(-50%, -50%)',
                cursor: 'pointer',
              }}
              onClick={() => handleGatewayClick(gateway)}
            />
          );
        })}
      </div>
      <Modal show={isModalOpen} onClose={handleCloseModal}>
        {modalContent}
      </Modal>
    </div>
  );
}

export default VisualizarMapa;
