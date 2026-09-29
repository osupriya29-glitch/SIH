/**
 * Game 10: Time Loop Escape
 * Temporal paradox puzzle. Cooperate with past recordings of yourself.
 */

window.TimeLoop = (function () {
  let container = null;
  let host = null;
  let canvas = null;
  let ctx = null;
  let animationId = null;
  let loopTimer = null;

  let level = 1;
  let score = 0;
  let loopCount = 1;
  const LOOP_DURATION = 20; // seconds
  let loopTimeLeft = LOOP_DURATION;
  let isGameOver = false;

  // Active player position
  let player = {
    x: 60,
    y: 350,
    vx: 0,
    vy: 0,
    speed: 3.2,
    radius: 12
  };

  // Keyboard input state
  let keys = {
    ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false,
    w: false, s: false, a: false, d: false
  };

  // Recorded paths: array of past loops, each containing array of { x, y } per tick
  let pastGhosts = [];
  let currentRecording = [];
  let currentTick = 0;

  // Room Puzzle Elements
  const CANVAS_WIDTH = 560;
  const CANVAS_HEIGHT = 420;

  const PLATE_1 = { x: 90, y: 110, w: 40, h: 40, active: false };
  const PLATE_2 = { x: 280, y: 230, w: 40, h: 40, active: false };

  const DOOR_1 = { x: 190, y: 80, w: 16, h: 120, open: false };
  const DOOR_2 = { x: 390, y: 200, w: 16, h: 120, open: false };

  const EXIT_PORTAL = { x: 480, y: 90, r: 24 };

  const WALLS = [
    // Outer perimeter
    { x: 0, y: 0, w: CANVAS_WIDTH, h: 16 },
    { x: 0, y: CANVAS_HEIGHT - 16, w: CANVAS_WIDTH, h: 16 },
    { x: 0, y: 0, w: 16, h: CANVAS_HEIGHT },
    { x: CANVAS_WIDTH - 16, y: 0, w: 16, h: CANVAS_HEIGHT },
    // Interior dividing wall 1 (x: 190)
    { x: 190, y: 16, w: 16, h: 64 },
    { x: 190, y: 200, w: 16, h: 204 },
    // Interior dividing wall 2 (x: 390)
    { x: 390, y: 16, w: 16, h: 184 },
    { x: 390, y: 320, w: 16, h: 84 }
  ];

  function renderUI() {
    container.innerHTML = `
      <div class="game-container">
        <div class="game-instruction-banner">
          Step on pressure plates to hold doors open for your future clones across time loops!
        </div>
        <div class="time-loop-wrapper">
          <div class="loop-timeline-bar">
            <span class="loop-counter">⏳ TIMELINE LOOP: <span id="loop-num">1</span></span>
            <span style="font-family: var(--font-mono); color: var(--neon-cyan);">
              Loop Reset in: <strong id="loop-countdown">20s</strong>
            </span>
            <button class="btn-ctrl btn-restart" id="btn-force-loop" style="padding: 0.35rem 0.85rem; font-size: 0.75rem;">
              RESET TIMELINE
            </button>
          </div>

          <div class="loop-canvas-box">
            <canvas id="timeloop-canvas" width="${CANVAS_WIDTH}" height="${CANVAS_HEIGHT}"></canvas>
          </div>

          <div class="loop-controls-hint">
            <span>[W / A / S / D] or [ARROWS] to move active agent</span>
          </div>
        </div>
      </div>
    `;

    canvas = container.querySelector('#timeloop-canvas');
    ctx = canvas.getContext('2d');

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);

    container.querySelector('#btn-force-loop').addEventListener('click', () => {
      if (isGameOver) return;
      host.playSound('click');
      startNextLoop();
    });
  }

  function onKeyDown(e) {
    if (keys.hasOwnProperty(e.key)) {
      keys[e.key] = true;
    }
  }

  function onKeyUp(e) {
    if (keys.hasOwnProperty(e.key)) {
      keys[e.key] = false;
    }
  }

  function startNextLoop() {
    if (isGameOver) return;

    // Save current recording as a ghost
    if (currentRecording.length > 0) {
      pastGhosts.push([...currentRecording]);
    }

    loopCount++;
    currentRecording = [];
    currentTick = 0;
    loopTimeLeft = LOOP_DURATION;

    // Reset player to spawn
    player.x = 60;
    player.y = 350;

    const loopNumEl = container.querySelector('#loop-num');
    if (loopNumEl) loopNumEl.textContent = loopCount;

    host.playSound('powerup');
  }

  function checkCollisions(newX, newY) {
    // Check walls
    for (const w of WALLS) {
      if (
        newX + player.radius > w.x &&
        newX - player.radius < w.x + w.w &&
        newY + player.radius > w.y &&
        newY - player.radius < w.y + w.h
      ) {
        return false;
      }
    }

    // Check closed Door 1
    if (!DOOR_1.open) {
      if (
        newX + player.radius > DOOR_1.x &&
        newX - player.radius < DOOR_1.x + DOOR_1.w &&
        newY + player.radius > DOOR_1.y &&
        newY - player.radius < DOOR_1.y + DOOR_1.h
      ) {
        return false;
      }
    }

    // Check closed Door 2
    if (!DOOR_2.open) {
      if (
        newX + player.radius > DOOR_2.x &&
        newX - player.radius < DOOR_2.x + DOOR_2.w &&
        newY + player.radius > DOOR_2.y &&
        newY - player.radius < DOOR_2.y + DOOR_2.h
      ) {
        return false;
      }
    }

    return true;
  }

  function update() {
    if (isGameOver) return;

    // Handle Input
    let moveX = 0;
    let moveY = 0;
    if (keys.ArrowUp || keys.w) moveY -= 1;
    if (keys.ArrowDown || keys.s) moveY += 1;
    if (keys.ArrowLeft || keys.a) moveX -= 1;
    if (keys.ArrowRight || keys.d) moveX += 1;

    if (moveX !== 0 && moveY !== 0) {
      moveX *= 0.7071;
      moveY *= 0.7071;
    }

    const nextX = player.x + moveX * player.speed;
    const nextY = player.y + moveY * player.speed;

    if (checkCollisions(nextX, player.y)) player.x = nextX;
    if (checkCollisions(player.x, nextY)) player.y = nextY;

    // Record active player's position
    currentRecording.push({ x: player.x, y: player.y });

    // Collect positions of all entities (current player + past ghosts)
    const allPositions = [{ x: player.x, y: player.y }];
    pastGhosts.forEach(ghost => {
      const pos = ghost[currentTick] || ghost[ghost.length - 1];
      if (pos) allPositions.push(pos);
    });

    // Check Pressure Plates
    PLATE_1.active = allPositions.some(p => {
      return (
        p.x >= PLATE_1.x && p.x <= PLATE_1.x + PLATE_1.w &&
        p.y >= PLATE_1.y && p.y <= PLATE_1.y + PLATE_1.h
      );
    });
    DOOR_1.open = PLATE_1.active;

    PLATE_2.active = allPositions.some(p => {
      return (
        p.x >= PLATE_2.x && p.x <= PLATE_2.x + PLATE_2.w &&
        p.y >= PLATE_2.y && p.y <= PLATE_2.y + PLATE_2.h
      );
    });
    DOOR_2.open = PLATE_2.active;

    // Check Exit Portal
    const distToExit = Math.hypot(player.x - EXIT_PORTAL.x, player.y - EXIT_PORTAL.y);
    if (distToExit < player.radius + EXIT_PORTAL.r) {
      triggerVictory();
      return;
    }

    currentTick++;
  }

  function draw() {
    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Floor
    ctx.fillStyle = '#0a0f1b';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Walls
    ctx.fillStyle = '#1e293b';
    WALLS.forEach(w => ctx.fillRect(w.x, w.y, w.w, w.h));

    // Pressure Plates
    // Plate 1
    ctx.fillStyle = PLATE_1.active ? '#00ff88' : '#334155';
    ctx.shadowColor = PLATE_1.active ? '#00ff88' : 'transparent';
    ctx.shadowBlur = PLATE_1.active ? 10 : 0;
    ctx.fillRect(PLATE_1.x, PLATE_1.y, PLATE_1.w, PLATE_1.h);
    ctx.shadowBlur = 0;

    // Plate 2
    ctx.fillStyle = PLATE_2.active ? '#00f0ff' : '#334155';
    ctx.shadowColor = PLATE_2.active ? '#00f0ff' : 'transparent';
    ctx.shadowBlur = PLATE_2.active ? 10 : 0;
    ctx.fillRect(PLATE_2.x, PLATE_2.y, PLATE_2.w, PLATE_2.h);
    ctx.shadowBlur = 0;

    // Security Doors (Laser barriers)
    // Door 1
    if (!DOOR_1.open) {
      ctx.fillStyle = '#ff0055';
      ctx.shadowColor = '#ff0055';
      ctx.shadowBlur = 12;
      ctx.fillRect(DOOR_1.x, DOOR_1.y, DOOR_1.w, DOOR_1.h);
      ctx.shadowBlur = 0;
    } else {
      ctx.strokeStyle = 'rgba(0, 255, 136, 0.4)';
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(DOOR_1.x, DOOR_1.y, DOOR_1.w, DOOR_1.h);
      ctx.setLineDash([]);
    }

    // Door 2
    if (!DOOR_2.open) {
      ctx.fillStyle = '#ff0055';
      ctx.shadowColor = '#ff0055';
      ctx.shadowBlur = 12;
      ctx.fillRect(DOOR_2.x, DOOR_2.y, DOOR_2.w, DOOR_2.h);
      ctx.shadowBlur = 0;
    } else {
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)';
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(DOOR_2.x, DOOR_2.y, DOOR_2.w, DOOR_2.h);
      ctx.setLineDash([]);
    }

    // Exit Portal
    ctx.fillStyle = 'rgba(157, 78, 221, 0.25)';
    ctx.strokeStyle = '#9d4edd';
    ctx.lineWidth = 3;
    ctx.shadowColor = '#9d4edd';
    ctx.shadowBlur = 16;
    ctx.beginPath();
    ctx.arc(EXIT_PORTAL.x, EXIT_PORTAL.y, EXIT_PORTAL.r, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Draw Past Ghost Clones
    pastGhosts.forEach((ghost, gIdx) => {
      const pos = ghost[currentTick] || ghost[ghost.length - 1];
      if (pos) {
        ctx.fillStyle = 'rgba(0, 240, 255, 0.45)';
        ctx.shadowColor = '#00f0ff';
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, player.radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#ffffff';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`G${gIdx + 1}`, pos.x, pos.y + 3);
        ctx.shadowBlur = 0;
      }
    });

    // Draw Active Player
    ctx.fillStyle = '#00ff88';
    ctx.shadowColor = '#00ff88';
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#060a12';
    ctx.font = 'bold 10px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('YOU', player.x, player.y + 3);
    ctx.shadowBlur = 0;
  }

  function gameLoop() {
    if (isGameOver) return;
    update();
    draw();
    animationId = requestAnimationFrame(gameLoop);
  }

  function triggerVictory() {
    isGameOver = true;
    destroyTimers();
    host.playSound('win');
    score = Math.max(100, 1000 - loopCount * 150 + loopTimeLeft * 20);
    host.updateScore(score);

    host.endGame({
      win: true,
      score,
      title: 'PARADOX RESOLVED!',
      message: `You broke the temporal loop through temporal self-cooperation in ${loopCount} loops!`,
      details: `Active Time Clones: ${pastGhosts.length}`
    });
  }

  function startLoopCountdown() {
    destroyTimers();
    loopTimeLeft = LOOP_DURATION;
    updateLoopHUD();

    loopTimer = setInterval(() => {
      loopTimeLeft--;
      updateLoopHUD();

      if (loopTimeLeft <= 0) {
        startNextLoop();
      }
    }, 1000);
  }

  function updateLoopHUD() {
    const el = container.querySelector('#loop-countdown');
    if (el) el.textContent = `${loopTimeLeft}s`;
    host.updateTime(loopTimeLeft);
  }

  function destroyTimers() {
    if (loopTimer) {
      clearInterval(loopTimer);
      loopTimer = null;
    }
  }

  return {
    id: 'timeLoop',
    name: 'Time Loop Escape',
    description: 'Solve cooperative puzzles by synchronizing actions with past temporal ghost echoes.',
    difficulty: 'Hard',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      if (animationId) cancelAnimationFrame(animationId);
      destroyTimers();

      level = 1;
      score = 0;
      loopCount = 1;
      isGameOver = false;

      pastGhosts = [];
      currentRecording = [];
      currentTick = 0;

      player = { x: 60, y: 350, vx: 0, vy: 0, speed: 3.2, radius: 12 };
      keys = { ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false, w: false, s: false, a: false, d: false };

      host.updateScore(score);
      host.updateLevel(level);

      renderUI();
      startLoopCountdown();

      animationId = requestAnimationFrame(gameLoop);
    },

    destroy() {
      isGameOver = true;
      if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = null;
      }
      destroyTimers();
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
      if (container) {
        container.innerHTML = '';
      }
    }
  };
})();
