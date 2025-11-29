import { initWebSocket } from './websocket.js';
import { loadCities, toggleCity, selectArea, syncState } from './actions.js';
import { setupEventListeners } from './events.js';
import { openModal, closeModal, openLightModal } from './ui.js';

// Expose global functions for HTML onclick handlers
window.toggleCity = toggleCity;
window.selectArea = selectArea;
window.openModal = openModal;
window.closeModal = closeModal;
window.openLightModal = openLightModal;
window.syncState = syncState;

document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    loadCities();
    setupEventListeners();
});
