import { state } from './config.js';
import * as api from './api.js';
import * as ui from './ui.js';

export async function syncState() {
    try {
        const data = await api.fetchSync();
        for (const [id, lightState] of Object.entries(data)) {
            ui.updateLightState(parseInt(id), lightState);
        }
    } catch (e) {
        console.error("Sync failed", e);
    }
}

export async function loadCities() {
    state.cities = await api.fetchCities();
    ui.renderCityTree();
    ui.populateDropdowns();
}

export async function toggleCity(cityId) {
    const list = document.getElementById(`areas-${cityId}`);
    const toggle = document.getElementById(`toggle-${cityId}`);
    const city = state.cities.find(c => c.id === cityId);
    
    if (!list || !city) return;

    if (!city.areas) {
        try {
            const cityData = await api.fetchCityDetails(cityId);
            city.areas = cityData.areas;
            ui.renderAreas(cityId);
        } catch (e) {
            console.error("Failed to load areas", e);
            return;
        }
    }

    list.classList.toggle('collapsed');
    toggle.parentElement.classList.toggle('collapsed');
}

export async function selectArea(areaId, cityId) {
    state.selectedAreaId = areaId;
    
    document.querySelectorAll('.area-item').forEach(el => el.classList.remove('active'));
    const activeEl = document.getElementById(`area-${areaId}`);
    if (activeEl) activeEl.classList.add('active');
    
    const city = state.cities.find(c => c.id === cityId);
    if (!city) return;
    
    let area = city.areas.find(a => a.id === areaId);
    if (!area) return;

    if (!area.intersections) {
        try {
            const areaData = await api.fetchAreaDetails(areaId);
            area.intersections = areaData.intersections;
        } catch (e) {
            console.error("Failed to load intersections", e);
            return;
        }
    }
    
    ui.renderIntersections(area);
    syncState();
}
