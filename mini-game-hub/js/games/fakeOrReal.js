/**
 * Game 2: Fake or Real
 * Visual anomaly detection puzzle. Spot the subtly altered shape.
 */

window.FakeOrReal = (function () {
  let container = null;
  let host = null;
  let level = 1;
  let score = 0;
  let timeLeft = 25;
  let timerInterval = null;
  let anomalyIndex = -1;
  let isLevelTransitioning = false;

  function renderUI() {
    container.innerHTML = `
      <div class="game-container">
        <div class="game-instruction-banner">
          Detect the glitch: Find the one geometric shape that does not match the rest.
        </div>
        <div class="fake-real-container">
          <div class="shape-grid" id="shape-grid"></div>
        </div>
      </div>
    `;

    const grid = container.querySelector('#shape-grid');
    grid.addEventListener('click', onTileClick);
  }

  function generateLevelGrid() {
    const gridEl = container.querySelector('#shape-grid');
    if (!gridEl) return;

    // Grid size scales with level
    let gridSize = 3;
    if (level >= 8) gridSize = 5;
    else if (level >= 4) gridSize = 4;

    const totalTiles = gridSize * gridSize;
    gridEl.style.gridTemplateColumns = `repeat(${gridSize}, 1fr)`;
    gridEl.innerHTML = '';

    anomalyIndex = Math.floor(Math.random() * totalTiles);

    // Pick shape archetype and base colors
    const archetypes = ['notch-circle', 'star-poly', 'nested-diamond', 'target-ring'];
    const archetype = archetypes[(level - 1) % archetypes.length];

    const baseHue = (level * 67) % 360;
    const baseColor = `hsl(${baseHue}, 75%, 55%)`;

    // Progressive subtlety based on level
    // Rotation difference: 45deg down to 8deg
    const rotDiff = Math.max(7, Math.floor(45 - level * 3.5));
    // Color lightness diff: 25% down to 6%
    const lightDiff = Math.max(5, Math.floor(25 - level * 1.8));
    const anomalyColor = `hsl(${baseHue}, 75%, ${55 + (Math.random() > 0.5 ? lightDiff : -lightDiff)}%)`;

    for (let i = 0; i < totalTiles; i++) {
      const isAnomaly = (i === anomalyIndex);
      const tile = document.createElement('div');
      tile.className = 'shape-tile';
      tile.setAttribute('data-index', i);

      const color = isAnomaly ? anomalyColor : baseColor;
      const rot = isAnomaly ? rotDiff : 0;
      const innerDot = isAnomaly ? (level % 2 === 0 ? 0 : 1) : (level % 2 === 0 ? 1 : 0);

      tile.innerHTML = createShapeSvg(archetype, color, rot, innerDot);
      gridEl.appendChild(tile);
    }
  }

  function createShapeSvg(archetype, color, rotation, innerMod) {
    const rotTransform = rotation !== 0 ? `transform="rotate(${rotation} 25 25)"` : '';
    switch (archetype) {
      case 'notch-circle':
        return `
          <svg viewBox="0 0 50 50">
            <g ${rotTransform}>
              <circle cx="25" cy="25" r="18" fill="none" stroke="${color}" stroke-width="4" stroke-dasharray="28 8" />
              <circle cx="25" cy="25" r="${innerMod ? 5 : 7}" fill="${color}" />
            </g>
          </svg>
        `;
      case 'nested-diamond':
        return `
          <svg viewBox="0 0 50 50">
            <g ${rotTransform}>
              <rect x="12" y="12" width="26" height="26" transform="rotate(45 25 25)" fill="none" stroke="${color}" stroke-width="3" />
              <rect x="17" y="17" width="16" height="16" transform="rotate(45 25 25)" fill="${innerMod ? color : 'none'}" stroke="${color}" stroke-width="2" />
            </g>
          </svg>
        `;
      case 'star-poly':
        return `
          <svg viewBox="0 0 50 50">
            <g ${rotTransform}>
              <polygon points="25,5 31,19 46,19 34,28 38,43 25,33 12,43 16,28 4,19 19,19" fill="none" stroke="${color}" stroke-width="2.5" />
              <circle cx="25" cy="25" r="4" fill="${color}" />
            </g>
          </svg>
        `;
      case 'target-ring':
      default:
        return `
          <svg viewBox="0 0 50 50">
            <g ${rotTransform}>
              <circle cx="25" cy="25" r="19" fill="none" stroke="${color}" stroke-width="3" />
              <circle cx="25" cy="25" r="12" fill="none" stroke="${color}" stroke-width="2" stroke-dasharray="10 4" />
              <circle cx="25" cy="25" r="${innerMod ? 4 : 2}" fill="${color}" />
            </g>
          </svg>
        `;
    }
  }

  function onTileClick(e) {
    if (isLevelTransitioning) return;
    const tile = e.target.closest('.shape-tile');
    if (!tile) return;

    const clickedIndex = parseInt(tile.getAttribute('data-index'), 10);

    if (clickedIndex === anomalyIndex) {
      // Correct!
      isLevelTransitioning = true;
      tile.classList.add('correct-flash');
      host.playSound('success');

      const pointsEarned = 150 + level * 50;
      score += pointsEarned;
      host.updateScore(score);

      level++;
      host.updateLevel(level);

      // Reward time
      timeLeft = Math.min(45, timeLeft + 4);
      host.updateTime(timeLeft);

      setTimeout(() => {
        isLevelTransitioning = false;
        generateLevelGrid();
      }, 350);
    } else {
      // Wrong
      tile.classList.add('wrong-flash');
      host.playSound('error');
      timeLeft = Math.max(1, timeLeft - 4);
      host.updateTime(timeLeft);

      setTimeout(() => {
        tile.classList.remove('wrong-flash');
      }, 350);
    }
  }

  function startTimer() {
    stopTimer();
    timeLeft = 25;
    host.updateTime(timeLeft);

    timerInterval = setInterval(() => {
      timeLeft--;
      host.updateTime(timeLeft);

      if (timeLeft <= 0) {
        stopTimer();
        host.playSound('error');
        host.endGame({
          win: false,
          score,
          title: 'TIME EXPIRED',
          message: 'The optical anomaly scanner timed out.',
          details: `Anomalies Solved: ${level - 1}`
        });
      }
    }, 1000);
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  return {
    id: 'fakeOrReal',
    name: 'Fake or Real',
    description: 'Find the one subtle glitch in a grid of identical geometric patterns.',
    difficulty: 'Easy',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4"></path><path d="M12 16h.01"></path><circle cx="12" cy="12" r="6" stroke-dasharray="3 3"></circle></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      stopTimer();
      level = 1;
      score = 0;
      isLevelTransitioning = false;
      host.updateScore(score);
      host.updateLevel(level);

      renderUI();
      generateLevelGrid();
      startTimer();
    },

    destroy() {
      stopTimer();
      isLevelTransitioning = false;
      if (container) {
        container.innerHTML = '';
      }
    }
  };
})();
