import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMaps, deleteMap } from '../services/api';
import '../styles/dashboardMapas.css';

function DashboardMapas() {
  const [maps, setMaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchMaps = async () => {
      try {
        console.log('Buscando mapas do backend...');
        const response = await getMaps();
        setMaps(response.data);
        console.log('Mapas recebidos:', response.data);
      } catch (error) {
        console.error('Erro ao buscar mapas:', error);
        setError('Erro ao buscar mapas. Verifique se o backend está funcionando corretamente.');
      } finally {
        setLoading(false);
      }
    };
    fetchMaps();
  }, []);

  const handleDelete = async (mapId) => {
    try {
      await deleteMap(mapId);
      setMaps((prevMaps) => prevMaps.filter((map) => map.id !== mapId));
    } catch (error) {
      console.error('Erro ao deletar mapa:', error);
    }
  };

  const handleView = (mapId) => {
    navigate(`/mapa/${mapId}`);
  };

  if (loading) {
    return <div>Carregando mapas...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <div className="dashboard-mapas-container">
      <h1>Dashboard de Mapas</h1>
      {maps.length === 0 ? (
        <p>Nenhum mapa disponível.</p>
      ) : (
        <div className="map-list">
          {maps.map((map) => (
            <div key={map.id} className="map-item">
              <h3>{map.name}</h3>
              <button onClick={() => handleView(map.id)}>Visualizar</button>
              <button onClick={() => handleDelete(map.id)}>Remover</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default DashboardMapas;
