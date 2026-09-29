/**
 * Game 6: Virus Evolution
 * Nanobot/organism survival and upgrade simulation.
 */

window.VirusEvolution = (function () {
  let container = null;
  let host = null;
  let canvas = null;
  let ctx = null;
  let animationId = null;
  let spawnInterval = null;
  let enemyInterval = null;
  let isGameOver = false;

  let level = 1;
  let score = 0;
  let energy = 0;

  // Upgrades
  let upgrades = {
    speed: { level: 1, cost: 40, max: 5 },
    defense: { level: 0, cost: 60, max: 4 },
    reproduction: { level: 0, cost: 100, max: 3 },
    vision: { level: 1, cost: 50, max: 5 }
  };

  // Player organism state
  let player = {
    x: 300,
    y: 190,
    radius: 16,
    speed: 3,
    shields: 0,
    magnetRadius: 40,
    targetX: 300,
    targetY: 190
  };

  let helpers = [];
  let food = [];
  let enemies = [];

  const CANVAS_WIDTH = 680;
  const CANVAS_HEIGHT = 380;

  function renderUI() {
    container.innerHTML = `
      <div class="game-container">
        <div class="game-instruction-banner">
          Guide your cell with the mouse. Absorb nutrients, upgrade your biology, and evade phages!
        </div>
        <div class="evolution-workspace">
          <div class="evolution-canvas-box">
            <canvas id="virus-canvas" width="${CANVAS_WIDTH}" height="${CANVAS_HEIGHT}"></canvas>
            <div class="evolution-hud" id="evo-hud">
              ⚡ Energy: <span id="hud-energy">0</span> | 🛡 Shields: <span id="hud-shields">0</span>
            </div>
          </div>
          <div class="evolution-shop" id="evo-shop"></div>
        </div>
      </div>
    `;

    canvas = container.querySelector('#virus-canvas');
    ctx = canvas.getContext('2d');

    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('touchmove', onTouchMove, { passive: false });

    renderShop();
  }

  function onMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = CANVAS_WIDTH / rect.width;
    const scaleY = CANVAS_HEIGHT / rect.height;
    player.targetX = (e.clientX - rect.left) * scaleX;
    player.targetY = (e.clientY - rect.top) * scaleY;
  }

  function onTouchMove(e) {
    e.preventDefault();
    if (!e.touches.length) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = CANVAS_WIDTH / rect.width;
    const scaleY = CANVAS_HEIGHT / rect.height;
    player.targetX = (e.touches[0].clientX - rect.left) * scaleX;
    player.targetY = (e.touches[0].clientY - rect.top) * scaleY;
  }

  function renderShop() {
    const shopEl = container.querySelector('#evo-shop');
    if (!shopEl) return;

    shopEl.innerHTML = `
      <div class="upgrade-card">
        <span class="upgrade-name">⚡ Speed</span>
        <span class="upgrade-level">LVL ${upgrades.speed.level}/${upgrades.speed.max}</span>
        <button class="btn-buy-upgrade" data-type="speed" ${canAfford('speed') ? '' : 'disabled'}>
          ${upgrades.speed.level >= upgrades.speed.max ? 'MAX' : `BUY: ${upgrades.speed.cost}`}
        </button>
      </div>

      <div class="upgrade-card">
        <span class="upgrade-name">🛡 Defense</span>
        <span class="upgrade-level">LVL ${upgrades.defense.level}/${upgrades.defense.max}</span>
        <button class="btn-buy-upgrade" data-type="defense" ${canAfford('defense') ? '' : 'disabled'}>
          ${upgrades.defense.level >= upgrades.defense.max ? 'MAX' : `BUY: ${upgrades.defense.cost}`}
        </button>
      </div>

      <div class="upgrade-card">
        <span class="upgrade-name">🧬 Clone Helper</span>
        <span class="upgrade-level">LVL ${upgrades.reproduction.level}/${upgrades.reproduction.max}</span>
        <button class="btn-buy-upgrade" data-type="reproduction" ${canAfford('reproduction') ? '' : 'disabled'}>
          ${upgrades.reproduction.level >= upgrades.reproduction.max ? 'MAX' : `BUY: ${upgrades.reproduction.cost}`}
        </button>
      </div>

      <div class="upgrade-card">
        <span class="upgrade-name">🧲 Bio-Magnet</span>
        <span class="upgrade-level">LVL ${upgrades.vision.level}/${upgrades.vision.max}</span>
        <button class="btn-buy-upgrade" data-type="vision" ${canAfford('vision') ? '' : 'disabled'}>
          ${upgrades.vision.level >= upgrades.vision.max ? 'MAX' : `BUY: ${upgrades.vision.cost}`}
        </button>
      </div>
    `;

    const buyBtns = shopEl.querySelectorAll('.btn-buy-upgrade');
    buyBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const type = btn.getAttribute('data-type');
        buyUpgrade(type);
      });
    });
  }

  function canAfford(type) {
    const up = upgrades[type];
    return up.level < up.max && energy >= up.cost;
  }

  function buyUpgrade(type) {
    const up = upgrades[type];
    if (!canAfford(type)) return;

    energy -= up.cost;
    up.level++;
    up.cost = Math.floor(up.cost * 1.8);
    host.playSound('powerup');

    // Apply upgrade effects
    if (type === 'speed') player.speed = 3 + up.level * 1.2;
    if (type === 'defense') {
      player.shields++;
      updateHUD();
    }
    if (type === 'vision') player.magnetRadius = 40 + up.level * 30;
    if (type === 'reproduction') {
      helpers.push({
        x: player.x + (Math.random() * 40 - 20),
        y: player.y + (Math.random() * 40 - 20),
        radius: 8,
        speed: 2.6
      });
    }

    score += 150;
    host.updateScore(score);

    // Calculate level as total upgrades
    level = 1 + Object.values(upgrades).reduce((sum, u) => sum + u.level, 0);
    host.updateLevel(level);

    renderShop();
    updateHUD();
  }

  function updateHUD() {
    const energyEl = container.querySelector('#hud-energy');
    const shieldsEl = container.querySelector('#hud-shields');
    if (energyEl) energyEl.textContent = energy;
    if (shieldsEl) shieldsEl.textContent = player.shields;
  }

  function spawnNutrient() {
    if (food.length >= 25) return;
    food.push({
      x: 20 + Math.random() * (CANVAS_WIDTH - 40),
      y: 20 + Math.random() * (CANVAS_HEIGHT - 40),
      radius: 4 + Math.random() * 3,
      hue: Math.floor(Math.random() * 360)
    });
  }

  function spawnEnemy() {
    if (isGameOver || enemies.length >= 2 + Math.floor(level / 2)) return;
    // Spawn from screen edges
    const fromSide = Math.random() > 0.5;
    const x = fromSide ? (Math.random() > 0.5 ? 0 : CANVAS_WIDTH) : Math.random() * CANVAS_WIDTH;
    const y = fromSide ? Math.random() * CANVAS_HEIGHT : (Math.random() > 0.5 ? 0 : CANVAS_HEIGHT);

    enemies.push({
      x,
      y,
      radius: 14 + Math.random() * 6,
      speed: 1.2 + Math.min(2.5, level * 0.15),
      pulse: 0
    });
  }

  function gameLoop() {
    if (isGameOver) return;

    ctx.fillStyle = '#060a12';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Subtle petri dish grid background
    ctx.strokeStyle = 'rgba(0, 255, 136, 0.04)';
    ctx.lineWidth = 1;
    for (let x = 0; x < CANVAS_WIDTH; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, CANVAS_HEIGHT);
      ctx.stroke();
    }
    for (let y = 0; y < CANVAS_HEIGHT; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(CANVAS_WIDTH, y);
      ctx.stroke();
    }

    // Update Player movement
    const dx = player.targetX - player.x;
    const dy = player.targetY - player.y;
    const dist = Math.hypot(dx, dy);
    if (dist > 2) {
      player.x += (dx / dist) * Math.min(player.speed, dist);
      player.y += (dy / dist) * Math.min(player.speed, dy);
    }

    // Clamp inside arena
    player.x = Math.max(player.radius, Math.min(CANVAS_WIDTH - player.radius, player.x));
    player.y = Math.max(player.radius, Math.min(CANVAS_HEIGHT - player.radius, player.y));

    // Draw magnet radius field
    if (upgrades.vision.level > 1) {
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.08)';
      ctx.beginPath();
      ctx.arc(player.x, player.y, player.magnetRadius, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Update & Draw Food
    for (let i = food.length - 1; i >= 0; i--) {
      const f = food[i];

      // Magnet pull towards player
      const dPlayer = Math.hypot(player.x - f.x, player.y - f.y);
      if (dPlayer < player.magnetRadius) {
        f.x += ((player.x - f.x) / dPlayer) * 3.5;
        f.y += ((player.y - f.y) / dPlayer) * 3.5;
      }

      // Collect food
      if (dPlayer < player.radius + f.radius) {
        food.splice(i, 1);
        energy += 10;
        score += 15;
        host.updateScore(score);
        host.playSound('click');
        updateHUD();
        renderShop();
        continue;
      }

      // Helper bots collecting food
      for (const h of helpers) {
        const dHelper = Math.hypot(h.x - f.x, h.y - f.y);
        if (dHelper < h.radius + f.radius) {
          food.splice(i, 1);
          energy += 10;
          score += 15;
          host.updateScore(score);
          updateHUD();
          renderShop();
          break;
        }
      }

      // Render nutrient
      ctx.fillStyle = `hsl(${f.hue}, 90%, 65%)`;
      ctx.shadowColor = `hsl(${f.hue}, 90%, 65%)`;
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.arc(f.x, f.y, f.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    // Update & Draw Helper Clones
    helpers.forEach(h => {
      // Find nearest food
      if (food.length > 0) {
        let nearest = food[0];
        let minDist = 9999;
        food.forEach(f => {
          const d = Math.hypot(h.x - f.x, h.y - f.y);
          if (d < minDist) {
            minDist = d;
            nearest = f;
          }
        });

        const hdx = nearest.x - h.x;
        const hdy = nearest.y - h.y;
        const hdist = Math.hypot(hdx, hdy);
        if (hdist > 2) {
          h.x += (hdx / hdist) * h.speed;
          h.y += (hdy / hdist) * h.speed;
        }
      }

      // Draw helper
      ctx.fillStyle = '#00f0ff';
      ctx.shadowColor = '#00f0ff';
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(h.x, h.y, h.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    // Update & Draw Enemies
    for (let i = enemies.length - 1; i >= 0; i--) {
      const en = enemies[i];
      en.pulse += 0.05;

      // Pursue player
      const edx = player.x - en.x;
      const edy = player.y - en.y;
      const edist = Math.hypot(edx, edy);
      if (edist > 2) {
        en.x += (edx / edist) * en.speed;
        en.y += (edy / edist) * en.speed;
      }

      // Collision with player
      if (edist < player.radius + en.radius - 2) {
        if (player.shields > 0) {
          // Shield absorbs enemy!
          player.shields--;
          enemies.splice(i, 1);
          host.playSound('explosion');
          updateHUD();
          continue;
        } else {
          // Death
          triggerGameOver('Engulfed by hostile predatory phages!');
          return;
        }
      }

      // Render Enemy
      ctx.fillStyle = '#ff0055';
      ctx.shadowColor = '#ff0055';
      ctx.shadowBlur = 10;
      ctx.beginPath();
      const currentR = en.radius + Math.sin(en.pulse) * 2;
      ctx.arc(en.x, en.y, currentR, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    // Draw Player Organism
    ctx.save();
    ctx.translate(player.x, player.y);

    // Shield glow if active
    if (player.shields > 0) {
      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = 3;
      ctx.shadowColor = '#00f0ff';
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.arc(0, 0, player.radius + 6, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Cell body
    ctx.fillStyle = '#00ff88';
    ctx.shadowColor = '#00ff88';
    ctx.shadowBlur = 14;
    ctx.beginPath();
    ctx.arc(0, 0, player.radius, 0, Math.PI * 2);
    ctx.fill();

    // Nucleus
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(0, 0, player.radius * 0.4, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();

    animationId = requestAnimationFrame(gameLoop);
  }

  function triggerGameOver(msg) {
    isGameOver = true;
    destroyLoop();
    host.playSound('error');

    host.endGame({
      win: false,
      score,
      title: 'ORGANISM EXTINCT',
      message: msg,
      details: `Evolution Level Reached: ${level}`
    });
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
    if (enemyInterval) {
      clearInterval(enemyInterval);
      enemyInterval = null;
    }
  }

  return {
    id: 'virusEvolution',
    name: 'Virus Evolution',
    description: 'Grow, evolve, purchase genetic upgrades, and avoid predatory phages.',
    difficulty: 'Medium',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="6"></circle><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      destroyLoop();
      level = 1;
      score = 0;
      energy = 20;
      isGameOver = false;

      upgrades = {
        speed: { level: 1, cost: 40, max: 5 },
        defense: { level: 0, cost: 60, max: 4 },
        reproduction: { level: 0, cost: 100, max: 3 },
        vision: { level: 1, cost: 50, max: 5 }
      };

      player = {
        x: 300,
        y: 190,
        radius: 16,
        speed: 3,
        shields: 0,
        magnetRadius: 40,
        targetX: 300,
        targetY: 190
      };

      helpers = [];
      food = [];
      enemies = [];

      host.updateScore(score);
      host.updateLevel(level);
      host.updateTime(0);

      renderUI();
      updateHUD();

      // Seed food
      for (let i = 0; i < 15; i++) spawnNutrient();

      spawnInterval = setInterval(spawnNutrient, 900);
      enemyInterval = setInterval(spawnEnemy, 4000);

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
