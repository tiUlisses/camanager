import React, { useState } from 'react';
import '../styles/DraggableItem.css';

function DraggableItem({ item, type, onPositionChange, style }) {
  const [position, setPosition] = useState(style || { x: 50, y: 50 }); // Posição inicial padrão

  const handleDragEnd = (e) => {
    const mapElement = e.target.closest('.map-area'); // Verifica se foi solto na área do mapa
    if (!mapElement) return;

    const mapRect = mapElement.getBoundingClientRect();
    const newPos = {
      x: e.clientX - mapRect.left,
      y: e.clientY - mapRect.top,
    };

    setPosition(newPos);
    onPositionChange(item.id, type, newPos);
  };

  return (
    <div
      className={`draggable-item ${type}`}
      style={{
        ...position,
        position: 'absolute',
        transform: 'translate(-50%, -50%)',
      }}
      draggable
      onDragEnd={handleDragEnd}
    >
      {type === 'camera' ? '📷' : '📡'} {item.name || item.mac}
    </div>
  );
}

export default DraggableItem;
