import axios from 'axios';

// API_BASE_URL = 'http://localhost:5000/api' -> para desenvolvimento
// ou, se quiser usar variável de ambiente:
const API_BASE_URL =  '/api';



const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // Timeout de 10 segundos
});

export const getCameras = () => api.get('/cameras');
export const addCamera = (data) => api.post('/cameras', data);
export const updateCamera = (id, data) => api.put(`/cameras/${id}`, data);
export const deleteCamera = (id) => api.delete(`/cameras/${id}`);
export const validateRTSP = (data) => api.post('/cameras/validate', data);

// Adicione essa função para buscar mapas
export const getMaps = async () => {
    try {
      const response = await api.get('/maps');
      return response;
    } catch (error) {
      console.error('Erro ao obter mapas:', error);
      throw error;
    }
  };
export const createMap = (data) => api.post('/maps', data);
export const getMapDetails = async (mapId) => {
    try {
      const response = await api.get(`/maps/${mapId}`);
      return response;
    } catch (error) {
      console.error('Erro ao obter detalhes do mapa:', error);
      throw error;
    }
  };
  
export const addCamerasToMap = (mapId, data) => api.post(`/maps/${mapId}/cameras`, data);
export const deleteMap = (mapId) => api.delete(`/maps/${mapId}`);

// Gateways
export const getGateways = () => api.get('/gateways'); // Lista todos os gateways
export const addGateway = (data) => api.post('/gateways/register', data); // Adiciona um novo gateway
export const deleteGateway = (id) => api.delete(`/gateways/delete/${id}`); // Deleta um gateway
export const getActiveGateways = () => api.get('/gateways/active'); // Lista gateways ativos

// Pessoas
export const getPeople = () => api.get('/people'); // Lista todas as pessoas
export const addPerson = (data) => api.post('/people/register', data); // Adiciona uma nova pessoa
export const updatePerson = (id, data) => api.put(`/people/update/${id}`, data); // Atualiza uma pessoa
export const deletePerson = (id) => api.delete(`/people/delete/${id}`); // Deleta uma pessoa

export const getPeopleNearGateway = (gatewayId) =>
  api.get(`/gateways/${gatewayId}/people`);


export const getGatewayDetails = async (gatewayId) => {
  return await axios.get(`${API_BASE_URL}/gateways/${gatewayId}`);
};