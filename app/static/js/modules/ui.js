import { state } from './config.js';
import { generateBuildings, generateCarHtml } from './visuals.js';

export function renderCityTree() {
    const tree = document.getElementById('cityTree');
    tree.innerHTML = '';
    
    state.cities.forEach(city => {
        const cityDiv = document.createElement('div');
        cityDiv.className = 'city-item';
        
        const cityHeader = document.createElement('div');
        cityHeader.className = 'city-header';
        cityHeader.innerHTML = `
            <span>🏙️ ${city.name} <small>(${city.code})</small></span>
            <span class="city-toggle" id="toggle-${city.id}">▼</span>
        `;
        cityHeader.onclick = () => window.toggleCity(city.id);
        cityDiv.appendChild(cityHeader);

        const areaList = document.createElement('div');
        areaList.className = 'area-list collapsed';
        areaList.id = `areas-${city.id}`;
        cityDiv.appendChild(areaList);
        
        tree.appendChild(cityDiv);
        
        if (city.areas && city.areas.length > 0) {
            renderAreas(city.id);
        }
    });
}

export function renderAreas(cityId) {
    const list = document.getElementById(`areas-${cityId}`);
    const city = state.cities.find(c => c.id === cityId);
    if (!list || !city || !city.areas) return;
    
    list.innerHTML = '';
    city.areas.forEach(area => {
        const areaDiv = document.createElement('div');
        areaDiv.className = `area-item ${state.selectedAreaId === area.id ? 'active' : ''}`;
        areaDiv.id = `area-${area.id}`;
        areaDiv.onclick = () => window.selectArea(area.id, cityId);
        areaDiv.innerHTML = `<span>📍</span> ${area.name}`;
        list.appendChild(areaDiv);
    });
}

export function renderIntersections(area) {
    const grid = document.getElementById('intersectionsGrid');
    grid.innerHTML = '';
    
    if (!area || !area.intersections) return;
    
    area.intersections.forEach(intersection => {
        grid.appendChild(createIntersectionCard(intersection, area));
    });
}

export function createIntersectionCard(intersection, area) {
    const card = document.createElement('div');
    card.className = 'intersection-card';
    card.id = `intersection-${intersection.id}`;
    
    const lightsMap = {};
    intersection.traffic_lights.forEach(light => {
        lightsMap[light.direction.toLowerCase()] = light;
    });

    const directions = ['north', 'south', 'west', 'east'];
    const dirLabels = { 'north': 'N', 'south': 'S', 'west': 'W', 'east': 'E' };
    let lightsHTML = '';
    
    directions.forEach(dir => {
        const light = lightsMap[dir];
        if (light) {
            lightsHTML += `
                <div class="traffic-light-container pos-${dir}" id="light-${light.id}">
                    <div class="traffic-light-body">
                        <div class="light-label">${dirLabels[dir]}</div>
                        <div class="light red ${light.status === 'RED' ? 'active' : ''}"></div>
                        <div class="light yellow ${light.status === 'YELLOW' ? 'active' : ''}"></div>
                        <div class="light green ${light.status === 'GREEN' ? 'active' : ''}"></div>
                    </div>
                    <div class="timer-badge" id="timer-${light.id}">--</div>
                    <button class="btn-sm" onclick="window.openLightModal(${light.id}, ${light.duration}, '${light.status}')" style="margin-top:5px; font-size:0.7rem; padding:2px 5px; background:rgba(255,255,255,0.1); border:none; color:white; border-radius:4px; cursor:pointer;">⚙️</button>
                </div>
            `;
        }
    });

    card.innerHTML = `
        <div class="card-title">${intersection.name}</div>
        <small style="color: #94a3b8; display: block; margin-bottom: 1rem;">${area.name}</small>
        
        <div class="intersection-visual">
            ${generateBuildings()}
            <div class="direction-badge badge-n">North</div>
            <div class="direction-badge badge-s">South</div>
            <div class="direction-badge badge-w">West</div>
            <div class="direction-badge badge-e">East</div>
            <div class="road-vertical"></div>
            <div class="road-horizontal"></div>
            <div class="road-center"></div>
            ${generateCarHtml('ns', intersection.id, 6)}
            ${generateCarHtml('sn', intersection.id, 6)}
            ${generateCarHtml('we', intersection.id, 6)}
            ${generateCarHtml('ew', intersection.id, 6)}
            <div class="car car-turn-nw" id="car-turn-nw-${intersection.id}">🚗</div>
            <div class="car car-turn-se" id="car-turn-se-${intersection.id}">🚕</div>
            <div class="car car-turn-ws" id="car-turn-ws-${intersection.id}">🚙</div>
            <div class="car car-turn-en" id="car-turn-en-${intersection.id}">🚌</div>
            ${lightsHTML}
        </div>
    `;
    
    return card;
}

