/**
 * breathing_ball.js
 * Visualisatie van een ademhalingscyclus:
 * - Responsive: past zich automatisch aan schermbreedte aan
 * - Soepele sinus-achtige lijnen
 * - Matplotlib-stijl assen en grid
 */

class BreathingBall {
    constructor(canvas, config) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.config = config; 
        
        this.cycleDuration = config.inhale + config.inhaleHold + config.exhale + config.exhaleHold;
        this.startTime = performance.now();
        this.isRunning = true;
        this.animationFrameId = null;

        // Kleuren en instellingen
        this.colors = {
            graph: '#00ffff',      
            ball: '#3498db',       
            ballBorder: '#ffffff',
            axis: '#bdc3c7',       
            grid: '#465c6b',       
            text: '#ecf0f1'        
        };

        this.ballRadius = 12;
        // Marges (iets kleiner voor mobiel)
        this.padding = { top: 20, right: 20, bottom: 30, left: 35 };
        this.viewSeconds = 12; 

        // --- RESPONSIVE LOGICA ---
        // Bind de resize functie zodat 'this' blijft werken
        this.resize = this.resize.bind(this);
        // Voeg luisteraar toe voor schermkanteling/resize
        window.addEventListener('resize', this.resize);
        // Roep 1x aan bij start
        this.resize();

        // Start animatie
        this.animate = this.animate.bind(this);
        this.animationFrameId = requestAnimationFrame(this.animate);
    }

    /**
     * Past de canvas grootte aan op basis van de container.
     */
    resize() {
        // Haal de breedte van het 'ouder' element op (bijv. de div eromheen)
        const parent = this.canvas.parentElement;
        if (parent) {
            // Zet canvas breedte op 100% van de container
            // We trekken er iets af voor padding van de container (optioneel, hier veiligheidsmarge)
            const newWidth = parent.clientWidth - (getComputedStyle(parent).paddingLeft.replace('px','') * 2);
            
            this.canvas.width = newWidth;
            
            // Hoogte: behoud een mooie verhouding (bijv. 3:2), maar niet hoger dan 400px
            // Op mobiel wil je hem misschien iets minder hoog hebben
            const ratio = window.innerWidth < 600 ? 0.8 : 0.6; 
            this.canvas.height = Math.min(400, newWidth * ratio);
        }
    }

    interpolate(t) {
        return (1 - Math.cos(t * Math.PI)) / 2;
    }

    calculateY(timeInSeconds) {
        const { inhale, inhaleHold, exhale, exhaleHold } = this.config;
        const totalTime = this.cycleDuration;
        
        let t = timeInSeconds % totalTime;
        if (t < 0) t += totalTime;
        
        let y; 

        if (t < inhale) {
            y = this.interpolate(t / inhale);
        } else if (t < inhale + inhaleHold) {
            y = 1;
        } else if (t < inhale + inhaleHold + exhale) {
            y = 1 - this.interpolate((t - (inhale + inhaleHold)) / exhale);
        } else {
            y = 0;
        }
        return y; 
    }

    drawGrid(width, height) {
        const { ctx, padding, viewSeconds } = this;
        const graphWidth = width - padding.left - padding.right;
        const graphHeight = height - padding.top - padding.bottom;
        const originY = height - padding.bottom;
        const originX = padding.left;

        ctx.lineWidth = 1;
        ctx.font = "10px monospace"; // Iets kleiner lettertype voor mobiel
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        // Y-AS
        const ySteps = [0, 0.5, 1.0];
        ySteps.forEach(val => {
            const yPlot = 0.1 + (val * 0.8); 
            const pixelY = originY - (yPlot * graphHeight);

            ctx.beginPath();
            ctx.strokeStyle = this.colors.grid;
            ctx.setLineDash([2, 4]);
            ctx.moveTo(originX, pixelY);
            ctx.lineTo(originX + graphWidth, pixelY);
            ctx.stroke();

            ctx.fillStyle = this.colors.axis;
            ctx.setLineDash([]);
            ctx.textAlign = "right";
            ctx.fillText(val.toFixed(1), originX - 5, pixelY);
        });

        // X-AS
        const centerX = originX + graphWidth / 2;
        const secondsHalf = viewSeconds / 2;
        
        // Dynamische stapgrootte: op kleine schermen minder labels
        const step = width < 400 ? 4 : 2; 
        
        for (let t = -Math.ceil(secondsHalf); t <= Math.ceil(secondsHalf); t += step) {
            const xOffset = (t / secondsHalf) * (graphWidth / 2);
            const pixelX = centerX + xOffset;

            if (pixelX >= originX && pixelX <= originX + graphWidth) {
                ctx.beginPath();
                ctx.strokeStyle = (t === 0) ? '#7f8c8d' : this.colors.grid;
                ctx.lineWidth = (t === 0) ? 1.5 : 1;
                ctx.setLineDash([2, 4]);
                ctx.moveTo(pixelX, padding.top);
                ctx.lineTo(pixelX, originY);
                ctx.stroke();

                ctx.fillStyle = this.colors.axis;
                ctx.setLineDash([]);
                ctx.textAlign = "center";
                ctx.fillText(t + "s", pixelX, originY + 15);
            }
        }
        
        // Kader
        ctx.beginPath();
        ctx.strokeStyle = this.colors.axis;
        ctx.rect(originX, padding.top, graphWidth, graphHeight);
        ctx.stroke();
    }

    draw(timeElapsed) {
        const { ctx, canvas, padding, viewSeconds } = this;
        const width = canvas.width;
        const height = canvas.height;
        const graphWidth = width - padding.left - padding.right;
        const graphHeight = height - padding.top - padding.bottom;
        const originY = height - padding.bottom;
        const originX = padding.left;

        ctx.clearRect(0, 0, width, height);
        this.drawGrid(width, height);

        // Sinus-Curve
        ctx.beginPath();
        ctx.strokeStyle = this.colors.graph;
        ctx.lineWidth = 3;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";

        const pixelsPerSecond = graphWidth / viewSeconds;
        const startTimeInView = timeElapsed - (viewSeconds / 2);
        const pixelStep = 2; 

        for (let px = 0; px <= graphWidth; px += pixelStep) {
            const t = startTimeInView + (px / pixelsPerSecond);
            const val = this.calculateY(t);
            const yPlot = 0.1 + (val * 0.8); 
            const pixelY = originY - (yPlot * graphHeight);
            const pixelX = originX + px;

            if (px === 0) ctx.moveTo(pixelX, pixelY);
            else ctx.lineTo(pixelX, pixelY);
        }
        ctx.stroke();

        // Balletje
        const centerX = originX + graphWidth / 2;
        const valNow = this.calculateY(timeElapsed);
        const yPlotNow = 0.1 + (valNow * 0.8);
        const centerY = originY - (yPlotNow * graphHeight);

        ctx.beginPath();
        ctx.arc(centerX, centerY, this.ballRadius, 0, Math.PI * 2);
        ctx.fillStyle = this.colors.ball;
        ctx.fill();
        ctx.strokeStyle = this.colors.ballBorder;
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    animate(timestamp) {
        if (!this.isRunning) return;
        const timeElapsed = (timestamp - this.startTime) / 1000;
        this.draw(timeElapsed);
        this.animationFrameId = requestAnimationFrame(this.animate);
    }
    
    stop() {
        this.isRunning = false;
        window.removeEventListener('resize', this.resize); // Netjes opruimen
        if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);
    }
}