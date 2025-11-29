export function generateBuildings() {
    const clusters = ['nw', 'ne', 'sw', 'se'];
    let html = '';
    
    clusters.forEach(cluster => {
        html += `<div class="building-cluster cluster-${cluster}">`;
        
        // Generate a mix of buildings and trees
        const count = Math.floor(Math.random() * 5) + 4; // 4-8 items per corner
        
        for (let i = 0; i < count; i++) {
            const type = Math.random();
            
            if (type < 0.4) {
                // House
                const variants = ['brick', 'cottage', 'modern', ''];
                const variant = variants[Math.floor(Math.random() * variants.length)];
                const height = Math.floor(Math.random() * 10) + 20; // 20-30px
                html += `<div class="structure house ${variant}" style="height: ${height}px;"></div>`;
            } else if (type < 0.7) {
                // Office
                const variants = ['tall', ''];
                const variant = variants[Math.floor(Math.random() * variants.length)];
                const height = Math.floor(Math.random() * 40) + 40; // 40-80px
                html += `<div class="structure office ${variant}" style="height: ${height}px;"></div>`;
            } else {
                // Tree
                const variants = ['pine', ''];
                const variant = variants[Math.floor(Math.random() * variants.length)];
                html += `<div class="tree ${variant}"></div>`;
            }
        }
        html += `</div>`;
    });
    
    return html;
}

export function generateCarHtml(direction, id, count) {
    let html = '';
    const cars = ['🚗', '🚕', '🚙', '🚌', '🚚', '🚓', '🚑'];
    for (let i = 1; i <= count; i++) {
        const randomCar = cars[Math.floor(Math.random() * cars.length)];
        // Stagger delays for continuous flow
        const delay = (i - 1) * 1.2;
        html += `<div class="car car-${direction}" id="car-${direction}-${i}-${id}" style="animation-delay: ${delay}s;">${randomCar}</div>`;
    }
    return html;
}
