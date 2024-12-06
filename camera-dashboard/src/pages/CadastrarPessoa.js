import React, { useState } from 'react';
import { addPerson } from '../services/api'; // Importar o serviço da API para cadastro de pessoas

const CadastrarPessoa = () => {
  const [name, setName] = useState(''); // Nome da pessoa
  const [sector, setSector] = useState(''); // Setor da pessoa
  const [ibeaconMac, setIbeaconMac] = useState(''); // MAC do iBeacon
  const [message, setMessage] = useState(''); // Mensagem de feedback

  // Função para cadastrar a pessoa
  const handleAddPerson = async () => {
    if (!name || !ibeaconMac) {
      setMessage('Preencha os campos obrigatórios.');
      return;
    }

    try {
      await addPerson({ name, sector, ibeacon_mac: ibeaconMac }); // Envia os dados para o backend
      setMessage(`Pessoa "${name}" cadastrada com sucesso!`);
      setName('');
      setSector('');
      setIbeaconMac('');
    } catch (error) {
      console.error('Erro ao cadastrar pessoa:', error);
      setMessage('Erro ao cadastrar a pessoa. Verifique os dados e tente novamente.');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Cadastro de Pessoas</h1>

      {/* Formulário de cadastro */}
      <div>
        <label>
          Nome: <span style={{ color: 'red' }}>*</span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Digite o nome da pessoa"
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
            placeholder="Digite o setor (opcional)"
          />
        </label>
      </div>
      <div>
        <label>
          MAC do iBeacon: <span style={{ color: 'red' }}>*</span>
          <input
            type="text"
            value={ibeaconMac}
            onChange={(e) => setIbeaconMac(e.target.value)}
            placeholder="Digite o MAC do iBeacon"
          />
        </label>
      </div>

      <button onClick={handleAddPerson}>Cadastrar Pessoa</button>

      {/* Mensagem de feedback */}
      {message && <p>{message}</p>}
    </div>
  );
};

export default CadastrarPessoa;
