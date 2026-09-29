/**
 * Utilities & Helper Suite for Mini Game Hub
 * Includes Web Audio Sound Synthesizer, Timer, Formatters, and Math Helpers.
 */

// Simple Web Audio Synthesizer (Zero external assets needed, works 100% offline)
const SoundFX = (function () {
  let audioCtx = null;
  let muted = false;

  function getAudioContext() {
    if (!audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        audioCtx = new AudioContextClass();
      }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  }

  function playTone(freq, type = 'sine', duration = 0.1, gainVal = 0.15) {
    if (muted) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = type;
      osc.frequency.setValueAtTime(freq, ctx.currentTime);

      gain.gain.setValueAtTime(gainVal, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch (e) {
      // Audio autoplay policy fallback
    }
  }

  return {
    isMuted() {
      return muted;
    },
    toggleMute() {
      muted = !muted;
      return muted;
    },
    setMuted(val) {
      muted = !!val;
    },
    play(soundName) {
      if (muted) return;
      try {
        const ctx = getAudioContext();
        if (!ctx) return;

        switch (soundName) {
          case 'click':
            playTone(800, 'sine', 0.04, 0.08);
            break;
          case 'beep':
            playTone(440, 'triangle', 0.08, 0.1);
            break;
          case 'tick':
            playTone(1200, 'square', 0.02, 0.03);
            break;
          case 'success':
            playTone(523.25, 'sine', 0.08, 0.12);
            setTimeout(() => playTone(659.25, 'sine', 0.08, 0.12), 70);
            setTimeout(() => playTone(783.99, 'sine', 0.14, 0.15), 140);
            break;
          case 'win':
            playTone(440, 'triangle', 0.1, 0.15);
            setTimeout(() => playTone(554.37, 'triangle', 0.1, 0.15), 90);
            setTimeout(() => playTone(659.25, 'triangle', 0.1, 0.15), 180);
            setTimeout(() => playTone(880, 'triangle', 0.25, 0.2), 270);
            break;
          case 'error':
            playTone(180, 'sawtooth', 0.15, 0.15);
            setTimeout(() => playTone(140, 'sawtooth', 0.2, 0.18), 120);
            break;
          case 'alert':
            playTone(900, 'square', 0.08, 0.1);
            setTimeout(() => playTone(600, 'square', 0.08, 0.1), 100);
            break;
          case 'explosion':
            if (ctx) {
              const bufferSize = ctx.sampleRate * 0.3;
              const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
              const data = buffer.getChannelData(0);
              for (let i = 0; i < bufferSize; i++) {
                data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.08));
              }
              const noise = ctx.createBufferSource();
              noise.buffer = buffer;
              const filter = ctx.createBiquadFilter();
              filter.type = 'lowpass';
              filter.frequency.value = 400;
              const gain = ctx.createGain();
              gain.gain.setValueAtTime(0.25, ctx.currentTime);
              gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
              noise.connect(filter);
              filter.connect(gain);
              gain.connect(ctx.destination);
              noise.start();
            }
            break;
          case 'cut':
            playTone(1400, 'sawtooth', 0.05, 0.07);
            break;
          case 'powerup':
            playTone(300, 'sine', 0.06, 0.1);
            setTimeout(() => playTone(450, 'sine', 0.06, 0.1), 50);
            setTimeout(() => playTone(600, 'sine', 0.06, 0.12), 100);
            setTimeout(() => playTone(900, 'sine', 0.15, 0.15), 150);
            break;
          default:
            playTone(600, 'sine', 0.05, 0.1);
        }
      } catch (e) {
        // Safe fail
      }
    }
  };
})();

/**
 * Reusable Game Timer
 */
class GameTimer {
  constructor({ duration = 30, onTick = null, onComplete = null, countUp = false } = {}) {
    this.initialDuration = duration;
    this.duration = duration;
    this.time = countUp ? 0 : duration;
    this.countUp = countUp;
    this.onTick = onTick;
    this.onComplete = onComplete;
    this.intervalId = null;
    this.isRunning = false;
  }

  start() {
    this.stop();
    this.isRunning = true;
    this.tick();
    this.intervalId = setInterval(() => {
      if (!this.isRunning) return;
      if (this.countUp) {
        this.time++;
        this.tick();
      } else {
        this.time--;
        this.tick();
        if (this.time <= 0) {
          this.stop();
          if (typeof this.onComplete === 'function') {
            this.onComplete();
          }
        }
      }
    }, 1000);
  }

  tick() {
    if (typeof this.onTick === 'function') {
      this.onTick(this.time);
    }
  }

  pause() {
    this.isRunning = false;
  }

  resume() {
    if (!this.isRunning && this.intervalId) {
      this.isRunning = true;
    }
  }

  stop() {
    this.isRunning = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  reset(newDuration = null) {
    this.stop();
    if (newDuration !== null) {
      this.initialDuration = newDuration;
      this.duration = newDuration;
    }
    this.time = this.countUp ? 0 : this.duration;
    this.tick();
  }

  getTime() {
    return this.time;
  }

  addTime(seconds) {
    this.time = Math.max(0, this.time + seconds);
    this.tick();
  }
}

// Utility helper functions
const Utils = {
  /**
   * Formats a score with leading zeros (e.g. 42 -> "0042")
   */
  formatScore(score, digits = 4) {
    const num = Math.max(0, Math.floor(score || 0));
    return String(num).padStart(digits, '0');
  },

  /**
   * Formats seconds into MM:SS
   */
  formatTime(totalSeconds) {
    const sec = Math.max(0, Math.floor(totalSeconds || 0));
    const mins = Math.floor(sec / 60);
    const remainingSecs = sec % 60;
    return `${String(mins).padStart(2, '0')}:${String(remainingSecs).padStart(2, '0')}`;
  },

  /**
   * Random integer in [min, max] inclusive
   */
  randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  },

  /**
   * Pick random item from an array
   */
  randomChoice(arr) {
    if (!arr || arr.length === 0) return null;
    return arr[Math.floor(Math.random() * arr.length)];
  },

  /**
   * Return shuffled copy of an array (Fisher-Yates)
   */
  shuffle(arr) {
    const copy = [...arr];
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  },

  /**
   * Clamp a value between min and max
   */
  clamp(val, min, max) {
    return Math.min(Math.max(val, min), max);
  },

  /**
   * Shorthand query selector
   */
  $(selector, context = document) {
    return context.querySelector(selector);
  },

  /**
   * Shorthand query selector all
   */
  $$(selector, context = document) {
    return Array.from(context.querySelectorAll(selector));
  }
};

window.SoundFX = SoundFX;
window.GameTimer = GameTimer;
window.Utils = Utils;
