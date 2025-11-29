import { state } from './config.js';
import { generateBuildings, generateCarHtml } from './visuals.js';
import { toggleFavorite, fetchCityDetails, fetchAreaDetails } from './api.js';

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
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div class="card-title" style="margin-bottom: 0;">${intersection.name}</div>
            <span class="favorite-star ${intersection.is_favorite ? 'active' : ''}" 
                  onclick="window.toggleFavoriteUI(${intersection.id}, ${!intersection.is_favorite}, event)"
                  style="cursor: pointer; font-size: 1.2rem; transition: transform 0.2s;">
                ${intersection.is_favorite ? '⭐' : '☆'}
            </span>
        </div>
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

window.toggleFavoriteUI = async function(id, isFavorite, event) {
    if (event) event.stopPropagation();
    
    try {
        const result = await toggleFavorite(id, isFavorite);
        
        // Update UI immediately
        const star = event.target;
        if (result.is_favorite) {
            star.classList.add('active');
            star.textContent = '⭐';
        } else {
            star.classList.remove('active');
            star.textContent = '☆';
        }
        
        // Update local state if needed
        state.cities.forEach(city => {
            if (city.areas) {
                city.areas.forEach(area => {
                    if (area.intersections) {
                        const intersection = area.intersections.find(i => i.id === id);
                        if (intersection) {
                            intersection.is_favorite = result.is_favorite;
                        }
                    }
                });
            }
        });
        
        // Refresh favorites page if active
        if (state.selectedAreaId === 'favorites') {
            renderFavoritesPage();
        }
        
    } catch (error) {
        console.error('Failed to toggle favorite:', error);
        alert('Failed to update favorite status');
    }
};
export async function renderFavoritesPage() {
    console.log("renderFavoritesPage called");
    const grid = document.getElementById('intersectionsGrid');
    if (!grid) {
        console.error("Grid not found!");
        return;
    }
    
    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #94a3b8;">Loading favorites...</div>';
    state.selectedAreaId = 'favorites';
    document.querySelectorAll('.area-item').forEach(el => el.classList.remove('active'));
    
    // Ensure we have all data loaded
    try {
        // We need to iterate all cities and areas to check for favorites
        // This might be heavy if there are many, but for now it's necessary
        // because favorites can be anywhere.
        // A better backend endpoint /api/v1/favorites would be ideal, but let's fix it frontend-side first.
        
        for (const city of state.cities) {
            if (!city.areas) {
                try {
                    const cityData = await fetchCityDetails(city.id);
                    city.areas = cityData.areas;
                } catch (e) {
                    console.error(`Failed to load areas for city ${city.id}`, e);
                }
            }
            
            if (city.areas) {
                for (const area of city.areas) {
                    if (!area.intersections) {
                        try {
                            const areaData = await fetchAreaDetails(area.id);
                            area.intersections = areaData.intersections;
                        } catch (e) {
                            console.error(`Failed to load intersections for area ${area.id}`, e);
                        }
                    }
                }
            }
        }
    } catch (e) {
        console.error("Error loading data for favorites:", e);
    }
    
    grid.innerHTML = '';
    let hasFavorites = false;
    
    state.cities.forEach(city => {
        if (city.areas) {
            city.areas.forEach(area => {
                if (area.intersections) {
                    area.intersections.forEach(intersection => {
                        if (intersection.is_favorite) {
                            hasFavorites = true;
                            grid.appendChild(createIntersectionCard(intersection, area));
                        }
                    });
                }
            });
        }
    });
    
    if (!hasFavorites) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #94a3b8;">
                <div style="font-size: 3rem; margin-bottom: 20px;">⭐</div>
                <h3>No Favorites Yet</h3>
                <p>Star intersections to see them here!</p>
            </div>
        `;
    }
    
    // Sync state to ensure lights are correct
    if (window.syncState) {
        window.syncState();
    }
}

// Expose to window
window.renderFavoritesPage = renderFavoritesPage;
