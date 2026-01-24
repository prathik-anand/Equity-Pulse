import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const triggerAnalysis = async (ticker: string) => {
    const response = await api.post('/analysis', { ticker });
    return response.data;
};

export const getAnalysisResult = async (sessionId: string) => {
    const response = await api.get(`/analysis/${sessionId}`);
    return response.data;
};

export const getTickers = async () => {
    const response = await api.get('/tickers');
    return response.data;
}

export default api;
