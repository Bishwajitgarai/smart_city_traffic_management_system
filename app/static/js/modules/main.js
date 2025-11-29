import { initWebSocket } from './websocket.js';
import { loadCities, toggleCity, selectArea, syncState } from './actions.js';
import { setupEventListeners } from './events.js';
import { openModal, closeModal, openLightModal, renderFavoritesPage } from './ui.js';

// Expose global functions for HTML onclick handlers
window.toggleCity = toggleCity;
window.selectArea = selectArea;
window.openModal = openModal;
window.closeModal = closeModal;
window.openLightModal = openLightModal;
window.syncState = syncState;
window.renderFavoritesPage = renderFavoritesPage;

document.addEventListener('DOMContentLoaded', async () => {
    console.log("DOM Content Loaded");
    initWebSocket();
    try {
        console.log("Loading cities...");
        await loadCities();
        console.log("Cities loaded");
        setupEventListeners();
        
        // Default to Favorites View
        console.log("Rendering Favorites Page...");
        setTimeout(async () => {
            await renderFavoritesPage();
            console.log("Favorites Page Rendered");
        }, 500);
    } catch (error) {
        console.error("Error during startup:", error);
    }
});
