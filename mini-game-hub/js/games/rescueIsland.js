/**
 * Game 8: Rescue the Island
 * Island disaster evacuation and flood barrier simulation.
 */

window.RescueIsland = (function () {
  let container = null;
  let host = null;
  let level = 1;
  let score = 0;
  let isGameOver = false;
  let floodTimer = null;

  const GRID_SIZE = 6;
  let grid = [];

  // Resources
  let resources = {
    boats: 3,
    fuel: 12,
    sandbags: 8,
    civiliansSaved: 0,
    civiliansTotal: 18
  };

  // Selected action tool: 'evacuate' | 'barrier'
  let activeTool = 'evacuate';

  function renderUI() {
    container.innerHTML = `
      <div class="game-container">
        <div class="game-instruction-banner">
          Rising storm waters are submerging the archipelago! Place sandbags and evacuate citizens to the Highland Shelter.
        </div>
        <div class="island-rescue-board">
          <div class="island-resources-bar">
            <div class="res-item">🚤 Boats: <span id="res-boats">${resources.boats}</span></div>
            <div class="res-item">⛽ Fuel: <span id="res-fuel">${resources.fuel}</span></div>
            <div class="res-item">🧱 Sandbags: <span id="res-sandbags">${resources.sandbags}</span></div>
            <div class="res-item">👥 Rescued: <span id="res-saved">${resources.civiliansSaved}/${resources.civiliansTotal}</span></div>
          </div>

          <div class="island-grid" id="island-grid"></div>

          <div class="island-actions-bar">
            <button class="btn-island-action ${activeTool === 'evacuate' ? 'active' : ''}" id="tool-evacuate">
              🚤 Evacuate Civilians (Cost: 1 Fuel)
            </button>
            <button class="btn-island-action ${activeTool === 'barrier' ? 'active' : ''}" id="tool-barrier">
              🧱 Build Sandbag Wall (Cost: 1 Bag)
            </button>
          </div>
        </div>
      </div>
    `;

    setupGridEvents();
  }

  function setupGridEvents() {
    const btnEvac = container.querySelector('#tool-evacuate');
    const btnBarr = container.querySelector('#tool-barrier');

    btnEvac.addEventListener('click', () => {
      activeTool = 'evacuate';
      btnEvac.classList.add('active');
      btnBarr.classList.remove('active');
      host.playSound('click');
    });

    btnBarr.addEventListener('click', () => {
      activeTool = 'barrier';
      btnBarr.classList.add('active');
      btnEvac.classList.remove('active');
      host.playSound('click');
    });
  }

  function initIslandMap() {
    grid = [];
    resources = {
      boats: 3,
      fuel: 14,
      sandbags: 7,
      civiliansSaved: 0,
      civiliansTotal: 16
    };

    let civiliansPlaced = 0;

    for (let r = 0; r < GRID_SIZE; r++) {
      grid[r] = [];
      for (let c = 0; c < GRID_SIZE; c++) {
        // Highland shelter in center-ish
        const isShelter = (r === 2 && c === 3);
        const isBorder = (r === 0 || r === GRID_SIZE - 1 || c === 0 || c === GRID_SIZE - 1);

        let type = 'plain';
        if (isShelter) type = 'shelter';
        else if (isBorder && (r === 0 || c === 0)) type = 'deep-water';
        else if (isBorder) type = 'coast';
        else if ((r === 1 && c === 2) || (r === 3 && c === 1) || (r === 4 && c === 3)) type = 'village';

        let civs = 0;
        if (type === 'village' && civiliansPlaced < resources.civiliansTotal) {
          civs = 4;
          civiliansPlaced += civs;
        } else if (type === 'coast' && civiliansPlaced < resources.civiliansTotal) {
          civs = 2;
          civiliansPlaced += civs;
        }

        grid[r][c] = {
          row: r,
          col: c,
          type,
          civilians: civs,
          hasSandbag: false,
          isFlooded: (type === 'deep-water')
        };
      }
    }

    renderGridTiles();
    updateHUD();
  }

  function renderGridTiles() {
    const gridEl = container.querySelector('#island-grid');
    if (!gridEl) return;
    gridEl.innerHTML = '';

    for (let r = 0; r < GRID_SIZE; r++) {
      for (let c = 0; c < GRID_SIZE; c++) {
        const cell = grid[r][c];
        const tileEl = document.createElement('div');
        tileEl.className = `island-tile tile-${cell.type} ${cell.isFlooded ? 'tile-flooded' : ''}`;
        tileEl.setAttribute('data-r', r);
        tileEl.setAttribute('data-c', c);

        let icon = '';
        if (cell.type === 'shelter') icon = '⛺';
        else if (cell.isFlooded) icon = '🌊';
        else if (cell.type === 'village') icon = '🏡';
        else if (cell.type === 'coast') icon = '🏖️';
        else if (cell.type === 'plain') icon = '🌲';

        tileEl.innerHTML = `
          <span>${icon}</span>
          ${cell.civilians > 0 ? `<div class="tile-civilians">👥 ${cell.civilians}</div>` : ''}
          ${cell.hasSandbag ? `<div class="tile-sandbag">🧱</div>` : ''}
        `;

        tileEl.addEventListener('click', () => onTileClick(r, c));
        gridEl.appendChild(tileEl);
      }
    }
  }

  function onTileClick(r, c) {
    if (isGameOver) return;
    const cell = grid[r][c];

    if (activeTool === 'evacuate') {
      if (cell.civilians <= 0) return;
      if (resources.fuel <= 0) {
        host.playSound('error');
        return;
      }

      // Evacuate 2 civilians per boat trip
      const savedCount = Math.min(2, cell.civilians);
      cell.civilians -= savedCount;
      resources.civiliansSaved += savedCount;
      resources.fuel--;
      score += savedCount * 100;
      host.playSound('success');

      updateHUD();
      renderGridTiles();

      // Win condition: rescued target quota (12+)
      if (resources.civiliansSaved >= 12) {
        triggerVictory();
      }
    } else if (activeTool === 'barrier') {
      if (cell.isFlooded || cell.hasSandbag) return;
      if (resources.sandbags <= 0) {
        host.playSound('error');
        return;
      }

      cell.hasSandbag = true;
      resources.sandbags--;
      host.playSound('click');
      updateHUD();
      renderGridTiles();
    }
  }

  function advanceFlood() {
    if (isGameOver) return;

    // Find tiles adjacent to flooded tiles
    const newlyFlooded = [];

    for (let r = 0; r < GRID_SIZE; r++) {
      for (let c = 0; c < GRID_SIZE; c++) {
        const cell = grid[r][c];
        if (cell.isFlooded || cell.type === 'shelter') continue;

        // Check if any neighbor is flooded
        const neighbors = [
          [r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]
        ];

        const hasWaterNeighbor = neighbors.some(([nr, nc]) => {
          return nr >= 0 && nr < GRID_SIZE && nc >= 0 && nc < GRID_SIZE && grid[nr][nc].isFlooded;
        });

        if (hasWaterNeighbor) {
          if (cell.hasSandbag) {
            // Sandbag degrades before water breaches
            cell.hasSandbag = false;
          } else {
            newlyFlooded.push(cell);
          }
        }
      }
    }

    // Flood the breached tiles
    let lostCivilians = 0;
    newlyFlooded.forEach(cell => {
      cell.isFlooded = true;
      if (cell.civilians > 0) {
        lostCivilians += cell.civilians;
        cell.civilians = 0;
      }
    });

    if (newlyFlooded.length > 0) {
      renderGridTiles();
    }

    // Check if shelter is surrounded or too many civilians drowned
    const totalRemaining = grid.flat().reduce((sum, cl) => sum + cl.civilians, 0);
    if (resources.civiliansSaved + totalRemaining < 12) {
      triggerDefeat("Too many civilians were trapped by rising flood tides.");
    }
  }

  function updateHUD() {
    if (!container) return;
    container.querySelector('#res-boats').textContent = resources.boats;
    container.querySelector('#res-fuel').textContent = resources.fuel;
    container.querySelector('#res-sandbags').textContent = resources.sandbags;
    container.querySelector('#res-saved').textContent = `${resources.civiliansSaved}/${resources.civiliansTotal}`;

    host.updateScore(score);
    host.updateLevel(level);
  }

  function triggerVictory() {
    isGameOver = true;
    clearInterval(floodTimer);
    host.playSound('win');
    score += resources.fuel * 50 + resources.sandbags * 40;
    host.updateScore(score);

    host.endGame({
      win: true,
      score,
      title: 'ISLAND EVACUATED!',
      message: `Heroic rescue! You successfully evacuated ${resources.civiliansSaved} citizens to high ground.`,
      details: `Fuel Remaining: ${resources.fuel} | Sandbags Saved: ${resources.sandbags}`
    });
  }

  function triggerDefeat(reason) {
    isGameOver = true;
    clearInterval(floodTimer);
    host.playSound('error');

    host.endGame({
      win: false,
      score,
      title: 'ISLAND SUBMERGED',
      message: reason,
      details: `Total Rescued: ${resources.civiliansSaved}/${resources.civiliansTotal}`
    });
  }

  function startFloodTimer() {
    if (floodTimer) clearInterval(floodTimer);
    floodTimer = setInterval(() => {
      advanceFlood();
    }, 4500);
  }

  return {
    id: 'rescueIsland',
    name: 'Rescue the Island',
    description: 'Construct levees and deploy rescue boats as tides submerge the archipelago.',
    difficulty: 'Hard',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 18h20"></path><path d="M6 14l3-6 4 6"></path><path d="M15 14l2-3 2 3"></path><path d="M12 3v5"></path></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      if (floodTimer) clearInterval(floodTimer);
      level = 1;
      score = 0;
      isGameOver = false;
      activeTool = 'evacuate';

      host.updateScore(score);
      host.updateLevel(level);
      host.updateTime(0);

      renderUI();
      initIslandMap();
      startFloodTimer();
    },

    destroy() {
      isGameOver = true;
      if (floodTimer) {
        clearInterval(floodTimer);
        floodTimer = null;
      }
      if (container) {
        container.innerHTML = '';
      }
    }
  };
})();
