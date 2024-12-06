import React from 'react';
import '../styles/mapGatewayIcon.css';

function MapGatewayIcon({ gateway, peopleCount, style, onClick }) {
  return (
    <div className="map-gateway-icon" style={style} onClick={onClick}>
      <img
        src="camera-dashboard/public/favicon.ico"
        alt="Gateway"
        className="gateway-icon"
      />
      {peopleCount > 0 && (
        <div className="people-count-indicator">
          {peopleCount}
        </div>
      )}
    </div>
  );
}

export default MapGatewayIcon;