export function updateLightState(lightId, stateData) {
    state.lightsState[lightId] = stateData;
    
    const container = document.getElementById(`light-${lightId}`);
    if (!container) return;
    
    container.querySelectorAll('.light').forEach(el => el.classList.remove('active'));
    const activeLight = container.querySelector(`.light.${stateData.status.toLowerCase()}`);
    if (activeLight) activeLight.classList.add('active');
    
    if (stateData.end_time) {
        startCountdown(lightId, stateData.end_time);
    } else {
        if (state.countdownIntervals[lightId]) {
            clearInterval(state.countdownIntervals[lightId]);
            delete state.countdownIntervals[lightId];
        }
        const timerEl = document.getElementById(`timer-${lightId}`);
        if (timerEl) timerEl.textContent = '--';
    }

    const card = container.closest('.intersection-card');
    if (card) {
        const intersectionId = card.id.split('-')[1];
        updateTrafficFlow(intersectionId);
    }
}

export function updateTrafficFlow(intersectionId) {
    const card = document.getElementById(`intersection-${intersectionId}`);
    if (!card) return;
    
    const lights = card.querySelectorAll('.traffic-light-container');
    lights.forEach(container => {
        const isGreen = container.querySelector('.light.green.active');
        if (!isGreen) {
            if (container.classList.contains('pos-north')) {
                card.querySelectorAll('.car-ns').forEach(c => { c.classList.remove('moving'); c.classList.add('waiting'); });
                card.querySelector('.car-turn-nw').classList.remove('moving');
            } else if (container.classList.contains('pos-south')) {
                card.querySelectorAll('.car-sn').forEach(c => { c.classList.remove('moving'); c.classList.add('waiting'); });
                card.querySelector('.car-turn-se').classList.remove('moving');
            } else if (container.classList.contains('pos-west')) {
                card.querySelectorAll('.car-we').forEach(c => { c.classList.remove('moving'); c.classList.add('waiting'); });
                card.querySelector('.car-turn-ws').classList.remove('moving');
            } else if (container.classList.contains('pos-east')) {
                card.querySelectorAll('.car-ew').forEach(c => { c.classList.remove('moving'); c.classList.add('waiting'); });
                card.querySelector('.car-turn-en').classList.remove('moving');
            }
            return;
        }
        
        if (container.classList.contains('pos-north')) {
            card.querySelectorAll('.car-ns').forEach(c => { c.classList.add('moving'); c.classList.remove('waiting'); });
            if (Math.random() > 0.3) card.querySelector('.car-turn-nw').classList.add('moving');
        } else if (container.classList.contains('pos-south')) {
            card.querySelectorAll('.car-sn').forEach(c => { c.classList.add('moving'); c.classList.remove('waiting'); });
            if (Math.random() > 0.3) card.querySelector('.car-turn-se').classList.add('moving');
        } else if (container.classList.contains('pos-west')) {
            card.querySelectorAll('.car-we').forEach(c => { c.classList.add('moving'); c.classList.remove('waiting'); });
            if (Math.random() > 0.3) card.querySelector('.car-turn-ws').classList.add('moving');
        } else if (container.classList.contains('pos-east')) {
            card.querySelectorAll('.car-ew').forEach(c => { c.classList.add('moving'); c.classList.remove('waiting'); });
            if (Math.random() > 0.3) card.querySelector('.car-turn-en').classList.add('moving');
        }
    });
}

export function startCountdown(lightId, endTime) {
    if (state.countdownIntervals[lightId]) {
        clearInterval(state.countdownIntervals[lightId]);
    }
    
    const timerEl = document.getElementById(`timer-${lightId}`);
    if (!timerEl) return;
    
    state.countdownIntervals[lightId] = setInterval(() => {
        const now = Date.now() / 1000;
        const remaining = Math.max(0, Math.ceil(endTime - now));
        timerEl.textContent = remaining > 0 ? `${remaining}s` : '0s';
        
        if (remaining === 0) {
            clearInterval(state.countdownIntervals[lightId]);
            setTimeout(() => window.syncState(), 1000);
        }
    }, 100);
}

export function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

export function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

export function openLightModal(lightId, currentDuration, currentStatus) {
    document.getElementById('lightId').value = lightId;
    document.getElementById('lightDuration').value = currentDuration || 60;
    if (currentStatus) {
        document.getElementById('lightStatus').value = currentStatus;
    }
    openModal('lightModal');
}

export function populateDropdowns() {
    const cityDropdown = document.getElementById('areaCity');
    cityDropdown.innerHTML = '<option value="">Select City</option>';
    state.cities.forEach(city => {
        cityDropdown.innerHTML += `<option value="${city.id}">${city.name}</option>`;
    });

    const areaDropdown = document.getElementById('intersectionArea');
    areaDropdown.innerHTML = '<option value="">Select Area</option>';
    state.cities.forEach(city => {
        if (city.areas) {
            city.areas.forEach(area => {
                areaDropdown.innerHTML += `<option value="${area.id}">${city.name} - ${area.name}</option>`;
            });
        }
    });
}
