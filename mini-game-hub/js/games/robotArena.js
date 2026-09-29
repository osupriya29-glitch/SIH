/**
 * Game 9: Robot Programming Arena
 * Visual command-queue coding battle against an AI combat drone.
 */

window.RobotArena = (function () {
  let container = null;
  let host = null;
  let level = 1;
  let score = 0;
  let isExecuting = false;
  let isGameOver = false;
  let stepTimeout = null;

  const GRID_SIZE = 6;
  const MAX_COMMANDS = 6;
  let commandQueue = [];

  // Robots
  let playerRobot = {
    x: 0,
    y: 5,
    dir: 0, // 0: North, 1: East, 2: South, 3: West
    hp: 100,
    shield: false
  };

  let aiRobot = {
    x: 5,
    y: 0,
    dir: 2, // South
    hp: 100,
    shield: false
  };

  const OBSTACLES = [
    { x: 2, y: 2 },
    { x: 3, y: 3 },
    { x: 1, y: 4 },
    { x: 4, y: 1 }
  ];

  const DIRECTIONS = [
    { dx: 0, dy: -1, sym: '▲' }, // 0: North
    { dx: 1, dy: 0, sym: '▶' },  // 1: East
    { dx: 0, dy: 1, sym: '▼' },  // 2: South
    { dx: -1, dy: 0, sym: '◀' }  // 3: West
  ];

  function renderUI() {
    container.innerHTML = `
      <div class="game-container">
        <div class="game-instruction-banner">
          Program your robot's command routine. Outsmart and eliminate the enemy AI drone!
        </div>
        <div class="robot-arena-wrapper">
          <!-- Status Bar -->
          <div style="display: flex; justify-content: space-between; width: 100%; max-width: 440px; font-family: var(--font-mono); font-size: 0.9rem;">
            <div style="color: var(--neon-cyan);">🤖 Player HP: <span id="hp-player">100</span>%</div>
            <div style="color: var(--neon-red);">🛸 AI Drone HP: <span id="hp-ai">100</span>%</div>
          </div>

          <!-- Arena Board -->
          <div class="arena-board-grid" id="arena-grid"></div>

          <!-- Command Queue Deck -->
          <div class="command-deck">
            <div class="command-queue-display" id="cmd-queue-slots"></div>

            <div class="command-palette">
              <button class="btn-cmd" data-cmd="MOVE">MOVE</button>
              <button class="btn-cmd" data-cmd="TURN_LEFT">TURN ↺</button>
              <button class="btn-cmd" data-cmd="TURN_RIGHT">TURN ↻</button>
              <button class="btn-cmd" data-cmd="ATTACK">ATTACK ⚔</button>
              <button class="btn-cmd" data-cmd="DEFEND">DEFEND 🛡</button>
              <button class="btn-cmd" data-cmd="WAIT">WAIT ⏸</button>
            </div>

            <div class="program-action-row">
              <button class="btn-ctrl btn-restart" id="btn-run-program" style="padding: 0.6rem 2rem;">
                ▶ RUN PROGRAM
              </button>
              <button class="btn-ctrl btn-exit" id="btn-clear-program" style="padding: 0.6rem 1.2rem;">
                CLEAR
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    setupEvents();
    renderBoard();
    renderQueueSlots();
  }

  function setupEvents() {
    const palette = container.querySelectorAll('.btn-cmd');
    palette.forEach(btn => {
      btn.addEventListener('click', () => {
        if (isExecuting || isGameOver) return;
        if (commandQueue.length >= MAX_COMMANDS) {
          host.playSound('error');
          return;
        }
        const cmd = btn.getAttribute('data-cmd');
        commandQueue.push(cmd);
        host.playSound('click');
        renderQueueSlots();
      });
    });

    container.querySelector('#btn-run-program').addEventListener('click', () => {
      if (isExecuting || isGameOver) return;
      if (commandQueue.length === 0) {
        host.playSound('error');
        return;
      }
      runProgram();
    });

    container.querySelector('#btn-clear-program').addEventListener('click', () => {
      if (isExecuting || isGameOver) return;
      commandQueue = [];
      host.playSound('click');
      renderQueueSlots();
    });
  }

  function renderBoard() {
    const gridEl = container.querySelector('#arena-grid');
    if (!gridEl) return;
    gridEl.innerHTML = '';

    for (let y = 0; y < GRID_SIZE; y++) {
      for (let x = 0; x < GRID_SIZE; x++) {
        const cell = document.createElement('div');
        cell.className = 'arena-cell';

        const isObstacle = OBSTACLES.some(o => o.x === x && o.y === y);
        if (isObstacle) {
          cell.classList.add('obstacle');
          cell.textContent = '🧱';
        }

        if (playerRobot.x === x && playerRobot.y === y) {
          cell.style.background = 'rgba(0, 240, 255, 0.2)';
          cell.style.border = '2px solid var(--neon-cyan)';
          cell.innerHTML = `
            <div style="display:flex; flex-direction:column; align-items:center;">
              <span style="font-size: 0.75rem; color: var(--neon-cyan);">${DIRECTIONS[playerRobot.dir].sym}</span>
              <span>🤖</span>
            </div>
          `;
        } else if (aiRobot.x === x && aiRobot.y === y) {
          cell.style.background = 'rgba(255, 51, 75, 0.2)';
          cell.style.border = '2px solid var(--neon-red)';
          cell.innerHTML = `
            <div style="display:flex; flex-direction:column; align-items:center;">
              <span style="font-size: 0.75rem; color: var(--neon-red);">${DIRECTIONS[aiRobot.dir].sym}</span>
              <span>🛸</span>
            </div>
          `;
        }

        gridEl.appendChild(cell);
      }
    }

    container.querySelector('#hp-player').textContent = Math.max(0, playerRobot.hp);
    container.querySelector('#hp-ai').textContent = Math.max(0, aiRobot.hp);
  }

  function renderQueueSlots(activeStep = -1) {
    const slotsEl = container.querySelector('#cmd-queue-slots');
    if (!slotsEl) return;
    slotsEl.innerHTML = '';

    for (let i = 0; i < MAX_COMMANDS; i++) {
      const slot = document.createElement('div');
      slot.className = `cmd-slot ${i === activeStep ? 'active-executing' : ''}`;
      slot.textContent = commandQueue[i] || `${i + 1}`;
      slotsEl.appendChild(slot);
    }
  }

  function runProgram() {
    isExecuting = true;
    let step = 0;

    function executeStep() {
      if (step >= commandQueue.length || isGameOver) {
        isExecuting = false;
        commandQueue = [];
        renderQueueSlots();
        return;
      }

      renderQueueSlots(step);
      const playerCmd = commandQueue[step];
      const aiCmd = getAiDecision();

      // Reset turn defenses
      playerRobot.shield = false;
      aiRobot.shield = false;

      // 1. Process Defend actions first
      if (playerCmd === 'DEFEND') playerRobot.shield = true;
      if (aiCmd === 'DEFEND') aiRobot.shield = true;

      // 2. Process Player Action
      executeRobotAction(playerRobot, playerCmd, aiRobot, true);

      // 3. Process AI Action
      executeRobotAction(aiRobot, aiCmd, playerRobot, false);

      renderBoard();

      // Check win/loss
      if (aiRobot.hp <= 0) {
        triggerVictory();
        return;
      }
      if (playerRobot.hp <= 0) {
        triggerDefeat();
        return;
      }

      step++;
      stepTimeout = setTimeout(executeStep, 700);
    }

    executeStep();
  }

  function executeRobotAction(actor, cmd, target, isPlayer) {
    switch (cmd) {
      case 'MOVE': {
        const d = DIRECTIONS[actor.dir];
        const nx = actor.x + d.dx;
        const ny = actor.y + d.dy;

        const isWall = (nx < 0 || nx >= GRID_SIZE || ny < 0 || ny >= GRID_SIZE);
        const isBlock = OBSTACLES.some(o => o.x === nx && o.y === ny);
        const isOtherRobot = (target.x === nx && target.y === ny);

        if (!isWall && !isBlock && !isOtherRobot) {
          actor.x = nx;
          actor.y = ny;
          host.playSound('click');
        }
        break;
      }
      case 'TURN_LEFT':
        actor.dir = (actor.dir + 3) % 4;
        host.playSound('click');
        break;
      case 'TURN_RIGHT':
        actor.dir = (actor.dir + 1) % 4;
        host.playSound('click');
        break;
      case 'ATTACK': {
        host.playSound('cut');
        // Laser hits up to 3 tiles straight ahead
        const d = DIRECTIONS[actor.dir];
        for (let r = 1; r <= 3; r++) {
          const tx = actor.x + d.dx * r;
          const ty = actor.y + d.dy * r;
          if (OBSTACLES.some(o => o.x === tx && o.y === ty)) break; // Laser blocked by wall
          if (target.x === tx && target.y === ty) {
            // Hit!
            const dmg = target.shield ? 10 : 30;
            target.hp -= dmg;
            host.playSound('explosion');
            if (isPlayer) {
              score += 150;
              host.updateScore(score);
            }
            break;
          }
        }
        break;
      }
      case 'DEFEND':
        host.playSound('beep');
        break;
      case 'WAIT':
      default:
        break;
    }
  }

  function getAiDecision() {
    // Simple tactical AI
    const dx = playerRobot.x - aiRobot.x;
    const dy = playerRobot.y - aiRobot.y;

    // Check if player is directly in laser sights
    const d = DIRECTIONS[aiRobot.dir];
    const isAlinedX = (d.dx !== 0 && Math.sign(dx) === d.dx && dy === 0);
    const isAlinedY = (d.dy !== 0 && Math.sign(dy) === d.dy && dx === 0);

    if (isAlinedX || isAlinedY) {
      return Math.random() > 0.3 ? 'ATTACK' : 'DEFEND';
    }

    // Turn toward player
    if (Math.abs(dx) > Math.abs(dy)) {
      if (dx > 0 && aiRobot.dir !== 1) return 'TURN_RIGHT';
      if (dx < 0 && aiRobot.dir !== 3) return 'TURN_LEFT';
    } else {
      if (dy > 0 && aiRobot.dir !== 2) return 'TURN_RIGHT';
      if (dy < 0 && aiRobot.dir !== 0) return 'TURN_LEFT';
    }

    return Math.random() > 0.4 ? 'MOVE' : 'DEFEND';
  }

  function triggerVictory() {
    isGameOver = true;
    isExecuting = false;
    host.playSound('win');
    score += 500 + playerRobot.hp * 10;
    host.updateScore(score);

    host.endGame({
      win: true,
      score,
      title: 'ARENA CHAMPION!',
      message: 'Enemy combat drone decommissioned! Flawless tactical program execution.',
      details: `Remaining Health: ${playerRobot.hp}%`
    });
  }

  function triggerDefeat() {
    isGameOver = true;
    isExecuting = false;
    host.playSound('error');

    host.endGame({
      win: false,
      score,
      title: 'ROBOT DESTROYED',
      message: 'Your robot suffered critical structural damage in the arena.',
      details: `AI Drone Remaining HP: ${aiRobot.hp}%`
    });
  }

  return {
    id: 'robotArena',
    name: 'Robot Programming Arena',
    description: 'Assemble tactical code routines to battle an intelligent enemy combat drone.',
    difficulty: 'Medium',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      if (stepTimeout) clearTimeout(stepTimeout);
      level = 1;
      score = 0;
      isExecuting = false;
      isGameOver = false;
      commandQueue = [];

      playerRobot = { x: 0, y: 5, dir: 0, hp: 100, shield: false };
      aiRobot = { x: 5, y: 0, dir: 2, hp: 100, shield: false };

      host.updateScore(score);
      host.updateLevel(level);
      host.updateTime(0);

      renderUI();
    },

    destroy() {
      isGameOver = true;
      isExecuting = false;
      if (stepTimeout) {
        clearTimeout(stepTimeout);
        stepTimeout = null;
      }
      if (container) {
        container.innerHTML = '';
      }
    }
  };
})();
