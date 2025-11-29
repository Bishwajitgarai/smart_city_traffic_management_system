import * as api from './api.js';
import { loadCities, syncState } from './actions.js';
import { closeModal } from './ui.js';

export function setupEventListeners() {
    document.getElementById('cityForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('cityName').value;
        const code = document.getElementById('cityCode').value;
        await api.createCity({name, code});
        closeModal('cityModal');
        loadCities();
    });
    
    document.getElementById('areaForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const cityId = document.getElementById('areaCity').value;
        const name = document.getElementById('areaName').value;
        const code = document.getElementById('areaCode').value;
        await api.createArea({city_id: parseInt(cityId), name, code});
        closeModal('areaModal');
        loadCities();
    });

    document.getElementById('intersectionForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const areaId = document.getElementById('intersectionArea').value;
        const name = document.getElementById('intersectionName').value;
        const code = document.getElementById('intersectionCode').value;
        const location = document.getElementById('intersectionLocation').value;
        await api.createIntersection({area_id: parseInt(areaId), name, code, location});
        closeModal('intersectionModal');
        loadCities();
    });
    
    document.getElementById('lightForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const lightId = document.getElementById('lightId').value;
        const status = document.getElementById('lightStatus').value;
        const duration = document.getElementById('lightDuration').value;
        
        await api.updateLightManual(lightId, status, parseInt(duration));
        await api.updateLightDuration(lightId, duration);
        
        closeModal('lightModal');
        syncState();
    });

    document.getElementById('resetLightBtn').addEventListener('click', async () => {
        const lightId = document.getElementById('lightId').value;
        await api.resetLightManual(lightId);
        closeModal('lightModal');
        syncState();
    });
}
