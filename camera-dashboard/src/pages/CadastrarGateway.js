import React, { useState } from 'react';
import { getActiveGateways, addGateway } from '../services/api'; // Importar os serviços da API

const CadastrarGateway = () => {
  const [activeGateways, setActiveGateways] = useState([]);
  const [selectedGateway, setSelectedGateway] = useState(null);
  const [name, setName] = useState('');
  const [sector, setSector] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const fetchActiveGateways = async () => {
    setLoading(true);
    try {
      const response = await getActiveGateways();
      setActiveGateways(response.data);
      setMessage('');
    } catch (error) {
      console.error('Erro ao listar gateways ativos:', error);
      setMessage('Erro ao buscar gateways ativos. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddGateway = async () => {
    if (!selectedGateway || !name || !sector) {
      setMessage('Preencha todos os campos antes de enviar.');
      return;
    }

    try {
      await addGateway({ name, mac: selectedGateway, sector });
      setMessage(`Gateway "${name}" cadastrado com sucesso!`);
      setName('');
      setSector('');
      setSelectedGateway(null);
      setActiveGateways([]);
    } catch (error) {
      console.error('Erro ao cadastrar gateway:', error);
      setMessage('Erro ao cadastrar o gateway. Verifique os dados e tente novamente.');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Cadastro de Gateways</h1>

      <button onClick={fetchActiveGateways} disabled={loading}>
        {loading ? 'Carregando...' : 'Listar Gateways Ativos'}
      </button>

      {activeGateways.length > 0 && (
        <div>
          <h2>Gateways Ativos</h2>
          <ul>
            {activeGateways.map((mac) => (
              <li key={mac}>
                <label>
                  <input
                    type="radio"
                    name="selectedGateway"
                    value={mac}
                    checked={selectedGateway === mac}
                    onChange={() => setSelectedGateway(mac)}
                  />
                  {mac}
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}

      {selectedGateway && (
        <div>
          <h2>Registrar Gateway</h2>
          <p><strong>MAC Selecionado:</strong> {selectedGateway}</p>
          <div>
            <label>
              Nome:
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Digite o nome do gateway"
              />
            </label>
          </div>
          <div>
            <label>
              Setor:
              <input
                type="text"
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                placeholder="Digite o setor do gateway"
              />
            </label>
          </div>
          <button onClick={handleAddGateway}>Cadastrar Gateway</button>
        </div>
      )}

      {message && <p>{message}</p>}
    </div>
  );
};

export default CadastrarGateway;
