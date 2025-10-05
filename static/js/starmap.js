class StarMap {
    constructor(containerId, width = 800, height = 600) {
        this.containerId = containerId;
        this.width = width;
        this.height = height;
        this.margin = { top: 20, right: 20, bottom: 30, left: 40 };
        this.exoplanets = [];
        this.colorScheme = {
            'Confirmed Exoplanet': '#00ff00',  // Green
            'Candidate': '#ffff00',           // Yellow
            'False Positive': '#ff4444'       // Red
        };
        
        this.init();
    }
    
    async init() {
        // Load exoplanet data
        await this.loadExoplanetData();
        
        // Create SVG
        this.svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('viewBox', [0, 0, this.width, this.height])
            .style('background', '#0a0a0a');  // Dark theme
        
        // Create scales
        this.xScale = d3.scaleLinear()
            .domain([0, 360])  // RA: 0-360 degrees
            .range([this.margin.left, this.width - this.margin.right]);
            
        this.yScale = d3.scaleLinear()
            .domain([-90, 90])  // Dec: -90 to 90 degrees
            .range([this.height - this.margin.bottom, this.margin.top]);
        
        // Create tooltip
        this.tooltip = d3.select('body')
            .append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '8px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none');
        
        this.render();
    }
    
    async loadExoplanetData() {
        try {
            const response = await fetch('/api/exoplanets');
            this.exoplanets = await response.json();
        } catch (error) {
            console.error('Error loading exoplanet data:', error);
            // Fallback to sample data
            this.exoplanets = this.generateSampleData();
        }
    }
    
    render() {
        // Clear previous render
        this.svg.selectAll('*').remove();
        
        // Create exoplanet points
        const points = this.svg.selectAll('.exoplanet')
            .data(this.exoplanets)
            .enter()
            .append('circle')
            .attr('class', 'exoplanet')
            .attr('cx', d => this.xScale(d.ra))
            .attr('cy', d => this.yScale(d.dec))
            .attr('r', d => this.calculateSize(d))
            .attr('fill', d => this.colorScheme[d.classification])
            .attr('stroke', '#ffffff')
            .attr('stroke-width', 0.5)
            .attr('opacity', 0.8)
            .style('cursor', 'pointer');
        
        // Add interactivity
        points.on('mouseover', (event, d) => {
            this.tooltip.transition()
                .duration(200)
                .style('opacity', .9);
            this.tooltip.html(this.getTooltipContent(d))
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', () => {
            this.tooltip.transition()
                .duration(500)
                .style('opacity', 0);
        })
        .on('click', (event, d) => {
            this.showExoplanetDetails(d);
        });
        
        // Add constellation lines (simplified)
        this.addConstellationLines();
        
        // Add Milky Way background (simplified)
        this.addMilkyWay();
    }
    
    calculateSize(exoplanet) {
        // Size based on radius and classification
        const baseSize = Math.log(exoplanet.radius + 1) * 2;
        const classificationMultiplier = {
            'Confirmed Exoplanet': 1.5,
            'Candidate': 1.2,
            'False Positive': 0.8
        };
        
        return baseSize * classificationMultiplier[exoplanet.classification];
    }
    
    getTooltipContent(exoplanet) {
        return `
            <strong>${exoplanet.name}</strong><br/>
            Classification: ${exoplanet.classification}<br/>
            Period: ${exoplanet.period.toFixed(2)} days<br/>
            Radius: ${exoplanet.radius.toFixed(2)} Earth radii<br/>
            Temperature: ${Math.round(exoplanet.temperature)} K<br/>
            SNR: ${exoplanet.snr.toFixed(1)}
        `;
    }
    
    showExoplanetDetails(exoplanet) {
        // Dispatch custom event for other components to handle
        const event = new CustomEvent('exoplanetSelected', { detail: exoplanet });
        document.dispatchEvent(event);
    }
    
    addConstellationLines() {
        // Simplified constellation lines
        // In a full implementation, use actual constellation data
        const constellations = this.generateConstellationData();
        
        constellations.forEach(constellation => {
            this.svg.append('path')
                .datum(constellation.points)
                .attr('d', d3.line()
                    .x(d => this.xScale(d.ra))
                    .y(d => this.yScale(d.dec))
                )
                .attr('stroke', '#333366')
                .attr('stroke-width', 1)
                .attr('fill', 'none')
                .attr('opacity', 0.3);
        });
    }
    
    addMilkyWay() {
        // Simplified Milky Way representation
        this.svg.append('ellipse')
            .attr('cx', this.width / 2)
            .attr('cy', this.height / 2)
            .attr('rx', this.width * 0.4)
            .attr('ry', this.height * 0.2)
            .attr('fill', 'url(#milkyWayGradient)')
            .attr('opacity', 0.1);
        
        // Add gradient definition
        const defs = this.svg.append('defs');
        const gradient = defs.append('linearGradient')
            .attr('id', 'milkyWayGradient')
            .attr('x1', '0%')
            .attr('y1', '0%')
            .attr('x2', '100%')
            .attr('y2', '100%');
            
        gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#ffffff')
            .attr('stop-opacity', 0.1);
            
        gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#ccccff')
            .attr('stop-opacity', 0.05);
    }
    
    generateSampleData() {
        // Generate sample data for demonstration
        const classifications = ['Confirmed Exoplanet', 'Candidate', 'False Positive'];
        const data = [];
        
        for (let i = 0; i < 100; i++) {
            data.push({
                id: `KOI-${1000 + i}`,
                name: `KOI-${1000 + i}`,
                ra: Math.random() * 360,
                dec: (Math.random() - 0.5) * 180,
                classification: classifications[Math.floor(Math.random() * 3)],
                period: Math.random() * 100,
                radius: Math.random() * 15,
                temperature: 300 + Math.random() * 1700,
                depth: Math.random() * 2000,
                snr: Math.random() * 20,
                magnitude: 8 + Math.random() * 7
            });
        }
        
        return data;
    }
    
    generateConstellationData() {
        // Simplified constellation data
        return [
            {
                name: 'Ursa Major',
                points: [
                    { ra: 160, dec: 56 }, { ra: 165, dec: 54 },
                    { ra: 170, dec: 52 }, { ra: 175, dec: 50 }
                ]
            }
            // Add more constellations as needed
        ];
    }
    
    filterByClassification(classification) {
        if (classification === 'all') {
            this.svg.selectAll('.exoplanet')
                .transition()
                .duration(500)
                .attr('opacity', 0.8);
        } else {
            this.svg.selectAll('.exoplanet')
                .transition()
                .duration(500)
                .attr('opacity', d => d.classification === classification ? 0.8 : 0.1);
        }
    }
}

// Initialize star map when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const starMap = new StarMap('starmap-container', 800, 600);
    
    // Listen for exoplanet selection
    document.addEventListener('exoplanetSelected', function(event) {
        const exoplanet = event.detail;
        console.log('Selected exoplanet:', exoplanet);
        // Update details panel or trigger other actions
    });
});
