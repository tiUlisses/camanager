import React from 'react';
import { useNavigate } from 'react-router-dom';

function CameraItem({ camera, onDelete }) {
  const navigate = useNavigate();

  return (
    <div className="camera-item">
      <h3>{camera.name}</h3>
      <p>Agrupamento: {camera.agrupamento}</p>
      <button onClick={() => navigate(`/camera/${camera.id}`)}>Visualizar</button>
      <button onClick={() => onDelete(camera.id)}>Remover</button>
    </div>
  );
}

export default CameraItem;
