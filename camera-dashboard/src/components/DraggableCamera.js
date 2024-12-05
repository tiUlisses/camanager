import React, { useState } from 'react';
import './DraggableCamera.css';

function DraggableCamera({ camera, onPositionChange }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleDrag = (e) => {
    const newPos = {
      x: e.clientX - e.target.offsetWidth / 2,
      y: e.clientY - e.target.offsetHeight / 2,
    };
    setPosition(newPos);
    onPositionChange(camera.id, newPos);
  };

  return (
    <div
      className="draggable-camera"
      style={{ left: `${position.x}px`, top: `${position.y}px` }}
      draggable
      onDragEnd={handleDrag}
    >
      📷 {camera.name}
    </div>
  );
}

export default DraggableCamera;
