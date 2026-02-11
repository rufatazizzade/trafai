
import axios from 'axios';

const api = axios.create({
    baseURL: '/', // Vite proxy handles redirection to localhost:8000
    headers: {
        'Content-Type': 'application/json',
    },
});

export const getNetworkStats = () => api.get('/network/stats');
export const computeRoute = (startNode, endNode, timeHour = 8) =>
    api.post('/route', { start_node: startNode, end_node: endNode, time_hour: timeHour });
export const updateTraffic = (updates) => api.post('/traffic/update', { updates });
export const geocode = (address) => api.post('/geocode', { address });
export const initGrid = (rows, cols) => api.post(`/network/init-grid?rows=${rows}&cols=${cols}`);

export default api;
