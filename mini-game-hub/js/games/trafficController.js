/**
 * Game 5: Traffic Controller
 * 4-Way intersection flow management simulation.
 */

window.TrafficController = (function () {
  let container = null;
  let host = null;
  let canvas = null;
  let ctx = null;
  let animationId = null;
  let spawnInterval = null;
  let level = 1;
  let score = 0;
  let carsPassed = 0;
  let isGameOver = false;

  // Traffic light state: 'NS_GREEN' or 'EW_GREEN'
  let lightState = 'NS_GREEN';

  // Cars collection
  let cars = [];
  const CAR_WIDTH = 22;
  const CAR_LENGTH = 38;
  const ROAD_WIDTH = 90;
  const CANVAS_SIZE = 540;
  const CENTER = CANVAS_SIZE / 2;

  // Stop lines
  const STOP_LINES = {
    NORTH: CENTER - ROAD_WIDTH / 2 - CAR_LENGTH / 2 - 4, // y
    SOUTH: CENTER + ROAD_WIDTH / 2 + CAR_LENGTH / 2 + 4, // y
    WEST: CENTER - ROAD_WIDTH / 2 - CAR_LENGTH / 2 - 4,  // x
    EAST: CENTER + ROAD_WIDTH / 2 + CAR_LENGTH / 2 + 4   // x
  };

  const CAR_COLORS = ['#00f0ff', '#ff007f', '#00ff88', '#ffaa00', '#9d4edd', '#38bdf8'];

  function renderUI() {
    container.innerHTML = `
      <div class="game-container">
        <div class="game-instruction-banner">
          Switch traffic lights to prevent accidents and keep intersection queues moving smoothly.
        </div>
        <div class="traffic-canvas-wrapper">
          <canvas id="traffic-canvas" width="${CANVAS_SIZE}" height="${CANVAS_SIZE}"></canvas>
        </div>
        <div class="traffic-ctrl-bar">
          <button class="btn-traffic-toggle" id="btn-toggle-lights">
            <span class="traffic-indicator-dot ${lightState === 'NS_GREEN' ? 'green' : ''}" id="ind-ns"></span>
            NORTH / SOUTH
            <span style="margin: 0 0.5rem; opacity: 0.5;">|</span>
            <span class="traffic-indicator-dot ${lightState === 'EW_GREEN' ? 'green' : ''}" id="ind-ew"></span>
            EAST / WEST
          </button>
        </div>
      </div>
    `;

    canvas = container.querySelector('#traffic-canvas');
    ctx = canvas.getContext('2d');

    const toggleBtn = container.querySelector('#btn-toggle-lights');
    toggleBtn.addEventListener('click', toggleLight);
    canvas.addEventListener('click', toggleLight);
  }

  function toggleLight() {
    if (isGameOver) return;
    lightState = (lightState === 'NS_GREEN') ? 'EW_GREEN' : 'NS_GREEN';
    host.playSound('click');

    const indNs = container.querySelector('#ind-ns');
    const indEw = container.querySelector('#ind-ew');
    if (indNs && indEw) {
      if (lightState === 'NS_GREEN') {
        indNs.classList.add('green');
        indEw.classList.remove('green');
      } else {
        indNs.classList.remove('green');
        indEw.classList.add('green');
      }
    }
  }

  class Car {
    constructor(direction) {
      this.direction = direction; // 'N', 'S', 'E', 'W'
      this.color = CAR_COLORS[Math.floor(Math.random() * CAR_COLORS.length)];
      this.speed = 2.4 + Math.random() * 0.8;
      this.currentSpeed = this.speed;
      this.waitingTime = 0;

      // Position
      switch (direction) {
        case 'N': // Moving South
          this.x = CENTER - ROAD_WIDTH / 4;
          this.y = -CAR_LENGTH;
          this.vx = 0;
          this.vy = this.speed;
          break;
        case 'S': // Moving North
          this.x = CENTER + ROAD_WIDTH / 4;
          this.y = CANVAS_SIZE + CAR_LENGTH;
          this.vx = 0;
          this.vy = -this.speed;
          break;
        case 'W': // Moving East
          this.x = -CAR_LENGTH;
          this.y = CENTER + ROAD_WIDTH / 4;
          this.vx = this.speed;
          this.vy = 0;
          break;
        case 'E': // Moving West
          this.x = CANVAS_SIZE + CAR_LENGTH;
          this.y = CENTER - ROAD_WIDTH / 4;
          this.vx = -this.speed;
          this.vy = 0;
          break;
      }
    }

    update(leadingCar) {
      let mustStop = false;

      // Check red light stop lines
      if (this.direction === 'N') {
        const isRed = lightState !== 'NS_GREEN';
        if (isRed && this.y < STOP_LINES.NORTH && this.y + this.speed >= STOP_LINES.NORTH - 10) {
          mustStop = true;
        }
      } else if (this.direction === 'S') {
        const isRed = lightState !== 'NS_GREEN';
        if (isRed && this.y > STOP_LINES.SOUTH && this.y - this.speed <= STOP_LINES.SOUTH + 10) {
          mustStop = true;
        }
      } else if (this.direction === 'W') {
        const isRed = lightState !== 'EW_GREEN';
        if (isRed && this.x < STOP_LINES.WEST && this.x + this.speed >= STOP_LINES.WEST - 10) {
          mustStop = true;
        }
      } else if (this.direction === 'E') {
        const isRed = lightState !== 'EW_GREEN';
        if (isRed && this.x > STOP_LINES.EAST && this.x - this.speed <= STOP_LINES.EAST + 10) {
          mustStop = true;
        }
      }

      // Check queue behind car ahead
      if (leadingCar) {
        const dist = Math.hypot(this.x - leadingCar.x, this.y - leadingCar.y);
        if (dist < CAR_LENGTH + 14) {
          mustStop = true;
        }
      }

      if (mustStop) {
        this.currentSpeed = 0;
        this.waitingTime += 1 / 60;
      } else {
        this.currentSpeed = this.speed;
      }

      this.x += (this.vx !== 0 ? Math.sign(this.vx) * this.currentSpeed : 0);
      this.y += (this.vy !== 0 ? Math.sign(this.vy) * this.currentSpeed : 0);
    }

    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);

      // Rotate based on direction
      if (this.direction === 'N') ctx.rotate(Math.PI);
      else if (this.direction === 'S') ctx.rotate(0);
      else if (this.direction === 'W') ctx.rotate(Math.PI / 2);
      else if (this.direction === 'E') ctx.rotate(-Math.PI / 2);

      // Car body
      ctx.fillStyle = this.color;
      ctx.shadowColor = this.color;
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.roundRect(-CAR_WIDTH / 2, -CAR_LENGTH / 2, CAR_WIDTH, CAR_LENGTH, 6);
      ctx.fill();

      // Windshield
      ctx.fillStyle = '#080c14';
      ctx.fillRect(-CAR_WIDTH / 2 + 3, -CAR_LENGTH / 2 + 8, CAR_WIDTH - 6, 8);

      // Headlights
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(-CAR_WIDTH / 2 + 2, CAR_LENGTH / 2 - 4, 4, 3);
      ctx.fillRect(CAR_WIDTH / 2 - 6, CAR_LENGTH / 2 - 4, 4, 3);

      // Warning patience indicator if waiting too long
      if (this.waitingTime > 5) {
        ctx.fillStyle = '#ff334b';
        ctx.beginPath();
        ctx.arc(0, -CAR_LENGTH / 2 - 8, 4, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.restore();
    }

    isOffscreen() {
      return (
        this.x < -CAR_LENGTH * 2 ||
        this.x > CANVAS_SIZE + CAR_LENGTH * 2 ||
        this.y < -CAR_LENGTH * 2 ||
        this.y > CANVAS_SIZE + CAR_LENGTH * 2
      );
    }
  }

  function spawnCar() {
    if (isGameOver) return;
    const directions = ['N', 'S', 'E', 'W'];
    const dir = directions[Math.floor(Math.random() * directions.length)];

    // Check if spawn point is currently blocked
    const blocked = cars.some(c => {
      if (c.direction !== dir) return false;
      if (dir === 'N' && c.y < 30) return true;
      if (dir === 'S' && c.y > CANVAS_SIZE - 30) return true;
      if (dir === 'W' && c.x < 30) return true;
      if (dir === 'E' && c.x > CANVAS_SIZE - 30) return true;
      return false;
    });

    if (!blocked) {
      cars.push(new Car(dir));
    }
  }

  function checkCollisions() {
    const interMin = CENTER - ROAD_WIDTH / 2 + 5;
    const interMax = CENTER + ROAD_WIDTH / 2 - 5;

    for (let i = 0; i < cars.length; i++) {
      const c1 = cars[i];

      // Check excessive wait time failure (> 12s)
      if (c1.waitingTime > 12) {
        triggerGameOver("Gridlock! Driver frustration caused an intersection standstill.");
        return;
      }

      for (let j = i + 1; j < cars.length; j++) {
        const c2 = cars[j];

        // Collision only possible inside or near intersection
        const inside1 = (c1.x > interMin && c1.x < interMax && c1.y > interMin && c1.y < interMax);
        const inside2 = (c2.x > interMin && c2.x < interMax && c2.y > interMin && c2.y < interMax);

        if (inside1 || inside2) {
          const dist = Math.hypot(c1.x - c2.x, c1.y - c2.y);
          if (dist < CAR_WIDTH + 6) {
            triggerGameOver("Collision in the intersection! Cars crashed.");
            return;
          }
        }
      }
    }
  }

  function triggerGameOver(msg) {
    isGameOver = true;
    destroyLoop();
    host.playSound('explosion');

    host.endGame({
      win: false,
      score,
      title: 'TRAFFIC ACCIDENT',
      message: msg,
      details: `Safe Vehicles Navigated: ${carsPassed}`
    });
  }

  function drawIntersection() {
    ctx.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

    // Background grass / city blocks
    ctx.fillStyle = '#0a101b';
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

    // Roads (Asphalt)
    ctx.fillStyle = '#161f30';
    // Vertical road
    ctx.fillRect(CENTER - ROAD_WIDTH / 2, 0, ROAD_WIDTH, CANVAS_SIZE);
    // Horizontal road
    ctx.fillRect(0, CENTER - ROAD_WIDTH / 2, CANVAS_SIZE, ROAD_WIDTH);

    // Road markings (lane dashes)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
    ctx.lineWidth = 2;
    ctx.setLineDash([12, 12]);

    // Vertical center line
    ctx.beginPath();
    ctx.moveTo(CENTER, 0);
    ctx.lineTo(CENTER, CENTER - ROAD_WIDTH / 2);
    ctx.moveTo(CENTER, CENTER + ROAD_WIDTH / 2);
    ctx.lineTo(CENTER, CANVAS_SIZE);
    ctx.stroke();

    // Horizontal center line
    ctx.beginPath();
    ctx.moveTo(0, CENTER);
    ctx.lineTo(CENTER - ROAD_WIDTH / 2, CENTER);
    ctx.moveTo(CENTER + ROAD_WIDTH / 2, CENTER);
    ctx.lineTo(CANVAS_SIZE, CENTER);
    ctx.stroke();

    ctx.setLineDash([]); // Reset dash

    // Draw Stop lines
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 4;

    // North stop line
    ctx.beginPath();
    ctx.moveTo(CENTER - ROAD_WIDTH / 2, CENTER - ROAD_WIDTH / 2);
    ctx.lineTo(CENTER, CENTER - ROAD_WIDTH / 2);
    ctx.stroke();

    // South stop line
    ctx.beginPath();
    ctx.moveTo(CENTER, CENTER + ROAD_WIDTH / 2);
    ctx.lineTo(CENTER + ROAD_WIDTH / 2, CENTER + ROAD_WIDTH / 2);
    ctx.stroke();

    // West stop line
    ctx.beginPath();
    ctx.moveTo(CENTER - ROAD_WIDTH / 2, CENTER);
    ctx.lineTo(CENTER - ROAD_WIDTH / 2, CENTER + ROAD_WIDTH / 2);
    ctx.stroke();

    // East stop line
    ctx.beginPath();
    ctx.moveTo(CENTER + ROAD_WIDTH / 2, CENTER - ROAD_WIDTH / 2);
    ctx.lineTo(CENTER + ROAD_WIDTH / 2, CENTER);
    ctx.stroke();

    // Draw Traffic Lights
    drawTrafficLight(CENTER - ROAD_WIDTH / 2 - 16, CENTER - ROAD_WIDTH / 2 - 16, lightState === 'NS_GREEN');
    drawTrafficLight(CENTER + ROAD_WIDTH / 2 + 16, CENTER + ROAD_WIDTH / 2 + 16, lightState === 'NS_GREEN');
    drawTrafficLight(CENTER - ROAD_WIDTH / 2 - 16, CENTER + ROAD_WIDTH / 2 + 16, lightState === 'EW_GREEN');
    drawTrafficLight(CENTER + ROAD_WIDTH / 2 + 16, CENTER - ROAD_WIDTH / 2 - 16, lightState === 'EW_GREEN');
  }

  function drawTrafficLight(x, y, isGreen) {
    ctx.fillStyle = '#060a12';
    ctx.fillRect(x - 8, y - 8, 16, 16);

    ctx.fillStyle = isGreen ? '#00ff88' : '#ff334b';
    ctx.shadowColor = isGreen ? '#00ff88' : '#ff334b';
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.arc(x, y, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  function gameLoop() {
    if (isGameOver) return;

    drawIntersection();

    // Group cars by direction to handle leading car queues
    ['N', 'S', 'E', 'W'].forEach(dir => {
      const dirCars = cars.filter(c => c.direction === dir);
      // Sort so front car is first
      if (dir === 'N') dirCars.sort((a, b) => b.y - a.y);
      if (dir === 'S') dirCars.sort((a, b) => a.y - b.y);
      if (dir === 'W') dirCars.sort((a, b) => b.x - a.x);
      if (dir === 'E') dirCars.sort((a, b) => a.x - b.x);

      for (let i = 0; i < dirCars.length; i++) {
        const leading = (i > 0) ? dirCars[i - 1] : null;
        dirCars[i].update(leading);
        dirCars[i].draw(ctx);
      }
    });

    // Check cars passed
    for (let i = cars.length - 1; i >= 0; i--) {
      if (cars[i].isOffscreen()) {
        cars.splice(i, 1);
        carsPassed++;
        score += 25;
        host.updateScore(score);

        // Level up every 10 cars
        const newLevel = 1 + Math.floor(carsPassed / 10);
        if (newLevel !== level) {
          level = newLevel;
          host.updateLevel(level);
          host.playSound('success');
          adjustSpawnRate();
        }
      }
    }

    checkCollisions();

    animationId = requestAnimationFrame(gameLoop);
  }

  function adjustSpawnRate() {
    if (spawnInterval) clearInterval(spawnInterval);
    const ms = Math.max(900, 2200 - level * 130);
    spawnInterval = setInterval(spawnCar, ms);
  }

  function destroyLoop() {
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }
    if (spawnInterval) {
      clearInterval(spawnInterval);
      spawnInterval = null;
    }
  }

  return {
    id: 'trafficController',
    name: 'Traffic Controller',
    description: 'Control traffic signals to prevent intersection crashes and manage queues.',
    difficulty: 'Medium',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="2" width="12" height="20" rx="3"></rect><circle cx="12" cy="7" r="2" fill="currentColor"></circle><circle cx="12" cy="12" r="2"></circle><circle cx="12" cy="17" r="2"></circle></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      destroyLoop();
      level = 1;
      score = 0;
      carsPassed = 0;
      isGameOver = false;
      lightState = 'NS_GREEN';
      cars = [];

      host.updateScore(score);
      host.updateLevel(level);
      host.updateTime(0); // Elapsed/Flow indicator

      renderUI();
      adjustSpawnRate();
      spawnCar();

      animationId = requestAnimationFrame(gameLoop);
    },

    destroy() {
      destroyLoop();
      isGameOver = true;
      if (container) {
        container.innerHTML = '';
      }
    }
  };
})();
