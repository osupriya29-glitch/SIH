/**
 * Game 4: Bomb Defusal Logic
 * Multi-module fictional cyber puzzle device with wires, symbols, and frequency tuning.
 */

window.BombDefusal = (function () {
  let container = null;
  let host = null;
  let level = 1;
  let score = 0;
  let timeLeft = 50;
  let timerInterval = null;
  let strikes = 0;
  const maxStrikes = 3;

  // Module states
  let wiresSolved = false;
  let keypadSolved = false;
  let frequencySolved = false;

  // Current puzzle data
  let wiresData = [];
  let correctWireIndex = -1;
  let keypadSymbols = [];
  let keypadInput = [];
  let targetFreq = 400;
  let currentFreq = 350;

  function renderUI() {
    container.innerHTML = `
      <div class="game-container">
        <div class="game-instruction-banner">
          Disarm all 3 sub-modules before the core goes critical. Follow the manual rules carefully!
        </div>
        <div class="bomb-chassis">
          <div class="bomb-top-panel">
            <div class="bomb-serial">DEFUSAL UNIT #C7-${level}9</div>
            <div class="bomb-strikes" id="strikes-container">
              <div class="strike-box" id="strike-1">X</div>
              <div class="strike-box" id="strike-2">X</div>
              <div class="strike-box" id="strike-3">X</div>
            </div>
          </div>

          <div class="bomb-modules-grid">
            <!-- Module 1: Wires -->
            <div class="bomb-module" id="mod-wires">
              <div class="module-header">
                <span class="module-title">1. Laser Cut Wires</span>
                <span class="module-status-led" id="led-wires"></span>
              </div>
              <div class="wires-rack" id="wires-rack"></div>
              <div class="manual-hint" id="wires-rule-hint"></div>
            </div>

            <!-- Module 2: Keypad Symbols -->
            <div class="bomb-module" id="mod-keypad">
              <div class="module-header">
                <span class="module-title">2. Symbol Matrix</span>
                <span class="module-status-led" id="led-keypad"></span>
              </div>
              <div class="keypad-grid" id="keypad-grid"></div>
              <div class="manual-hint">Press symbols in ascending order</div>
            </div>

            <!-- Module 3: Frequency Stabilizer -->
            <div class="bomb-module" id="mod-frequency">
              <div class="module-header">
                <span class="module-title">3. Core Frequency</span>
                <span class="module-status-led" id="led-freq"></span>
              </div>
              <div class="frequency-tuner">
                <div class="freq-display" id="freq-val">000 MHz</div>
                <div class="freq-controls">
                  <button class="freq-btn" data-delta="-25">-25</button>
                  <button class="freq-btn" data-delta="-5">-5</button>
                  <button class="freq-btn" data-delta="5">+5</button>
                  <button class="freq-btn" data-delta="25">+25</button>
                </div>
                <button class="btn-ctrl btn-restart" id="btn-lock-freq" style="width: 100%; padding: 0.5rem; font-size: 0.8rem;">
                  LOCK HARMONIC
                </button>
              </div>
              <div class="manual-hint" id="freq-rule-hint">Target: 400 MHz</div>
            </div>
          </div>
        </div>
      </div>
    `;

    setupEventListeners();
  }

  function setupEventListeners() {
    // Frequency controls
    const freqBtns = container.querySelectorAll('.freq-btn');
    freqBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        if (frequencySolved) return;
        const delta = parseInt(btn.getAttribute('data-delta'), 10);
        currentFreq = Math.max(100, Math.min(999, currentFreq + delta));
        updateFreqDisplay();
        host.playSound('click');
      });
    });

    const lockBtn = container.querySelector('#btn-lock-freq');
    lockBtn.addEventListener('click', onLockFrequency);
  }

  function generateModules() {
    wiresSolved = false;
    keypadSolved = false;
    frequencySolved = false;

    // 1. Wires setup
    const possibleColors = [
      { name: 'red', hex: '#ff334b' },
      { name: 'blue', hex: '#00f0ff' },
      { name: 'yellow', hex: '#ffea00' },
      { name: 'white', hex: '#f0f4fc' }
    ];

    const wireCount = 4;
    wiresData = [];
    for (let i = 0; i < wireCount; i++) {
      wiresData.push(possibleColors[Math.floor(Math.random() * possibleColors.length)]);
    }

    const hasRed = wiresData.some(w => w.name === 'red');
    const hasYellow = wiresData.some(w => w.name === 'yellow');

    let ruleText = "";
    if (hasRed && !hasYellow) {
      correctWireIndex = 1; // 2nd wire (0-indexed 1)
      ruleText = "RULE: If RED exists & NO YELLOW, cut Wire #2. Otherwise cut Wire #4.";
    } else if (hasYellow) {
      correctWireIndex = 0; // 1st wire
      ruleText = "RULE: If YELLOW exists, cut Wire #1. Otherwise cut Wire #3.";
    } else {
      correctWireIndex = wireCount - 1; // Last wire
      ruleText = "RULE: Cut the LAST wire.";
    }

    renderWires(ruleText);

    // 2. Keypad symbols setup
    const allSymbols = [
      { sym: 'Ϙ', rank: 1 },
      { sym: 'Ѭ', rank: 2 },
      { sym: 'Ж', rank: 3 },
      { sym: 'Ͼ', rank: 4 },
      { sym: 'Ѱ', rank: 5 },
      { sym: 'Ϟ', rank: 6 }
    ];

    const shuffled = [...allSymbols].sort(() => Math.random() - 0.5);
    keypadSymbols = shuffled.slice(0, 4);
    keypadInput = [];
    renderKeypad();

    // 3. Frequency setup
    targetFreq = 300 + Math.floor(Math.random() * 40) * 10;
    currentFreq = targetFreq + (Math.random() > 0.5 ? 45 : -45);
    updateFreqDisplay();
    container.querySelector('#freq-rule-hint').textContent = `Target Resonance: ${targetFreq} MHz`;
  }

  function renderWires(ruleText) {
    const rack = container.querySelector('#wires-rack');
    const hint = container.querySelector('#wires-rule-hint');
    rack.innerHTML = '';
    hint.textContent = ruleText;

    wiresData.forEach((w, idx) => {
      const wireEl = document.createElement('div');
      wireEl.className = 'wire-item';
      wireEl.setAttribute('data-index', idx);
      wireEl.innerHTML = `<div class="wire-lead" style="background: ${w.hex};"></div>`;
      wireEl.addEventListener('click', () => onCutWire(idx, wireEl));
      rack.appendChild(wireEl);
    });
  }

  function onCutWire(index, element) {
    if (wiresSolved || element.classList.contains('cut')) return;
    element.classList.add('cut');
    host.playSound('cut');

    if (index === correctWireIndex) {
      wiresSolved = true;
      host.playSound('success');
      container.querySelector('#led-wires').classList.add('solved');
      score += 200;
      host.updateScore(score);
      checkAllSolved();
    } else {
      addStrike('Incorrect wire sliced!');
    }
  }

  function renderKeypad() {
    const grid = container.querySelector('#keypad-grid');
    grid.innerHTML = '';

    keypadSymbols.forEach(item => {
      const btn = document.createElement('button');
      btn.className = 'keypad-btn';
      btn.textContent = item.sym;
      btn.addEventListener('click', () => onKeypadPress(item, btn));
      grid.appendChild(btn);
    });
  }

  function onKeypadPress(item, buttonEl) {
    if (keypadSolved || buttonEl.classList.contains('pressed')) return;
    host.playSound('beep');

    // Expected next symbol has lowest rank among remaining
    const sorted = [...keypadSymbols].sort((a, b) => a.rank - b.rank);
    const expected = sorted[keypadInput.length];

    if (item.rank === expected.rank) {
      buttonEl.classList.add('pressed');
      keypadInput.push(item);

      if (keypadInput.length === keypadSymbols.length) {
        keypadSolved = true;
        host.playSound('success');
        container.querySelector('#led-keypad').classList.add('solved');
        score += 250;
        host.updateScore(score);
        checkAllSolved();
      }
    } else {
      addStrike('Wrong symbol sequence!');
      // Reset keypad
      keypadInput = [];
      const btns = container.querySelectorAll('.keypad-btn');
      btns.forEach(b => b.classList.remove('pressed'));
    }
  }

  function updateFreqDisplay() {
    const display = container.querySelector('#freq-val');
    if (display) {
      display.textContent = `${currentFreq} MHz`;
    }
  }

  function onLockFrequency() {
    if (frequencySolved) return;

    if (currentFreq === targetFreq) {
      frequencySolved = true;
      host.playSound('success');
      container.querySelector('#led-freq').classList.add('solved');
      score += 200;
      host.updateScore(score);
      checkAllSolved();
    } else {
      addStrike('Frequency off target!');
    }
  }

  function addStrike(reason) {
    strikes++;
    host.playSound('error');
    timeLeft = Math.max(1, timeLeft - 8);
    host.updateTime(timeLeft);

    const strikeEl = container.querySelector(`#strike-${strikes}`);
    if (strikeEl) strikeEl.classList.add('active');

    if (strikes >= maxStrikes) {
      detonate('Critical core overload! 3 strikes received.');
    }
  }

  function checkAllSolved() {
    if (wiresSolved && keypadSolved && frequencySolved) {
      stopTimer();
      host.playSound('win');
      score += 500 + timeLeft * 10;
      host.updateScore(score);

      setTimeout(() => {
        level++;
        host.updateLevel(level);
        strikes = 0;
        for (let i = 1; i <= 3; i++) {
          const s = container.querySelector(`#strike-${i}`);
          if (s) s.classList.remove('active');
        }
        container.querySelectorAll('.module-status-led').forEach(led => led.classList.remove('solved'));
        timeLeft = Math.max(25, 55 - level * 3);
        startTimer();
        generateModules();
      }, 1000);
    }
  }

  function detonate(msg) {
    stopTimer();
    host.playSound('explosion');
    host.endGame({
      win: false,
      score,
      title: 'CORE DETONATED',
      message: msg,
      details: `Devices Disarmed: ${level - 1}`
    });
  }

  function startTimer() {
    stopTimer();
    host.updateTime(timeLeft);

    timerInterval = setInterval(() => {
      timeLeft--;
      host.updateTime(timeLeft);

      if (timeLeft <= 10) {
        host.playSound('tick');
      }

      if (timeLeft <= 0) {
        detonate('Time expired! Detonation occurred.');
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
    id: 'bombDefusal',
    name: 'Bomb Defusal Logic',
    description: 'Solve wires, symbols, and frequencies before the core detonates.',
    difficulty: 'Hard',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="13" r="8"></circle><path d="M12 9v4l2 2"></path><path d="M14.5 3.5l2.5 2.5"></path><path d="M12 2v3"></path></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      stopTimer();
      level = 1;
      score = 0;
      strikes = 0;
      timeLeft = 50;

      host.updateScore(score);
      host.updateLevel(level);

      renderUI();
      generateModules();
      startTimer();
    },

    destroy() {
      stopTimer();
      if (container) {
        container.innerHTML = '';
      }
    }
  };
})();
