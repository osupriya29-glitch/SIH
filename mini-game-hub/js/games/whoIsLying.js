/**
 * Game 3: Who Is Lying?
 * Fictional detective mystery deduction puzzle.
 */

window.WhoIsLying = (function () {
  let container = null;
  let host = null;
  let level = 1;
  let score = 0;
  let timeLeft = 60;
  let timerInterval = null;
  let currentCase = null;
  let caseAnswered = false;

  // Rich collection of mystery scenarios with strict deductive logic
  const CASE_TEMPLATES = [
    {
      title: "The Cryo-Chamber Sabotage",
      scenario: "At 03:00 AM, the station's primary cryo-pod cooling valve was tampered with.",
      clues: [
        "Biometric log: Cryo-Lab was locked by security between 02:45 AM and 03:15 AM.",
        "Airlock log: Officer Vance entered the hydroponics bay at 02:50 AM.",
        "Maintenance report: The ventilation ducts were fully sealed with laser mesh."
      ],
      suspects: [
        {
          id: 'vance',
          name: 'Officer Vance',
          role: 'Security Guard',
          avatar: '👮‍♂️',
          statement: "I was patrolling Hydroponics from 02:50 onwards. Check the logs, I didn't go near Cryo.",
          isLiar: false
        },
        {
          id: 'dr_reed',
          name: 'Dr. Reed',
          role: 'Chief Medical',
          avatar: '👨‍⚕️',
          statement: "I walked through the Cryo-Lab doors at 03:05 AM to grab synthetic saline.",
          isLiar: true,
          explanation: "Dr. Reed claimed he walked through the Cryo-Lab doors at 03:05 AM, but the verified biometric log confirms the Cryo-Lab was electronically locked from 02:45 AM to 03:15 AM!"
        },
        {
          id: 'tara',
          name: 'Tara Lin',
          role: 'Systems Engineer',
          avatar: '👩‍💻',
          statement: "I was in the server core repairing optical fiber until sunrise.",
          isLiar: false
        }
      ]
    },
    {
      title: "The Quantum Core Leak",
      scenario: "A classified quantum capacitor went missing from the sub-level workshop.",
      clues: [
        "Radiation sensor: High radiation was detected exclusively in the East Wing elevator.",
        "Security camera: Dr. Thorne carried a heavy thermal case down the North stairway.",
        "Janitorial log: The cargo lift was out of service all night."
      ],
      suspects: [
        {
          id: 'dr_thorne',
          name: 'Dr. Thorne',
          role: 'Head Physicist',
          avatar: '🧑‍🔬',
          statement: "I used the North stairway to move calibration tools to my office.",
          isLiar: false
        },
        {
          id: 'kane',
          name: 'Kane Bishop',
          role: 'Cargo Handler',
          avatar: '👷‍♂️',
          statement: "I transported the spare batteries via the cargo lift around midnight.",
          isLiar: true,
          explanation: "Kane claimed he used the cargo lift around midnight, but the verified maintenance log states the cargo lift was completely out of service all night!"
        },
        {
          id: 'maya',
          name: 'Maya Cross',
          role: 'Drone Specialist',
          avatar: '👩‍🔧',
          statement: "My scout drone was docked in the hangar undergoing firmware flashing.",
          isLiar: false
        }
      ]
    },
    {
      title: "The Midnight Server Wipe",
      scenario: "Critical AI training checkpoints were purged from the secure mainframe at 22:15.",
      clues: [
        "Keycard terminal: Alex's physical card was swiped at the cafeteria at 22:12.",
        "Network monitor: The purge was initiated locally using an authorized physical terminal in Bay 4.",
        "Camera footage: Terminal Bay 4 was completely pitch black; nobody had night-vision goggles except Ops."
      ],
      suspects: [
        {
          id: 'alex',
          name: 'Alex Mercer',
          role: 'Junior Dev',
          avatar: '👨‍💻',
          statement: "I was getting coffee in the cafeteria when the server alert buzzed.",
          isLiar: false
        },
        {
          id: 'sam',
          name: 'Samira Quinn',
          role: 'Ops Director',
          avatar: '👩‍💼',
          statement: "I was in Terminal Bay 4 with the ceiling floodlights on, debugging routing tables.",
          isLiar: true,
          explanation: "Samira claimed she was working in Terminal Bay 4 with floodlights on, but security camera logs confirm Bay 4 was completely in the pitch black!"
        },
        {
          id: 'ronan',
          name: 'Ronan Cole',
          role: 'Database Admin',
          avatar: '🧔',
          statement: "I had already logged off from my dorm terminal at 21:30.",
          isLiar: false
        }
      ]
    },
    {
      title: "The Vault Microfilm Theft",
      scenario: "A titanium vault containing the micro-blueprints was bypassed without explosives.",
      clues: [
        "Laser grid log: The corridor lasers were active and unbroken throughout the heist.",
        "Ceiling hatch: The rooftop service hatch had fresh rope abrasions.",
        "Security record: Guard Dex stayed posted right in front of the main corridor door."
      ],
      suspects: [
        {
          id: 'dex',
          name: 'Dex Callahan',
          role: 'Hallway Sentry',
          avatar: '👮',
          statement: "I watched the main corridor the entire shift; nobody walked through that hallway.",
          isLiar: false
        },
        {
          id: 'elena',
          name: 'Elena Frost',
          role: 'Acrobat Infiltrator',
          avatar: '🕵️‍♀️',
          statement: "I sprinted through the hallway laser grid without tripping the alarms.",
          isLiar: true,
          explanation: "Elena claimed she sprinted through the corridor laser grid, but the system logs confirm the lasers were active and continuous—nobody crossed that floor!"
        },
        {
          id: 'jin',
          name: 'Jin Sato',
          role: 'Rooftop Courier',
          avatar: '🧑‍🚀',
          statement: "I saw an open maintenance hatch on the roof when I arrived with rations.",
          isLiar: false
        }
      ]
    },
    {
      title: "The Poisoned Hyper-Drive Fuel",
      scenario: "Contaminant was injected into Fuel Tank Delta before scheduled launch.",
      clues: [
        "Hazmat report: Fuel Tank Delta requires Level-4 Hazmat suits to withstand toxic fumes.",
        "Equipment locker: Only suit #3 and suit #7 were signed out.",
        "Sign-out log: Engineer Kael signed out suit #3, and Pilot Nova signed out suit #7."
      ],
      suspects: [
        {
          id: 'kael',
          name: 'Kaelen Voss',
          role: 'Fuel Engineer',
          avatar: '👨‍🔧',
          statement: "I took suit #3 to replace the fuel filter on Tank Alpha.",
          isLiar: false
        },
        {
          id: 'nova',
          name: 'Nova Starling',
          role: 'Test Pilot',
          avatar: '👩‍✈️',
          statement: "I took suit #7 to inspect the thruster bells outside the hull.",
          isLiar: false
        },
        {
          id: 'boris',
          name: 'Boris Chen',
          role: 'Lab Assistant',
          avatar: '👨‍🔬',
          statement: "I went into Fuel Tank Delta in my standard cloth uniform to retrieve a lost wrench.",
          isLiar: true,
          explanation: "Boris claimed he entered Fuel Tank Delta in a standard cloth uniform, but Tank Delta's atmosphere is immediately lethal without a Level-4 Hazmat suit!"
        }
      ]
    }
  ];

  function renderUI() {
    container.innerHTML = `
      <div class="game-container">
        <div class="game-instruction-banner">
          Read the case clues and suspect statements. Cross-reference facts to identify who is lying!
        </div>
        <div class="detective-board" id="detective-board"></div>
      </div>
    `;
  }

  function loadCase() {
    caseAnswered = false;
    const board = container.querySelector('#detective-board');
    if (!board) return;

    // Pick case template based on level
    const caseIndex = (level - 1) % CASE_TEMPLATES.length;
    currentCase = CASE_TEMPLATES[caseIndex];

    board.innerHTML = `
      <div class="case-briefing">
        <h4>CASE #${level}: ${currentCase.title}</h4>
        <p>${currentCase.scenario}</p>
      </div>

      <div class="clues-box">
        <h5>Verified Forensic Evidence:</h5>
        <ul>
          ${currentCase.clues.map(c => `<li>${c}</li>`).join('')}
        </ul>
      </div>

      <div class="suspects-grid">
        ${currentCase.suspects.map(s => `
          <div class="suspect-card" data-id="${s.id}">
            <div class="suspect-header">
              <div class="suspect-avatar">${s.avatar}</div>
              <div>
                <div class="suspect-name">${s.name}</div>
                <div class="suspect-role">${s.role}</div>
              </div>
            </div>
            <div class="suspect-statement">"${s.statement}"</div>
            <button class="btn-accuse" data-id="${s.id}">ACCUSE SUSPECT</button>
          </div>
        `).join('')}
      </div>

      <div id="solution-slot"></div>
    `;

    const accuseBtns = board.querySelectorAll('.btn-accuse');
    accuseBtns.forEach(btn => {
      btn.addEventListener('click', () => onAccuse(btn.getAttribute('data-id')));
    });
  }

  function onAccuse(suspectId) {
    if (caseAnswered) return;
    caseAnswered = true;
    stopTimer();

    const suspect = currentCase.suspects.find(s => s.id === suspectId);
    const liar = currentCase.suspects.find(s => s.isLiar);
    const solutionSlot = container.querySelector('#solution-slot');

    if (suspect && suspect.isLiar) {
      // Correct!
      host.playSound('win');
      const caseScore = 300 + timeLeft * 10;
      score += caseScore;
      host.updateScore(score);

      solutionSlot.innerHTML = `
        <div class="solution-explanation-card">
          <h4 style="color: var(--neon-green); margin-bottom: 0.5rem; text-transform: uppercase;">
            ✔ CASE SOLVED! ${suspect.name} was lying!
          </h4>
          <p style="font-size: 0.9rem; color: var(--text-main); margin-bottom: 1rem;">
            ${liar.explanation}
          </p>
          <button id="btn-next-case" class="btn-primary-launch" style="padding: 0.6rem 1.5rem; font-size: 0.9rem;">
            NEXT MYSTERY →
          </button>
        </div>
      `;

      container.querySelector('#btn-next-case').addEventListener('click', () => {
        level++;
        host.updateLevel(level);
        loadCase();
        startTimer();
      });
    } else {
      // Wrong suspect
      host.playSound('error');
      solutionSlot.innerHTML = `
        <div class="solution-explanation-card" style="border-color: var(--neon-red); background: rgba(255, 51, 75, 0.1);">
          <h4 style="color: var(--neon-red); margin-bottom: 0.5rem; text-transform: uppercase;">
            ✖ WRONG ACCUSATION! ${suspect ? suspect.name : 'Unknown'} told the truth!
          </h4>
          <p style="font-size: 0.9rem; color: var(--text-main); margin-bottom: 1rem;">
            The actual culprit was <strong>${liar.name}</strong>.<br>
            ${liar.explanation}
          </p>
        </div>
      `;

      setTimeout(() => {
        host.endGame({
          win: false,
          score,
          title: 'MISCARRIAGE OF JUSTICE',
          message: `You accused an innocent person. The real liar escaped.`,
          details: `Cases Solved: ${level - 1}`
        });
      }, 3500);
    }
  }

  function startTimer() {
    stopTimer();
    timeLeft = 60;
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
          title: 'INVESTIGATION TIMED OUT',
          message: 'The suspect fled the jurisdiction before you made an accusation.',
          details: `Cases Solved: ${level - 1}`
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
    id: 'whoIsLying',
    name: 'Who Is Lying?',
    description: 'Investigate fictional crimes and cross-examine clues to expose the one liar.',
    difficulty: 'Medium',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><path d="M11 8a3 3 0 0 0-3 3"></path></svg>`,

    init(targetContainer, hostApi) {
      container = targetContainer;
      host = hostApi;
      this.restart();
    },

    restart() {
      stopTimer();
      level = 1;
      score = 0;
      caseAnswered = false;
      host.updateScore(score);
      host.updateLevel(level);

      renderUI();
      loadCase();
      startTimer();
    },

    destroy() {
      stopTimer();
      caseAnswered = false;
      if (container) {
        container.innerHTML = '';
      }
    }
  };
})();
