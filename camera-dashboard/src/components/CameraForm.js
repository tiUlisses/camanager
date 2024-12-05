import React, { useState, useEffect } from 'react';
import { getCameras, addCamera, validateRTSP } from '../services/api';

function CameraForm({ onSuccess }) {
  const [name, setName] = useState('');
  const [rtspUrl, setRtspUrl] = useState('');
  const [agrupamento, setAgrupamento] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const [cameras, setCameras] = useState([]);
  const [filteredCameras, setFilteredCameras] = useState([]);
  const [searchName, setSearchName] = useState('');
  const [selectedAgrupamento, setSelectedAgrupamento] = useState('');

  useEffect(() => {
    // Carregar câmeras do backend
    const fetchCameras = async () => {
      try {
        const response = await getCameras();
        setCameras(response.data);
        setFilteredCameras(response.data);
      } catch (error) {
        console.error('Erro ao buscar câmeras:', error);
      }
    };
    fetchCameras();
  }, []);

  // Atualizar a lista de câmeras com base nos filtros de nome e agrupamento
  useEffect(() => {
    let filtered = cameras;

    if (searchName) {
      filtered = filtered.filter((camera) =>
        camera.name.toLowerCase().includes(searchName.toLowerCase())
      );
    }

    if (selectedAgrupamento) {
      filtered = filtered.filter((camera) => camera.agrupamento === selectedAgrupamento);
    }

    setFilteredCameras(filtered);
  }, [searchName, selectedAgrupamento, cameras]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      // Validar a URL RTSP
      setSuccess('Validando URL RTSP...');
      await validateRTSP({ rtsp_url: rtspUrl });

      // Adicionar a câmera
      setSuccess('Adicionando câmera ao sistema...');
      await addCamera({ name, rtsp_url: rtspUrl, agrupamento });

      setSuccess('Câmera adicionada com sucesso!');
      setLoading(false);

      // Limpar os campos do formulário e chamar o callback de sucesso
      setName('');
      setRtspUrl('');
      setAgrupamento('');
      onSuccess();

      // Recarregar a lista de câmeras
      const response = await getCameras();
      setCameras(response.data);
    } catch (error) {
      setLoading(false);
      if (error.response && error.response.data && error.response.data.error) {
        setError(`Erro: ${error.response.data.error}`);
      } else {
        setError('Erro ao adicionar câmera. Verifique os dados inseridos e tente novamente.');
      }
      console.error('Erro ao adicionar câmera:', error);
    }
  };

  return (
    <div className="camera-dashboard-container">
      <form onSubmit={handleSubmit} className="camera-form">
        <h2>Adicionar Nova Câmera</h2>
        <input
          type="text"
          placeholder="Nome da Câmera"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          disabled={loading}
        />
        <input
          type="text"
          placeholder="URL RTSP"
          value={rtspUrl}
          onChange={(e) => setRtspUrl(e.target.value)}
          required
          disabled={loading}
        />
        <input
          type="text"
          placeholder="Agrupamento"
          value={agrupamento}
          onChange={(e) => setAgrupamento(e.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Processando...' : 'Adicionar Câmera'}
        </button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {success && <p style={{ color: 'green' }}>{success}</p>}
      </form>

      <div className="camera-filters">
        <h3>Filtrar Câmeras</h3>
        <input
          type="text"
          placeholder="Buscar por Nome"
          value={searchName}
          onChange={(e) => setSearchName(e.target.value)}
        />
        <select
          value={selectedAgrupamento}
          onChange={(e) => setSelectedAgrupamento(e.target.value)}
        >
          <option value="">Todos os Agrupamentos</option>
          {[...new Set(cameras.map((camera) => camera.agrupamento))].map((agrup) => (
            <option key={agrup} value={agrup}>
              {agrup}
            </option>
          ))}
        </select>
      </div>

      <div className="camera-list">
        <h3>Lista de Câmeras</h3>
        {filteredCameras.map((camera) => (
          <div key={camera.id} className="camera-list-item">
            <p>Nome: {camera.name}</p>
            <p>Agrupamento: {camera.agrupamento}</p>
            <p>URL RTSP: {camera.rtsp_url}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CameraForm;
