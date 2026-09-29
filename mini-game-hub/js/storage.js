/**
 * Storage Module for Mini Game Hub
 * Handles saving and retrieving high scores and play statistics using localStorage.
 */

const STORAGE_KEYS = {
  HIGH_SCORES: 'mgh_high_scores_v1',
  STATS: 'mgh_global_stats_v1'
};

const Storage = {
  /**
   * Load high score for a specific game
   * @param {string} gameId 
   * @returns {number}
   */
  loadHighScore(gameId) {
    try {
      const scores = JSON.parse(localStorage.getItem(STORAGE_KEYS.HIGH_SCORES) || '{}');
      return Number(scores[gameId]) || 0;
    } catch (e) {
      console.warn('Storage read failed:', e);
      return 0;
    }
  },

  /**
   * Save high score for a specific game if it exceeds previous best
   * @param {string} gameId 
   * @param {number} score 
   * @returns {boolean} True if new high score was set
   */
  saveHighScore(gameId, score) {
    try {
      const scores = JSON.parse(localStorage.getItem(STORAGE_KEYS.HIGH_SCORES) || '{}');
      const currentHigh = Number(scores[gameId]) || 0;
      
      if (score > currentHigh) {
        scores[gameId] = Math.floor(score);
        localStorage.setItem(STORAGE_KEYS.HIGH_SCORES, JSON.stringify(scores));
        this.updateGlobalHighest();
        return true;
      }
      return false;
    } catch (e) {
      console.warn('Storage write failed:', e);
      return false;
    }
  },

  /**
   * Get all high scores
   * @returns {Record<string, number>}
   */
  getAllHighScores() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEYS.HIGH_SCORES) || '{}');
    } catch (e) {
      return {};
    }
  },

  /**
   * Record that a game was launched/played
   * @param {string} gameId 
   */
  recordGamePlay(gameId) {
    try {
      const stats = this.getGlobalStats();
      stats.totalPlays = (stats.totalPlays || 0) + 1;
      stats.perGamePlays = stats.perGamePlays || {};
      stats.perGamePlays[gameId] = (stats.perGamePlays[gameId] || 0) + 1;
      localStorage.setItem(STORAGE_KEYS.STATS, JSON.stringify(stats));
    } catch (e) {
      console.warn('Storage stats update failed:', e);
    }
  },

  /**
   * Record that a game was successfully completed or won
   * @param {string} gameId 
   */
  recordGameCompletion(gameId) {
    try {
      const stats = this.getGlobalStats();
      stats.totalCompleted = (stats.totalCompleted || 0) + 1;
      stats.completedGames = stats.completedGames || {};
      stats.completedGames[gameId] = true;
      localStorage.setItem(STORAGE_KEYS.STATS, JSON.stringify(stats));
    } catch (e) {
      console.warn('Storage completion update failed:', e);
    }
  },

  /**
   * Retrieve global game statistics
   * @returns {{ totalPlays: number, totalCompleted: number, highestScore: number, perGamePlays: Record<string, number>, completedGames: Record<string, boolean> }}
   */
  getGlobalStats() {
    try {
      const defaultStats = {
        totalPlays: 0,
        totalCompleted: 0,
        highestScore: 0,
        perGamePlays: {},
        completedGames: {}
      };
      const stats = JSON.parse(localStorage.getItem(STORAGE_KEYS.STATS) || '{}');
      return { ...defaultStats, ...stats };
    } catch (e) {
      return {
        totalPlays: 0,
        totalCompleted: 0,
        highestScore: 0,
        perGamePlays: {},
        completedGames: {}
      };
    }
  },

  /**
   * Recalculates and updates the global highest score across all games
   */
  updateGlobalHighest() {
    try {
      const scores = this.getAllHighScores();
      const highest = Object.values(scores).reduce((max, val) => Math.max(max, Number(val) || 0), 0);
      const stats = this.getGlobalStats();
      stats.highestScore = highest;
      localStorage.setItem(STORAGE_KEYS.STATS, JSON.stringify(stats));
    } catch (e) {
      console.warn('Highest score calculation error:', e);
    }
  },

  /**
   * Resets all game data (useful for testing or full reset)
   */
  resetAllStats() {
    try {
      localStorage.removeItem(STORAGE_KEYS.HIGH_SCORES);
      localStorage.removeItem(STORAGE_KEYS.STATS);
    } catch (e) {
      console.warn('Reset failed:', e);
    }
  }
};

window.Storage = Storage;
