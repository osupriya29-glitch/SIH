/**
 * Game 1: Memory Hacker
 * Cyberpunk sequence memorization game.
 */

window.MemoryHacker = (function () {
  let container = null;
  let host = null;
  let level = 1;
  let score = 0;
  let sequence = [];
  let playerInput = [];
  let isDisplaying = false;
  let isAcceptingInput = false;
  let timeouts = [];
  let timerInterval = null;
  let timeLeft = 30;

  const NODES = [
    { id: 0, label: 'ALPHA', glyph: 'α', color: '#00f0ff' },
    { id: 1, label: 'BETA', glyph: 'β', color: '#ff007f' },
    { id: 2, label: 'GAMMA', glyph: 'γ', color: '#00ff88' },
    { id: 3, label: 'DELTA', glyph: 'δ', color: '#ffaa00' },
    { id: 4, label: 'EPSILON', glyph: 'ε', color: '#9d4edd' },
    { id: 5, label: 'ZETA', glyph: 'ζ', color: '#38bdf8' }
  ];

  function clearAllTimeouts() {
    timeouts.forEach(t => clearTimeout(t));
    timeouts = [];
  }

  function renderUI() {
    container.innerHTML = `
      <div class="game-container">
        <div class="game-instruction-banner">
          Observe the memory sequence carefully, then replicate it in exact order.
        </div>
        <div class="memory-terminal">
          <div class="terminal-status-text" id="mem-status">INITIALIZING SYSTEM...</div>
          <div class="memory-node-grid" id="mem-grid">
            ${NODES.map(n => `
              <div class="memory-node disabled" data-id="${n.id}" style="--node-color: ${n.color};">
                <span class="node-glyph">${n.glyph}</span>
                <span class="node-label">${n.label}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;

    const grid = container.querySelector('#mem-grid');
    grid.addEventListener('click', onNodeClick);
  }

  function setStatus(text, color = 'var(--neon-cyan)') {
    const el = container ? container.querySelector('#mem-status') : null;
    if (el) {
      el.textContent = text;
      el.style.color = color;
    }
  }

  function flashNode(nodeId, duration = 350) {
    return new Promise(resolve => {
      const nodeEl = container.querySelector(`.memory-node[data-id="${nodeId}"]`);
      if (!nodeEl) {
        resolve();
        return;
      }

      nodeEl.classList.add('active-flash');
      host.playSound('beep');

      const t = setTimeout(() => {
        nodeEl.classList.remove('active-flash');
        const t2 = setTimeout(resolve, 150);
        timeouts.push(t2);
      }, duration);
      timeouts.push(t);
    });
  }

  async function playSequence() {
    isDisplaying = true;
    isAcceptingInput = false;
    setNodesClickable(false);
    setStatus(`DECRYPTING LEVEL ${level} SEQUENCE...`, 'var(--neon-cyan)');

    await new Promise(r => {
      const t = setTimeout(r, 600);
      timeouts.push(t);
    });

    const speed = Math.max(180, 420 - level * 25);
    for (let i = 0; i < sequence.length; i++) {
      if (!isDisplaying) return;
      await flashNode(sequence[i], speed);
    }

    if (!isDisplaying) return;
    isDisplaying = false;
    isAcceptingInput = true;
    playerInput = [];
    setNodesClickable(true);
    setStatus('REPRODUCE SEQUENCE NOW!', 'var(--neon-green)');
  }

  function setNodesClickable(clickable) {
    const nodes = container.querySelectorAll('.memory-node');
    nodes.forEach(n => {
      if (clickable) {
        n.classList.remove('disabled');
      } else {
        n.classList.add('disabled');
      }
    });
  }

  function onNodeClick(e) {
    if (!isAcceptingInput) return;
    const nodeEl = e.target.closest('.memory-node');
    if (!nodeEl) return;

    const nodeId = parseInt(nodeEl.getAttribute('data-id'), 10);
    host.playSound('click');

    // Quick visual feedback on click
    nodeEl.classList.add('active-flash');
    const t = setTimeout(() => nodeEl.classList.remove('active-flash'), 120);
    timeouts.push(t);

    playerInput.push(nodeId);
    const currentIndex = playerInput.length - 1;

    // Check correctness
    if (playerInput[currentIndex] !== sequence[currentIndex]) {
      handleGameOver(false);
      return;
    }

    // Completed round?
    if (playerInput.length === sequence.length) {
      handleLevelComplete();
    }
  }

  function handleLevelComplete() {
    isAcceptingInput = false;
    setNodesClickable(false);
    host.playSound('success');
    setStatus('ACCESS GRANTED! NEXT NODE OPENING...', 'var(--neon-green)');

    const earned = level * 100 + timeLeft * 10;
    score += earned;
    host.updateScore(score);

    level++;
    host.updateLevel(level);

    // Add bonus time
    timeLeft = Math.min(60, timeLeft + 10);
    host.updateTime(timeLeft);

    // Append next node
    sequence.push(Math.floor(Math.random() * NODES.length));

    const t = setTimeout(() => {
      playSequence();
    }, 1200);
    timeouts.push(t);
  }

  function handleGameOver(outOfTime = false) {
    destroyTimers();
    isAcceptingInput = false;
    setNodesClickable(false);
    host.playSound('error');

    setStatus(outOfTime ? 'TIME OUT! FIREWALL LOCKED.' : 'DECRYPTION FAILED! ACCESS DENIED.', 'var(--neon-red)');

    const t = setTimeout(() => {
      host.endGame({
        win: false,
        score,
        title: 'BREACH FAILED',
        message: outOfTime ? 'You ran out of time while hacking the node.' : `Corrupted sequence on Level ${level}.`,
        details: `Nodes Infiltrated: ${level - 1}`
      });
    }, 900);
    timeouts.push(t);
  }

  function startRoundTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timeLeft = 35;
    host.updateTime(timeLeft);

    timerInterval = setInterval(() => {
      timeLeft--;
      host.updateTime(timeLeft);
      if (timeLeft <= 0) {
        clearInterval(timerInterval);
        handleGameOver(true);
      }
    }, 1000);
  }

  function destroyTimers() {
    clearAllTimeouts();
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  return {
    id: 'memoryHacker',
    name: 'Memory Hacker',
    description: 'Memorize glowing cyber sequences to bypass mainframe firewalls.',
    difficulty: 'Easy',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><path d="M6 8h4"></path><path d="M6 12h8"></path><path d="M6 16h6"></path><circle cx="17" cy="12" r="2"></circle></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      destroyTimers();
      level = 1;
      score = 0;
      sequence = [];
      playerInput = [];
      isDisplaying = false;
      isAcceptingInput = false;

      host.updateScore(score);
      host.updateLevel(level);

      renderUI();
      startRoundTimer();

      // Seed first 3 nodes
      for (let i = 0; i < 3; i++) {
        sequence.push(Math.floor(Math.random() * NODES.length));
      }

      playSequence();
    },

    destroy() {
      destroyTimers();
      isDisplaying = false;
      isAcceptingInput = false;
      if (container) {
        container.innerHTML = '';
      }
    }
  };
})();
