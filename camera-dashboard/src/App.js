import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import CameraView from './pages/CameraView';
import CadastrarMapa from './pages/CadastrarMapa';
import CadastrarMapa2 from './pages/CadastrarMapa2';
import DashboardMapas from './pages/DashboardMapas';
import VisualizarMapa from './pages/VisualizarMapa';
import CadastrarGateway from './pages/CadastrarGateway';
import CadastrarPessoa from './pages/CadastrarPessoa'; // Importar o novo componente

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/camera/:id" element={<CameraView />} />
        <Route path="/cadastrar-mapa" element={<CadastrarMapa />} />
        <Route path="/cadastrar-mapa2" element={<CadastrarMapa2 />} />
        <Route path="/dashboard-mapas" element={<DashboardMapas />} />
        <Route path="/mapa/:mapId" element={<VisualizarMapa />} />
        <Route path="/cadastrar-gateway" element={<CadastrarGateway />} />
        <Route path="/cadastrar-pessoa" element={<CadastrarPessoa />} /> {/* Nova rota */}
      </Routes>
    </Router>
  );
}

export default App;
