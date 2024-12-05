import React, { useEffect, useState } from 'react';
import { getCameras, deleteCamera } from '../services/api';
import CameraForm from '../components/CameraForm';
import Modal from '../components/Modal';
import CameraView from './CameraView';
import '../styles/Dashboard.css';

function Dashboard() {
  const [cameras, setCameras] = useState([]);
  const [showFormModal, setShowFormModal] = useState(false);
  const [showCameraModal, setShowCameraModal] = useState(false);
  const [selectedCameraId, setSelectedCameraId] = useState(null);

  useEffect(() => {
    fetchCameras();
  }, []);

  const fetchCameras = async () => {
    try {
      const response = await getCameras();
      setCameras(response.data);
    } catch (error) {
      console.error('Erro ao buscar câmeras:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteCamera(id);
      fetchCameras();
    } catch (error) {
      console.error('Erro ao deletar câmera:', error);
    }
  };

  const handleViewCamera = (id) => {
    setSelectedCameraId(id);
    setShowCameraModal(true);
  };

  return (
    <div className="dashboard">
      <h1>Dashboard de Câmeras</h1>
      <button onClick={() => setShowFormModal(true)}>Adicionar Câmera</button>

      <table className="camera-table">
        <thead>
          <tr>
            <th>Nome</th>
            <th>Agrupamento</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {cameras.map((camera) => (
            <tr key={camera.id}>
              <td>{camera.name}</td>
              <td>{camera.agrupamento}</td>
              <td>
                <button onClick={() => handleViewCamera(camera.id)}>👁️</button>
                <button onClick={() => handleDelete(camera.id)}>🗑️</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Modal para adicionar câmera */}
      <Modal show={showFormModal} onClose={() => setShowFormModal(false)}>
        <CameraForm onSuccess={() => {
          fetchCameras();
          setShowFormModal(false);
        }} />
      </Modal>

      {/* Modal para visualizar câmera */}
      <Modal show={showCameraModal} onClose={() => setShowCameraModal(false)}>
        {selectedCameraId && <CameraView cameraId={selectedCameraId} />}
      </Modal>
    </div>
  );
}

export default Dashboard;
