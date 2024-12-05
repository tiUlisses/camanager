import React from 'react';
import { FaCamera } from 'react-icons/fa';
import '../styles/mapCameraIcon.css';

function MapCameraIcon({ camera, isInMap, onDragStart, style, onClick }) {
  return (
    <div
      className={`map-camera-icon ${isInMap ? 'in-map' : 'in-list'}`}
      draggable={!isInMap}
      onDragStart={onDragStart}
      onClick={onClick}
      style={style}
    >
      {isInMap ? <FaCamera /> : camera.name}
    </div>
  );
}

export default MapCameraIcon;
