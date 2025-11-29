import { state } from './config.js';
import { updateLightState } from './ui.js';
import { syncState } from './actions.js';

export function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    state.ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/ws`);
    
    let isReconnect = false;
    
    state.ws.onopen = () => {
        console.log('WebSocket connected');
        if (isReconnect) {
            syncState();
        }
        isReconnect = true;
    };
    
    state.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'state_update') {
            updateLightState(data.light_id, data.state);
        } else if (data.type === 'batch_state_update') {
            data.updates.forEach(update => {
                updateLightState(update.light_id, update.state);
            });
        }
    };
    
    state.ws.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting...');
        setTimeout(initWebSocket, 3000);
    };
}
