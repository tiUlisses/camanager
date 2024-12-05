import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import CameraView from './pages/CameraView';
import CadastrarMapa from './pages/CadastrarMapa';
import DashboardMapas from './pages/DashboardMapas';
import VisualizarMapa from './pages/VisualizarMapa';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/camera/:id" element={<CameraView />} />
        <Route path="/cadastrar-mapa" element={<CadastrarMapa />} />
        <Route path="/dashboard-mapas" element={<DashboardMapas />} />
        <Route path="/mapa/:mapId" element={<VisualizarMapa />} />
      </Routes>
    </Router>
  );
}

export default App;
