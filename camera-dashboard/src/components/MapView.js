import React, { useEffect, useState } from 'react';
import { getMap } from '../services/api';
import VideoPlayer from './VideoPlayer';
import './mapView.css';

function MapView({ mapId }) {
  const [mapData, setMapData] = useState(null);
  const [selectedCamera, setSelectedCamera] = useState(null);

  useEffect(() => {
    const fetchMap = async () => {
      try {
        const response = await getMap(mapId);
        setMapData(response.data);
      } catch (error) {
        console.error('Erro ao buscar mapa:', error);
      }
    };
    fetchMap();
  }, [mapId]);

  if (!mapData) {
    return <div>Carregando...</div>;
  }

  return (
    <div className="map-view-container">
      <h1>{mapData.name}</h1>
      <div className="map-view">
        <img src={mapData.image_url} alt="Mapa" className="map-image" />
        {mapData.cameras.map((camera) => (
          <div
            key={camera.camera_id}
            className="camera-icon"
            style={{ top: camera.pos_y, left: camera.pos_x }}
            onClick={() => setSelectedCamera(camera)}
          >
            📷
          </div>
        ))}
      </div>
      {selectedCamera && (
        <div className="modal">
          <div className="modal-content">
            <span className="close" onClick={() => setSelectedCamera(null)}>&times;</span>
            <h2>{selectedCamera.name}</h2>
            <VideoPlayer src={`/streams/cameras_data/${selectedCamera.camera_id}/stream.m3u8`} />
          </div>
        </div>
      )}
    </div>
  );
}

export default MapView;
