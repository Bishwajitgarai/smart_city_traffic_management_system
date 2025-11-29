export async function fetchSync() {
    const response = await fetch('/api/v1/frontend/sync');
    return await response.json();
}

export async function fetchCities() {
    const response = await fetch('/api/v1/cities/');
    return await response.json();
}

export async function fetchCityDetails(id) {
    const response = await fetch(`/api/v1/cities/${id}`);
    return await response.json();
}

export async function fetchAreaDetails(id) {
    const response = await fetch(`/api/v1/areas/${id}`);
    return await response.json();
}

export async function createCity(data) {
    return await fetch('/api/v1/cities/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
}

export async function createArea(data) {
    return await fetch('/api/v1/areas/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
}

export async function createIntersection(data) {
    return await fetch('/api/v1/intersections/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
}

export async function updateLightManual(id, status, duration) {
    return await fetch(`/api/v1/admin/traffic-lights/${id}/manual`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({status, duration})
    });
}

export async function updateLightDuration(id, duration) {
    return await fetch(`/api/v1/admin/traffic-lights/${id}/duration?duration=${duration}`, {
        method: 'PUT'
    });
}
