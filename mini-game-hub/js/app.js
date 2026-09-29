/**
 * Main Application Controller for Mini Game Hub
 * Handles page navigation, game mounting/unmounting, HUD updates, and modal dialogues.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Registry of all 10 games
  const GAMES = [
    window.MemoryHacker,
    window.FakeOrReal,
    window.WhoIsLying,
    window.BombDefusal,
    window.TrafficController,
    window.VirusEvolution,
    window.BankHeist,
    window.RescueIsland,
    window.RobotArena,
    window.TimeLoop
  ];

  // DOM Elements
  const views = {
    home: document.getElementById('view-home'),
    hub: document.getElementById('view-hub'),
    game: document.getElementById('view-game')
  };

  const hud = {
    title: document.getElementById('hud-game-title'),
    score: document.getElementById('hud-score'),
    best: document.getElementById('hud-best'),
    level: document.getElementById('hud-level'),
    time: document.getElementById('hud-time')
  };

  const gameArea = document.getElementById('game-area');
  const modalOverlay = document.getElementById('modal-overlay');

  // Currently running game
  let activeGame = null;
  let activeGameId = null;
  let currentScore = 0;

  // Unified Host API provided to each game module
  const hostApi = {
    updateScore(val) {
      currentScore = Math.floor(val);
      hud.score.textContent = Utils.formatScore(currentScore, 4);

      // Check if current score beats high score live
      const best = Storage.loadHighScore(activeGameId);
      if (currentScore > best) {
        hud.best.textContent = Utils.formatScore(currentScore, 4);
      }
    },

    updateLevel(val) {
      hud.level.textContent = val;
    },

    updateTime(val) {
      hud.time.textContent = Utils.formatTime(val);
      if (val > 0 && val <= 10) {
        hud.time.classList.add('time-alert');
      } else {
        hud.time.classList.remove('time-alert');
      }
    },

    getHighScore() {
      return Storage.loadHighScore(activeGameId);
    },

    playSound(soundType) {
      SoundFX.play(soundType);
    },

    endGame({ win, score, title, message, details = '' }) {
      const finalScore = Math.floor(score);
      const isNewRecord = Storage.saveHighScore(activeGameId, finalScore);
      
      if (win) {
        Storage.recordGameCompletion(activeGameId);
      }

      showGameOverModal({
        win,
        title,
        message,
        details,
        score: finalScore,
        isNewRecord,
        best: Storage.loadHighScore(activeGameId)
      });
    }
  };

  /* ==========================================================================
     VIEW NAVIGATION
     ========================================================================== */
  function switchView(viewName) {
    // Hide all views
    Object.values(views).forEach(v => v.classList.remove('active'));

    // Show target view
    if (views[viewName]) {
      views[viewName].classList.add('active');
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Update screen-specific content
    if (viewName === 'home') {
      updateHomeStats();
    } else if (viewName === 'hub') {
      renderGameCards();
    }
  }

  function showHome() {
    exitCurrentGame();
    switchView('home');
  }

  function showHub() {
    exitCurrentGame();
    switchView('hub');
  }

  /* ==========================================================================
     GAME LIFECYCLE MANAGEMENT
     ========================================================================== */
  function launchGame(gameId) {
    // Clean up any existing game first
    exitCurrentGame();

    const game = GAMES.find(g => g && g.id === gameId);
    if (!game) {
      console.error(`Game not found: ${gameId}`);
      return;
    }

    activeGame = game;
    activeGameId = gameId;
    currentScore = 0;

    // Track play count
    Storage.recordGamePlay(gameId);

    // Setup HUD
    hud.title.textContent = game.name;
    hud.score.textContent = "0000";
    hud.best.textContent = Utils.formatScore(Storage.loadHighScore(gameId), 4);
    hud.level.textContent = "1";
    hud.time.textContent = "00:00";
    hud.time.classList.remove('time-alert');

    // Switch view
    switchView('game');

    // Clear game area and initialize
    gameArea.innerHTML = '';
    SoundFX.play('click');
    activeGame.init(gameArea, hostApi);
  }

  function restartCurrentGame() {
    if (!activeGame) return;
    closeModal();
    SoundFX.play('click');
    currentScore = 0;
    hud.score.textContent = "0000";
    hud.level.textContent = "1";
    hud.time.classList.remove('time-alert');
    activeGame.restart();
  }

  function exitCurrentGame() {
    closeModal();
    if (activeGame) {
      try {
        activeGame.destroy();
      } catch (err) {
        console.warn('Error during game destruction:', err);
      }
      activeGame = null;
      activeGameId = null;
    }
    gameArea.innerHTML = '';
  }

  /* ==========================================================================
     HOME & HUB RENDERING
     ========================================================================== */
  function updateHomeStats() {
    const stats = Storage.getGlobalStats();
    const statPlays = document.getElementById('stat-total-plays');
    const statCompleted = document.getElementById('stat-completed');
    const statHighest = document.getElementById('stat-highest-score');

    if (statPlays) statPlays.textContent = stats.totalPlays || 0;
    if (statCompleted) statCompleted.textContent = stats.totalCompleted || 0;
    if (statHighest) statHighest.textContent = Utils.formatScore(stats.highestScore || 0, 4);
  }

  function renderGameCards() {
    const grid = document.getElementById('games-grid');
    if (!grid) return;

    grid.innerHTML = '';

    GAMES.forEach(game => {
      if (!game) return;
      const highScore = Storage.loadHighScore(game.id);

      let diffClass = 'diff-easy';
      if (game.difficulty === 'Medium') diffClass = 'diff-medium';
      if (game.difficulty === 'Hard') diffClass = 'diff-hard';

      const card = document.createElement('div');
      card.className = 'game-card';
      card.innerHTML = `
        <div class="card-top">
          <div class="card-icon-box">
            ${game.icon || '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle></svg>'}
          </div>
          <span class="badge-difficulty ${diffClass}">${game.difficulty}</span>
        </div>
        <div class="card-content">
          <h3 class="card-title">${game.name}</h3>
          <p class="card-desc">${game.description}</p>
        </div>
        <div class="card-footer">
          <div class="card-highscore">
            <span class="score-caption">High Score</span>
            <span class="score-digits">${Utils.formatScore(highScore, 4)}</span>
          </div>
          <button class="btn-play" data-game-id="${game.id}">PLAY</button>
        </div>
      `;

      card.querySelector('.btn-play').addEventListener('click', (e) => {
        e.stopPropagation();
        launchGame(game.id);
      });

      card.addEventListener('click', () => {
        launchGame(game.id);
      });

      grid.appendChild(card);
    });
  }

  /* ==========================================================================
     MODALS (GAME OVER & VICTORY)
     ========================================================================== */
  function showGameOverModal({ win, title, message, details, score, isNewRecord, best }) {
    const modalContent = document.getElementById('modal-content');
    if (!modalContent) return;

    modalContent.innerHTML = `
      <div class="modal-icon-badge ${win ? 'win' : 'lose'}">
        ${win ? '🏆' : '💀'}
      </div>
      <h2 class="modal-title" style="color: ${win ? 'var(--neon-green)' : 'var(--neon-red)'};">
        ${title}
      </h2>
      <p class="modal-msg">${message}</p>
      ${details ? `<p style="font-size: 0.85rem; color: var(--text-dim); margin-top: -0.8rem; margin-bottom: 1.25rem;">${details}</p>` : ''}

      <div class="modal-stats">
        <div class="modal-stat-box">
          <span class="modal-stat-label">Final Score</span>
          <span class="modal-stat-val">${Utils.formatScore(score, 4)}</span>
          ${isNewRecord ? '<span class="new-record-tag">NEW RECORD!</span>' : ''}
        </div>
        <div class="modal-stat-box">
          <span class="modal-stat-label">All-Time Best</span>
          <span class="modal-stat-val">${Utils.formatScore(best, 4)}</span>
        </div>
      </div>

      <div class="modal-actions">
        <button class="modal-btn modal-btn-secondary" id="modal-btn-hub">EXIT TO HUB</button>
        <button class="modal-btn modal-btn-primary" id="modal-btn-retry">PLAY AGAIN</button>
      </div>
    `;

    modalOverlay.classList.add('active');

    document.getElementById('modal-btn-retry').addEventListener('click', () => {
      closeModal();
      restartCurrentGame();
    });

    document.getElementById('modal-btn-hub').addEventListener('click', () => {
      closeModal();
      showHub();
    });
  }

  function closeModal() {
    if (modalOverlay) {
      modalOverlay.classList.remove('active');
    }
  }

  /* ==========================================================================
     GLOBAL EVENT LISTENERS
     ========================================================================== */
  // Logo returns home
  document.getElementById('brand-link').addEventListener('click', showHome);

  // Home "Explore Games" button
  document.getElementById('btn-explore').addEventListener('click', showHub);

  // Back button on Game screen
  document.getElementById('btn-game-back').addEventListener('click', showHub);

  // Game bottom bar: Restart & Exit
  document.getElementById('btn-restart-game').addEventListener('click', restartCurrentGame);
  document.getElementById('btn-exit-game').addEventListener('click', showHub);

  // Sound toggle button
  const soundBtn = document.getElementById('btn-toggle-sound');
  soundBtn.addEventListener('click', () => {
    const isMuted = SoundFX.toggleMute();
    soundBtn.innerHTML = isMuted
      ? `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 5L6 9H2v6h4l5 4V5z"></path><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>`
      : `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>`;
  });

  // Start on Home view
  showHome();
});
