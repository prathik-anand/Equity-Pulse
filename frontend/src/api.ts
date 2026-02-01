import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const triggerAnalysis = async (ticker: string, userSessionId: string) => {
    const response = await api.post('/analysis', {
        ticker,
        user_session_id: userSessionId
    });
    return response.data;
};

export const getAnalysisResult = async (id: string) => {
    const response = await api.get(`/analysis/${id}`);
    return response.data;
};

export const getUserHistory = async (userSessionId: string) => {
    const response = await api.get(`/history/${userSessionId}`);
    return response.data;
};

export const getTickers = async () => {
    const response = await api.get('/tickers');
    return response.data;
}

export default api;
