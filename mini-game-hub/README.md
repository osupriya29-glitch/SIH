# 🎮 Mini Game Hub

A modern, fast, responsive indie game launcher featuring **10 unique, fully playable mini-games**. Built purely with **HTML5, CSS3, and Vanilla JavaScript**, with zero external frameworks or build tooling.

---

## 🚀 How to Run the Project

1. **Direct In-Browser**:
   - Navigate to the `mini-game-hub/` folder.
   - Double-click `index.html` (or right-click → **Open with** → Chrome, Edge, Firefox, or Safari).
   - The game hub is completely self-contained and offline-ready!

2. **Using a Local Development Server (Optional)**:
   - If using VS Code: install the **Live Server** extension, right-click `index.html` and select **Open with Live Server**.
   - Or with Python:
     ```bash
     cd mini-game-hub
     python -m http.server 8000
     ```
     Then open `http://localhost:8000` in your browser.

---

## 🕹️ Game Library

| # | Game | Genre | Description |
|---|------|-------|-------------|
| **1** | **Memory Hacker** | Pattern / Memory | Memorize glowing cyber terminal sequences to bypass mainframe security. |
| **2** | **Fake or Real** | Visual Anomaly | Spot subtle geometric anomalies and glitches across increasing grid sizes. |
| **3** | **Who Is Lying?** | Detective Deduction | Cross-examine suspect testimonies against verified forensic logs to catch the liar. |
| **4** | **Bomb Defusal Logic** | Multi-Module Puzzle | Slice colored laser wires, input cipher glyphs, and tune resonance frequencies against a ticking timer. |
| **5** | **Traffic Controller** | Traffic Simulation | Manage 4-way intersection traffic signals to prevent accidents and alleviate vehicle queues. |
| **6** | **Virus Evolution** | Survival & Upgrades | Absorb energy motes in a petri dish, evolve genetic upgrades (Speed, Shields, Clones, Magnet), and evade phages. |
| **7** | **Bank Heist Planner** | Abstract Strategy | Lead an elite crew through Infiltration, Vault Breaching, and Getaway stages while balancing Time, Cash, and Risk. |
| **8** | **Rescue the Island** | Crisis Management | Deploy rescue boats and construct sandbag barriers to evacuate stranded villagers before storm floods submerge the archipelago. |
| **9** | **Robot Programming Arena** | Visual Coding Battle | Queue tactical command sequences (`MOVE`, `TURN`, `ATTACK`, `DEFEND`) to defeat an AI combat drone. |
| **10** | **Time Loop Escape** | Temporal Paradox Co-op | Step on pressure plates to hold laser doors open for your past recorded ghost clones across a 20-second time loop. |

---

## 📂 Project Architecture

```text
mini-game-hub/
├── index.html               # Main application entry point & view container system
├── README.md                # Project documentation and guide
├── css/
│   ├── style.css            # Dark gaming theme, hub layout, HUD, cards, and modal styles
│   └── games.css            # Game-specific styles (terminals, canvases, decks, matrices)
├── js/
│   ├── app.js               # Central controller: view routing, mounting, unified HUD, game lifecycle
│   ├── storage.js           # LocalStorage manager: persistent high scores & global play metrics
│   ├── utils.js             # Web Audio synthesizer sound effects, game timer, formatting helpers
│   └── games/
│       ├── memoryHacker.js      # Game 1
│       ├── fakeOrReal.js        # Game 2
│       ├── whoIsLying.js        # Game 3
│       ├── bombDefusal.js       # Game 4
│       ├── trafficController.js # Game 5
│       ├── virusEvolution.js    # Game 6
│       ├── bankHeist.js         # Game 7
│       ├── rescueIsland.js      # Game 8
│       ├── robotArena.js        # Game 9
│       └── timeLoop.js          # Game 10
└── assets/                  # Icons and media (all SVG graphics and sounds are synthesized natively)
```

---

## ➕ How to Add an 11th Game

Every game in the hub follows a clean, decoupled module pattern. To add a new game:

### 1. Create the Game Script
Create a new file in `js/games/myNewGame.js`:

```javascript
window.MyNewGame = (function () {
  let container = null;
  let host = null;
  let score = 0;
  let level = 1;

  return {
    id: 'myNewGame',
    name: 'My New Game',
    description: 'A brief description of your awesome new challenge.',
    difficulty: 'Medium', // 'Easy' | 'Medium' | 'Hard'
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      score = 0;
      level = 1;
      host.updateScore(score);
      host.updateLevel(level);
      host.updateTime(30);

      // Render your game HTML into container
      container.innerHTML = `
        <div class="game-container">
          <button id="btn-click-me" class="btn-primary-launch">CLICK ME</button>
        </div>
      `;

      container.querySelector('#btn-click-me').addEventListener('click', () => {
        score += 100;
        host.updateScore(score);
        host.playSound('success');

        if (score >= 500) {
          host.endGame({
            win: true,
            score,
            title: 'VICTORY!',
            message: 'You scored 500 points!'
          });
        }
      });
    },

    destroy() {
      // ALWAYS stop any intervals, animation loops, or global event listeners here!
      if (container) {
        container.innerHTML = '';
      }
    }
  };
})();
```

### 2. Register in `index.html`
Add the script tag before `js/app.js`:

```html
<script src="js/games/myNewGame.js"></script>
<script src="js/app.js"></script>
```

### 3. Register in `js/app.js`
Add `window.MyNewGame` to the `GAMES` array inside `js/app.js`:

```javascript
const GAMES = [
  window.MemoryHacker,
  // ... existing games ...
  window.TimeLoop,
  window.MyNewGame // <-- Added here
];
```

The new game card will automatically appear in the library with real-time high-score tracking!

---

## 🔊 Sound Effects System
The sound effects use the browser's native **Web Audio API** via `SoundFX` in `js/utils.js`. No audio files or network bandwidth are required. Sound can be muted or unmuted at any time using the speaker button in the top navigation header.
