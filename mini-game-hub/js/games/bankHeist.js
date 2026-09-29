/**
 * Game 7: Bank Heist Planner
 * Abstract strategic resource management simulation.
 */

window.BankHeist = (function () {
  let container = null;
  let host = null;
  let level = 1; // Stage 1: Infiltration, Stage 2: Vault, Stage 3: Extraction
  let score = 0;
  let isGameOver = false;

  // Strategic gauges
  let stats = {
    time: 100,      // %
    cash: 50,       // $k
    morale: 100,    // %
    stealth: 100,   // %
    alert: 0        // %
  };

  let currentTurn = 0;
  const turnsPerStage = 3;

  // Procedural situation decks for each stage
  const STAGES = [
    {
      name: "STAGE 1: FACILITY INFILTRATION",
      badge: "Infiltration",
      situations: [
        {
          prompt: "The perimeter is guarded by thermal cameras and two roaming guard drones.",
          choices: [
            {
              title: "Deploy Electronic EMP Jammer",
              cost: "Cash -$15k | Time -15%",
              effect: { cash: -15, time: -15, stealth: 10, alert: -10, morale: 0 },
              log: "Jammer blinded sensors without triggering sirens."
            },
            {
              title: "Splice Fiber-Optic Camera Feed",
              cost: "Time -25% | Morale -10%",
              effect: { cash: 0, time: -25, stealth: 15, alert: -5, morale: -10 },
              log: "Hacker successfully looped the camera footage."
            },
            {
              title: "Sprint through Blind Spot",
              cost: "Risk Alert +25% | Time -10%",
              effect: { cash: 0, time: -10, stealth: -25, alert: 25, morale: 5 },
              log: "Close call! A drone almost spotted your footsteps."
            }
          ]
        },
        {
          prompt: "A reinforced magnetic bulkhead seals access to the central elevator.",
          choices: [
            {
              title: "Overload Power Generator",
              cost: "Time -15% | Risk Alert +15%",
              effect: { cash: 0, time: -15, stealth: -10, alert: 15, morale: 0 },
              log: "Power dipped, releasing the magnetic locks."
            },
            {
              title: "Bribe Maintenance Contractor",
              cost: "Cash -$20k | Time -10%",
              effect: { cash: -20, time: -10, stealth: 15, alert: -10, morale: 10 },
              log: "Contractor provided emergency bypass keycards."
            },
            {
              title: "Crack Biometric Keypad Manual",
              cost: "Time -30% | Morale -15%",
              effect: { cash: 0, time: -30, stealth: 10, alert: 0, morale: -15 },
              log: "Lengthy decryption, but bypassed with zero trace."
            }
          ]
        },
        {
          prompt: "An unexpected guard shift patrol crosses into the lobby checkpoint.",
          choices: [
            {
              title: "Deploy Acoustic Decoy Grenade",
              cost: "Cash -$10k | Time -10%",
              effect: { cash: -10, time: -10, stealth: 5, alert: 5, morale: 0 },
              log: "Guards diverted toward false alarm in West wing."
            },
            {
              title: "Conceal in Ventilation Ducts",
              cost: "Time -20% | Morale -10%",
              effect: { cash: 0, time: -20, stealth: 10, alert: -5, morale: -10 },
              log: "Cramped crawl, but the patrol walked right past."
            },
            {
              title: "Neutralize with Tranq Darts",
              cost: "Cash -$15k | Risk Alert +15%",
              effect: { cash: -15, time: -10, stealth: -10, alert: 15, morale: 5 },
              log: "Guards knocked unconscious and hidden in closets."
            }
          ]
        }
      ]
    },
    {
      name: "STAGE 2: VAULT PENETRATION",
      badge: "Deep Vault",
      situations: [
        {
          prompt: "You reach the primary titanium vault door, shielded by harmonic lasers.",
          choices: [
            {
              title: "Deploy Laser-Reflective Prisms",
              cost: "Cash -$20k | Time -15%",
              effect: { cash: -20, time: -15, stealth: 10, alert: -10, morale: 5 },
              log: "Prisms redirected the laser matrix safely."
            },
            {
              title: "Cut Power Grid to Floor",
              cost: "Time -20% | Risk Alert +20%",
              effect: { cash: 0, time: -20, stealth: -20, alert: 20, morale: 0 },
              log: "Emergency backup batteries kicked in, alarm tick raised!"
            },
            {
              title: "Gymnast Laser Acrobatics",
              cost: "Time -15% | Morale -20%",
              effect: { cash: 0, time: -15, stealth: 0, alert: 10, morale: -20 },
              log: "Acrobat grazed a sensor, but reached the cutoff switch."
            }
          ]
        },
        {
          prompt: "The main vault lock is a 12-tumbler digital cryogenic safe.",
          choices: [
            {
              title: "Apply Liquid Nitrogen Cryo-Drill",
              cost: "Cash -$25k | Time -15%",
              effect: { cash: -25, time: -15, stealth: 10, alert: 0, morale: 5 },
              log: "Cryo-drill shattered the tumblers cleanly."
            },
            {
              title: "Shape-Charge Micro-Explosive",
              cost: "Risk Alert +30% | Time -10%",
              effect: { cash: 0, time: -10, stealth: -35, alert: 30, morale: 10 },
              log: "BOOM! Loud blast breached the door instantly."
            },
            {
              title: "Manual Stethoscope & Acoustic Dialing",
              cost: "Time -35% | Morale -15%",
              effect: { cash: 0, time: -35, stealth: 20, alert: -10, morale: -15 },
              log: "Silent click... the vault swing opened quietly."
            }
          ]
        },
        {
          prompt: "Inside the vault: millions in bearer bonds and gold bullion!",
          choices: [
            {
              title: "Pack Everything (Maximum Greed)",
              cost: "Time -25% | Morale -15%",
              effect: { cash: 150, time: -25, stealth: -15, alert: 15, morale: -15 },
              log: "Heavy bags packed to the brim! Loot secured: +$150k."
            },
            {
              title: "Grab Diamonds & High-Value Bonds",
              cost: "Time -15% | Morale +10%",
              effect: { cash: 90, time: -15, stealth: 5, alert: 0, morale: 10 },
              log: "Lightweight, high-density loot secured: +$90k."
            },
            {
              title: "Grab Quick Platinum Drives Only",
              cost: "Time -10% | Stealth +15%",
              effect: { cash: 50, time: -10, stealth: 15, alert: -10, morale: 5 },
              log: "Swift grab-and-go: +$50k."
            }
          ]
        }
      ]
    },
    {
      name: "STAGE 3: GETAWAY & EXTRACTION",
      badge: "Extraction",
      situations: [
        {
          prompt: "Sirens wail outside. Roadblocks are forming around the financial district.",
          choices: [
            {
              title: "Hack City Traffic Signal Network",
              cost: "Cash -$15k | Time -15%",
              effect: { cash: -15, time: -15, stealth: 10, alert: -15, morale: 10 },
              log: "Traffic gridlock trapped police interceptors."
            },
            {
              title: "Disguised Armored Security Van",
              cost: "Cash -$25k | Time -10%",
              effect: { cash: -25, time: -10, stealth: 20, alert: -20, morale: 5 },
              log: "Passed police checkpoint under fake credentials."
            },
            {
              title: "High-Speed Muscle Car Ramming",
              cost: "Risk Alert +35% | Morale -15%",
              effect: { cash: 0, time: -10, stealth: -40, alert: 35, morale: -15 },
              log: "Wild chase! Tires smoking through the avenue."
            }
          ]
        },
        {
          prompt: "A police surveillance helicopter hovers above your escape route.",
          choices: [
            {
              title: "Fire Military Chaff & Smoke Screen",
              cost: "Cash -$20k | Time -10%",
              effect: { cash: -20, time: -10, stealth: 15, alert: -15, morale: 5 },
              log: "Thermal smoke blinded the helicopter's tracking."
            },
            {
              title: "Divert into Underground Subways",
              cost: "Time -20% | Morale -10%",
              effect: { cash: 0, time: -20, stealth: 10, alert: -10, morale: -10 },
              log: "Subway tunnels shielded the crew from air patrol."
            },
            {
              title: "Laser Blinder on Pilot Canopy",
              cost: "Risk Alert +20% | Time -10%",
              effect: { cash: 0, time: -10, stealth: -15, alert: 20, morale: 5 },
              log: "Chopper forced to pull up and disengage."
            }
          ]
        },
        {
          prompt: "Final rendezvous dock: The getaway speedboat engine won't turn over!",
          choices: [
            {
              title: "Hotwire Emergency Nitro Bypass",
              cost: "Time -15% | Risk Alert +20%",
              effect: { cash: 0, time: -15, stealth: -10, alert: 20, morale: 10 },
              log: "Twin turbo roared to life with flame spitting out!"
            },
            {
              title: "Pay Local Fisherman for his Trawler",
              cost: "Cash -$30k | Time -10%",
              effect: { cash: -30, time: -10, stealth: 25, alert: -20, morale: 15 },
              log: "Slipped away unseen into international waters."
            },
            {
              title: "Abandon Heavy Gear & Jet-Ski Sprint",
              cost: "Cash -$20k | Time -10%",
              effect: { cash: -20, time: -10, stealth: 10, alert: 0, morale: 10 },
              log: "Split up and vanished into the coastal fog."
            }
          ]
        }
      ]
    }
  ];

  function renderUI() {
    container.innerHTML = `
      <div class="game-container">
        <div class="game-instruction-banner">
          Make calculated tactical decisions. Balance Alert, Time, and Morale to escape with the loot!
        </div>
        <div class="heist-planner">
          <div class="heist-meters">
            <div class="meter-box">
              <div class="meter-header">
                <span>⏱ Time</span>
                <span id="txt-time">100%</span>
              </div>
              <div class="meter-bar-track">
                <div class="meter-bar-fill" id="bar-time" style="width: 100%; background: var(--neon-cyan);"></div>
              </div>
            </div>

            <div class="meter-box">
              <div class="meter-header">
                <span>💰 Loot</span>
                <span id="txt-cash">$50k</span>
              </div>
              <div class="meter-bar-track">
                <div class="meter-bar-fill" id="bar-cash" style="width: 25%; background: var(--neon-green);"></div>
              </div>
            </div>

            <div class="meter-box">
              <div class="meter-header">
                <span>👥 Morale</span>
                <span id="txt-morale">100%</span>
              </div>
              <div class="meter-bar-track">
                <div class="meter-bar-fill" id="bar-morale" style="width: 100%; background: var(--neon-purple);"></div>
              </div>
            </div>

            <div class="meter-box">
              <div class="meter-header">
                <span>👁 Stealth</span>
                <span id="txt-stealth">100%</span>
              </div>
              <div class="meter-bar-track">
                <div class="meter-bar-fill" id="bar-stealth" style="width: 100%; background: var(--neon-cyan);"></div>
              </div>
            </div>

            <div class="meter-box">
              <div class="meter-header">
                <span>🚨 Police Alert</span>
                <span id="txt-alert">0%</span>
              </div>
              <div class="meter-bar-track">
                <div class="meter-bar-fill" id="bar-alert" style="width: 0%; background: var(--neon-red);"></div>
              </div>
            </div>
          </div>

          <div class="heist-scenario-card" id="heist-card"></div>
        </div>
      </div>
    `;

    updateMeters();
    renderCurrentSituation();
  }

  function updateMeters() {
    if (!container) return;

    // Clamp stats
    stats.time = Math.max(0, Math.min(100, stats.time));
    stats.morale = Math.max(0, Math.min(100, stats.morale));
    stats.stealth = Math.max(0, Math.min(100, stats.stealth));
    stats.alert = Math.max(0, Math.min(100, stats.alert));
    stats.cash = Math.max(0, stats.cash);

    container.querySelector('#txt-time').textContent = `${stats.time}%`;
    container.querySelector('#bar-time').style.width = `${stats.time}%`;

    container.querySelector('#txt-cash').textContent = `$${stats.cash}k`;
    container.querySelector('#bar-cash').style.width = `${Math.min(100, (stats.cash / 250) * 100)}%`;

    container.querySelector('#txt-morale').textContent = `${stats.morale}%`;
    container.querySelector('#bar-morale').style.width = `${stats.morale}%`;

    container.querySelector('#txt-stealth').textContent = `${stats.stealth}%`;
    container.querySelector('#bar-stealth').style.width = `${stats.stealth}%`;

    container.querySelector('#txt-alert').textContent = `${stats.alert}%`;
    container.querySelector('#bar-alert').style.width = `${stats.alert}%`;

    // Host updates
    score = Math.floor(stats.cash * 10 + stats.stealth * 5 + stats.morale * 3);
    host.updateScore(score);
    host.updateLevel(level);
    host.updateTime(stats.time);
  }

  function renderCurrentSituation() {
    const card = container.querySelector('#heist-card');
    if (!card) return;

    const currentStageData = STAGES[level - 1];
    const currentSit = currentStageData.situations[currentTurn];

    card.innerHTML = `
      <div class="heist-stage-badge">${currentStageData.badge} - Step ${currentTurn + 1}/3</div>
      <div class="heist-prompt">${currentSit.prompt}</div>
      <div class="heist-choices">
        ${currentSit.choices.map((c, idx) => `
          <button class="choice-btn" data-choice="${idx}">
            <div class="choice-title">${c.title}</div>
            <div class="choice-meta">Impact: <span>${c.cost}</span></div>
          </button>
        `).join('')}
      </div>
    `;

    const choiceBtns = card.querySelectorAll('.choice-btn');
    choiceBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const choiceIdx = parseInt(btn.getAttribute('data-choice'), 10);
        onSelectChoice(currentSit.choices[choiceIdx]);
      });
    });
  }

  function onSelectChoice(choice) {
    if (isGameOver) return;
    host.playSound('click');

    // Apply effects
    stats.time += choice.effect.time;
    stats.cash += choice.effect.cash;
    stats.morale += choice.effect.morale;
    stats.stealth += choice.effect.stealth;
    stats.alert += choice.effect.alert;

    updateMeters();

    // Check failure conditions
    if (stats.alert >= 100) {
      triggerGameOver(false, 'SWAT BARRICADE BREACH', 'Police alert reached 100%. The team was encircled and captured.');
      return;
    }
    if (stats.time <= 0) {
      triggerGameOver(false, 'TIME RUN OUT', 'The window of opportunity slammed shut. Lockdowns trapped everyone inside.');
      return;
    }
    if (stats.morale <= 0) {
      triggerGameOver(false, 'CREW MUTINY', 'Morale collapsed. The team abandoned their positions.');
      return;
    }

    currentTurn++;

    if (currentTurn >= turnsPerStage) {
      currentTurn = 0;
      level++;

      if (level > STAGES.length) {
        // Victory!
        triggerGameOver(true, 'HEIST SUCCESSFUL!', `The crew escaped cleanly with $${stats.cash},000 in untraceable bearer bonds!`);
        return;
      } else {
        host.playSound('win');
      }
    }

    renderCurrentSituation();
  }

  function triggerGameOver(win, title, message) {
    isGameOver = true;
    host.playSound(win ? 'win' : 'error');

    host.endGame({
      win,
      score,
      title,
      message,
      details: `Loot Secured: $${stats.cash}k | Final Morale: ${stats.morale}%`
    });
  }

  return {
    id: 'bankHeist',
    name: 'Bank Heist Planner',
    description: 'Lead a tactical heist crew. Manage stealth, time, cash, and police alert.',
    difficulty: 'Hard',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path><circle cx="12" cy="16" r="1"></circle></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      level = 1;
      currentTurn = 0;
      isGameOver = false;

      stats = {
        time: 100,
        cash: 50,
        morale: 100,
        stealth: 100,
        alert: 0
      };

      score = 0;
      host.updateScore(score);
      host.updateLevel(level);

      renderUI();
    },

    destroy() {
      isGameOver = true;
      if (container) {
        container.innerHTML = '';
      }
    }
  };
})();
