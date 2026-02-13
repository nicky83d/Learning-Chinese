/**
 * Scores Modal Module
 * Display practice scores, stats, and game details
 */

(function() {
  'use strict';

  const ScoresModal = {
    // DOM elements (cached on init)
    elements: {},

    /**
     * Initialize the Scores modal
     */
    init: function() {
      this.cacheElements();
    },

    /**
     * Cache DOM elements for performance
     */
    cacheElements: function() {
      this.elements = {
        modal: document.getElementById('scoresModal'),
        loading: document.getElementById('scoresLoading'),
        content: document.getElementById('scoresContent'),
        empty: document.getElementById('scoresEmpty'),
        statsBody: document.getElementById('scoresStatsBody'),
        recentList: document.getElementById('scoresRecentList'),
        // Game details modal
        detailsModal: document.getElementById('gameDetailsModal'),
        detailsLoading: document.getElementById('gameDetailsLoading'),
        detailsContent: document.getElementById('gameDetailsContent'),
        detailsTitle: document.getElementById('gameDetailsTitle'),
        detailsSummary: document.getElementById('gameDetailsSummary'),
        detailsResults: document.getElementById('gameDetailsResults'),
        detailsResultsList: document.getElementById('gameDetailsResultsList'),
        detailsEmpty: document.getElementById('gameDetailsEmpty')
      };
    },

    /**
     * Open the Scores modal
     */
    open: function() {
      if (this.elements.modal) {
        this.elements.modal.style.display = 'flex';
      }
      this.loadScores();
    },

    /**
     * Close the Scores modal
     */
    close: function() {
      if (this.elements.modal) {
        this.elements.modal.style.display = 'none';
      }
    },

    /**
     * Reset all user scores
     */
    resetScores: async function() {
      if (!confirm('This will delete ALL your practice scores. Are you sure?')) {
        return;
      }
      
      try {
        const response = await fetch('/api/reset-my-scores', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'}
        });
        
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Failed to reset scores');
        }
        
        const result = await response.json();
        alert('✅ Reset complete! Deleted ' + result.deleted_count + ' practice scores.');
        
        // Reload the scores display
        this.loadScores();
      } catch (error) {
        console.error('Error resetting scores:', error);
        alert('Error resetting scores: ' + error.message);
      }
    },

    /**
     * Load and display scores
     */
    loadScores: async function() {
      if (this.elements.loading) {
        this.elements.loading.style.display = 'block';
      }
      if (this.elements.content) {
        this.elements.content.style.display = 'none';
      }
      if (this.elements.empty) {
        this.elements.empty.style.display = 'none';
      }
      
      try {
        // Fetch stats and history in parallel
        const [statsRes, historyRes] = await Promise.all([
          fetch('/api/user/practice/stats'),
          fetch('/api/user/practice/history?limit=10')
        ]);
        
        const stats = await statsRes.json();
        const history = await historyRes.json();
        
        if (statsRes.status === 401 || historyRes.status === 401) {
          if (this.elements.loading) {
            this.elements.loading.style.display = 'none';
          }
          if (this.elements.empty) {
            this.elements.empty.style.display = 'block';
            this.elements.empty.innerHTML = '<p style="color: var(--text-muted);">Please log in to view your scores.</p>';
          }
          return;
        }
        
        // Check if there are any games played
        const totalGames = (stats.listening?.total_games || 0) + 
                           (stats.words?.total_games || 0) + 
                           (stats.speaking?.total_games || 0) +
                           (stats.drawing?.total_games || 0);
        
        if (totalGames === 0) {
          if (this.elements.loading) {
            this.elements.loading.style.display = 'none';
          }
          if (this.elements.empty) {
            this.elements.empty.style.display = 'block';
          }
          return;
        }
        
        // Populate stats table
        if (this.elements.statsBody) {
          this.elements.statsBody.innerHTML = this.renderStatsRow('👂 Listening', stats.listening) +
                                              this.renderStatsRow('📝 Words', stats.words) +
                                              this.renderStatsRow('🎤 Speaking', stats.speaking) +
                                              this.renderStatsRow('✍️ Drawing', stats.drawing);
        }
        
        // Populate recent games
        if (this.elements.recentList) {
          if (history.length === 0) {
            this.elements.recentList.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No recent games</p>';
          } else {
            this.elements.recentList.innerHTML = history.map(function(game) {
              return ScoresModal.renderGameRow(game);
            }).join('');
          }
        }
        
        if (this.elements.loading) {
          this.elements.loading.style.display = 'none';
        }
        if (this.elements.content) {
          this.elements.content.style.display = 'block';
        }
        
      } catch (error) {
        console.error('Error loading scores:', error);
        if (this.elements.loading) {
          this.elements.loading.style.display = 'none';
        }
        if (this.elements.empty) {
          this.elements.empty.style.display = 'block';
          this.elements.empty.innerHTML = '<p style="color: var(--text-muted);">Error loading scores. Please try again.</p>';
        }
      }
    },

    /**
     * Render a stats table row
     * @param {string} label - Row label
     * @param {Object} stats - Stats for this game type
     * @returns {string} HTML string
     */
    renderStatsRow: function(label, stats) {
      return '<tr>' +
        '<td style="padding: 10px; border: 1px solid var(--border-color);">' + label + '</td>' +
        '<td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">' + (stats?.total_games || 0) + '</td>' +
        '<td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">' + (stats?.average_percentage || 0) + '%</td>' +
        '<td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">' + (stats?.best_score || 0) + '%</td>' +
      '</tr>';
    },

    /**
     * Render a game history row
     * @param {Object} game - Game data
     * @returns {string} HTML string
     */
    renderGameRow: function(game) {
      const gameIcon = game.game_type === 'words' ? '📝' : 
                      game.game_type === 'speaking' ? '🎤' : 
                      game.game_type === 'drawing' ? '✍️' : '👂';
      const gameLabel = game.game_type.charAt(0).toUpperCase() + game.game_type.slice(1);
      const date = game.played_at ? new Date(game.played_at).toLocaleDateString() : 'Unknown';
      const time = game.played_at ? new Date(game.played_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '';
      const scoreColor = game.percentage >= 80 ? '#51cf66' : 
                        game.percentage >= 60 ? '#fcc419' : '#ff6b6b';
      
      return '<div onclick="VocabApp.ScoresModal.openDetails(' + game.id + ')" style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid var(--border-color); cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background=\'var(--card-bg)\'" onmouseout="this.style.background=\'transparent\'">' +
        '<div>' +
          '<span style="font-size: 1.1em;">' + gameIcon + ' ' + gameLabel + '</span>' +
          '<span style="color: var(--text-muted); font-size: 0.85em; margin-left: 10px;">' + date + ' ' + time + '</span>' +
        '</div>' +
        '<div style="text-align: right; display: flex; align-items: center; gap: 8px;">' +
          '<span style="font-weight: 600; color: ' + scoreColor + ';">' + (game.percentage || 0) + '%</span>' +
          '<span style="color: var(--text-muted); font-size: 0.85em;">(' + game.score + '/' + game.total_questions + ')</span>' +
          '<span style="color: var(--text-muted); font-size: 0.9em;">→</span>' +
        '</div>' +
      '</div>';
    },

    /**
     * Open game details modal
     * @param {number} gameId - Game ID
     */
    openDetails: function(gameId) {
      if (this.elements.detailsModal) {
        this.elements.detailsModal.style.display = 'flex';
      }
      this.loadGameDetails(gameId);
    },

    /**
     * Close game details modal
     */
    closeDetails: function() {
      if (this.elements.detailsModal) {
        this.elements.detailsModal.style.display = 'none';
      }
    },

    /**
     * Load game details
     * @param {number} gameId - Game ID
     */
    loadGameDetails: async function(gameId) {
      if (this.elements.detailsLoading) {
        this.elements.detailsLoading.style.display = 'block';
      }
      if (this.elements.detailsContent) {
        this.elements.detailsContent.style.display = 'none';
      }
      
      try {
        const response = await fetch('/api/user/practice/' + gameId + '/details');
        if (!response.ok) throw new Error('Failed to load game details');
        
        const data = await response.json();
        
        const gameIcon = data.game_type === 'words' ? '📝' : 
                        data.game_type === 'speaking' ? '🎤' : 
                        data.game_type === 'drawing' ? '✍️' : '👂';
        const gameLabel = data.game_type.charAt(0).toUpperCase() + data.game_type.slice(1);
        const date = data.played_at ? new Date(data.played_at).toLocaleDateString() : 'Unknown';
        const time = data.played_at ? new Date(data.played_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '';
        const scoreColor = data.percentage >= 80 ? '#51cf66' : 
                          data.percentage >= 60 ? '#fcc419' : '#ff6b6b';
        
        // Update title
        if (this.elements.detailsTitle) {
          this.elements.detailsTitle.textContent = gameIcon + ' ' + gameLabel + ' Results';
        }
        
        // Show summary
        if (this.elements.detailsSummary) {
          this.elements.detailsSummary.innerHTML = 
            '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">' +
              '<div>' +
                '<div style="font-size: 1.3em; font-weight: 600; color: ' + scoreColor + ';">' + (data.percentage || 0) + '%</div>' +
                '<div style="color: var(--text-muted); font-size: 0.9em;">' + data.score + '/' + data.total_questions + ' correct</div>' +
              '</div>' +
              '<div style="text-align: right;">' +
                '<div style="color: var(--text-muted); font-size: 0.9em;">' + date + '</div>' +
                '<div style="color: var(--text-muted); font-size: 0.85em;">' + time + '</div>' +
              '</div>' +
            '</div>';
        }
        
        // Show results or empty state
        if (data.results && data.results.length > 0) {
          if (this.elements.detailsResults) {
            this.elements.detailsResults.style.display = 'block';
          }
          if (this.elements.detailsEmpty) {
            this.elements.detailsEmpty.style.display = 'none';
          }
          
          if (this.elements.detailsResultsList) {
            this.elements.detailsResultsList.innerHTML = data.results.map(function(r) {
              return ScoresModal.renderResultRow(r, gameId);
            }).join('');
          }
        } else {
          if (this.elements.detailsResults) {
            this.elements.detailsResults.style.display = 'none';
          }
          if (this.elements.detailsEmpty) {
            this.elements.detailsEmpty.style.display = 'block';
          }
        }
        
        if (this.elements.detailsLoading) {
          this.elements.detailsLoading.style.display = 'none';
        }
        if (this.elements.detailsContent) {
          this.elements.detailsContent.style.display = 'block';
        }
        
      } catch (error) {
        console.error('Error loading game details:', error);
        if (this.elements.detailsLoading) {
          this.elements.detailsLoading.style.display = 'none';
        }
        if (this.elements.detailsContent) {
          this.elements.detailsContent.style.display = 'block';
        }
        if (this.elements.detailsSummary) {
          this.elements.detailsSummary.innerHTML = '<p style="color: var(--text-muted);">Error loading game details.</p>';
        }
        if (this.elements.detailsResults) {
          this.elements.detailsResults.style.display = 'none';
        }
        if (this.elements.detailsEmpty) {
          this.elements.detailsEmpty.style.display = 'none';
        }
      }
    },

    /**
     * Render a result row
     * @param {Object} r - Result data
     * @param {number} gameId - Game ID
     * @returns {string} HTML string
     */
    renderResultRow: function(r, gameId) {
      const statusIcon = r.is_correct ? '✅' : '❌';
      const statusColor = r.is_correct ? '#51cf66' : '#ff6b6b';
      
      let html = '<div style="padding: 12px; margin-bottom: 10px; background: var(--card-bg); border-radius: 8px; border-left: 4px solid ' + statusColor + ';">' +
        '<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">' +
          '<div style="font-weight: 600;">' + statusIcon + ' Question ' + r.question_number + '</div>' +
          (r.word_hanzi ? '<div style="font-size: 1.2em;">' + r.word_hanzi + '</div>' : '') +
        '</div>' +
        (r.word_pinyin ? '<div style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 4px;">' + r.word_pinyin + '</div>' : '') +
        (r.word_english ? '<div style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 8px;">' + r.word_english + '</div>' : '');
      
      if (!r.is_correct) {
        html += '<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border-color);">' +
          '<div style="font-size: 0.85em; margin-bottom: 4px;">' +
            '<span style="color: var(--text-muted);">Your answer:</span> ' +
            '<span style="color: #ff6b6b;">' + (r.user_answer || 'No answer') + '</span>' +
          '</div>' +
          '<div style="font-size: 0.85em; margin-bottom: 8px;">' +
            '<span style="color: var(--text-muted);">Correct answer:</span> ' +
            '<span style="color: #51cf66;">' + (r.correct_answer || 'N/A') + '</span>' +
          '</div>';
        
        if (r.feedback) {
          html += '<div style="margin-top: 8px; padding: 10px; background: rgba(255, 193, 7, 0.1); border-radius: 6px; font-size: 0.9em;">' +
            '<div style="font-weight: 600; margin-bottom: 4px;">💡 AI Tip:</div>' +
            r.feedback +
          '</div>';
        } else {
          html += '<button onclick="VocabApp.ScoresModal.requestFeedback(' + gameId + ', ' + r.question_number + ', this)" class="secondary" style="padding: 6px 12px; font-size: 0.85em; margin-top: 4px;">' +
            '💡 Get AI Tips' +
          '</button>';
        }
        
        html += '</div>';
      }
      
      html += '</div>';
      return html;
    },

    /**
     * Request AI feedback for a question
     * @param {number} gameId - Game ID
     * @param {number} questionNumber - Question number
     * @param {HTMLElement} buttonEl - Button element
     */
    requestFeedback: async function(gameId, questionNumber, buttonEl) {
      buttonEl.disabled = true;
      buttonEl.textContent = '⏳ Loading...';
      
      try {
        // First get the details to find this question
        const detailsRes = await fetch('/api/user/practice/' + gameId + '/details');
        const details = await detailsRes.json();
        
        const question = details.results.find(function(r) {
          return r.question_number === questionNumber;
        });
        if (!question) {
          buttonEl.textContent = '❌ Error';
          return;
        }
        
        // Request AI feedback
        const response = await fetch('/api/user/practice/feedback', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            game_type: details.game_type,
            question_type: question.question_type,
            correct_answer: question.correct_answer,
            user_answer: question.user_answer,
            word_hanzi: question.word_hanzi,
            word_pinyin: question.word_pinyin,
            word_english: question.word_english
          })
        });
        
        const data = await response.json();
        
        if (data.feedback) {
          // Replace button with feedback
          const feedbackHtml = 
            '<div style="margin-top: 8px; padding: 10px; background: rgba(255, 193, 7, 0.1); border-radius: 6px; font-size: 0.9em;">' +
              '<div style="font-weight: 600; margin-bottom: 4px;">💡 AI Tip: ' + (data.cached ? '(cached)' : '') + '</div>' +
              data.feedback +
            '</div>';
          buttonEl.outerHTML = feedbackHtml;
        } else {
          buttonEl.textContent = '❌ No tips available';
        }
        
      } catch (error) {
        console.error('Error requesting feedback:', error);
        buttonEl.textContent = '❌ Error';
        buttonEl.disabled = false;
      }
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      ScoresModal.init();
    });
  } else {
    ScoresModal.init();
  }

  // Expose to VocabApp namespace
  window.VocabApp = window.VocabApp || {};
  window.VocabApp.ScoresModal = ScoresModal;

  // Global functions for backward compatibility
  window.openScoresModal = function() {
    ScoresModal.open();
  };
  
  window.closeScoresModal = function() {
    ScoresModal.close();
  };
  
  window.resetMyScores = function() {
    ScoresModal.resetScores();
  };
  
  window.loadScores = function() {
    ScoresModal.loadScores();
  };
  
  window.openGameDetailsModal = function(gameId) {
    ScoresModal.openDetails(gameId);
  };
  
  window.closeGameDetailsModal = function() {
    ScoresModal.closeDetails();
  };
  
  window.requestFeedback = function(gameId, questionNumber, buttonEl) {
    ScoresModal.requestFeedback(gameId, questionNumber, buttonEl);
  };

})();
