/**
 * Words Quiz Game Module
 * Flashcard-style quiz for vocabulary practice
 * 
 * Note: This module is more integrated with the main page than others
 * because the Words quiz transforms the main view rather than being modal-based.
 */

(function() {
  'use strict';

  const WordsQuiz = {
    // State
    mode: 'chinese',
    currentWord: null,
    currentOptions: null,
    state: 'showing-options', // 'showing-options' or 'showing-result'
    selectedOptionId: null,
    wins: 0,

    // DOM elements (cached on init)
    elements: {},

    /**
     * Initialize the Words quiz
     */
    init: function() {
      this.cacheElements();
      this.loadWins();
      this.bindEvents();
    },

    /**
     * Cache DOM elements for performance
     */
    cacheElements: function() {
      this.elements = {
        container: document.getElementById('quiz-container'),
        header: document.getElementById('quizHeader'),
        card: document.getElementById('quizCard'),
        counter: document.getElementById('quizCounter'),
        optionsContainer: document.getElementById('quizOptionsContainer'),
        options: document.getElementById('quizOptions'),
        resultFeedback: document.getElementById('quizResultFeedback'),
        resultStatus: document.getElementById('resultStatus'),
        resultExplanation: document.getElementById('resultExplanation'),
        validateBtn: document.getElementById('quizValidateBtn'),
        nextBtn: document.getElementById('nextQuizCardAlt'),
        trophyDisplay: document.getElementById('trophyDisplay'),
        trophyQuality: document.getElementById('trophyQuality'),
        streakCount: document.getElementById('streakCount'),
        mainControls: document.getElementById('mainControls'),
        grid: document.getElementById('vocab-grid')
      };
    },

    /**
     * Bind event listeners
     */
    bindEvents: function() {
      const self = this;
      
      // Validate button
      if (this.elements.validateBtn) {
        this.elements.validateBtn.addEventListener('click', function() {
          self.validateAnswer();
        });
      }
      
      // Next card button (in result feedback)
      if (this.elements.nextBtn) {
        this.elements.nextBtn.addEventListener('click', function() {
          self.showNextCard();
        });
      }
    },

    /**
     * Load quiz wins from localStorage
     */
    loadWins: function() {
      this.wins = parseInt(localStorage.getItem('quizWins') || '0');
      this.updateStreakDisplay();
    },

    /**
     * Save quiz wins to localStorage
     */
    saveWins: function() {
      localStorage.setItem('quizWins', this.wins.toString());
      this.updateStreakDisplay();
    },

    /**
     * Update the streak display
     */
    updateStreakDisplay: function() {
      if (this.elements.streakCount) {
        this.elements.streakCount.textContent = this.wins % 5;
      }
    },

    /**
     * Reset quiz wins
     */
    resetWins: function() {
      this.wins = 0;
      this.saveWins();
    },

    /**
     * Add a quiz win
     */
    addWin: function() {
      this.wins++;
      this.saveWins();
      if (this.wins % 5 === 0) {
        this.showTrophy();
      }
    },

    /**
     * Show the trophy display
     */
    showTrophy: function() {
      const qualityPct = 90 + Math.random() * 10;
      if (this.elements.trophyQuality) {
        this.elements.trophyQuality.innerHTML = 'Quality Score: <strong>' + qualityPct.toFixed(0) + '%</strong>';
      }
      if (this.elements.trophyDisplay) {
        this.elements.trophyDisplay.style.display = 'block';
      }
    },

    /**
     * Start the quiz
     * @param {string} mode - Quiz mode ('chinese', 'japanese', 'french')
     * @param {Array} words - Words to quiz on
     */
    start: function(mode, words) {
      if (!words || words.length === 0) {
        alert("No words available with current filters. Try broadening your search or category.");
        return;
      }

      this.mode = mode;
      
      // Update global state (for backward compatibility)
      window.currentQuizMode = mode;
      window.currentWords = words;

      // Hide main controls, show quiz
      if (this.elements.mainControls) {
        this.elements.mainControls.style.display = 'none';
      }
      if (this.elements.grid) {
        this.elements.grid.style.display = 'none';
      }
      if (this.elements.header) {
        this.elements.header.style.display = 'block';
      }
      if (this.elements.container) {
        this.elements.container.style.display = 'block';
      }
      
      // Start tracking session for 'words' practice
      VocabApp.startPracticeSession('words');

      // Update counter
      let modeText;
      if (mode === 'chinese') {
        modeText = 'Chinese → Translations';
      } else if (mode === 'japanese') {
        modeText = 'Japanese → Translations';
      } else {
        modeText = 'Français → Translations';
      }
      
      if (this.elements.counter) {
        this.elements.counter.textContent = 'Words in quiz: ' + words.length + ' (' + modeText + ')';
      }
      
      this.showNextCard();
    },

    /**
     * Exit the quiz
     */
    exit: function() {
      // Save practice score before exiting
      VocabApp.savePracticeScore();
      
      if (this.elements.container) {
        this.elements.container.style.display = 'none';
      }
      if (this.elements.header) {
        this.elements.header.style.display = 'none';
      }
      if (this.elements.mainControls) {
        this.elements.mainControls.style.display = 'block';
      }
      if (this.elements.grid) {
        this.elements.grid.style.display = 'grid';
      }
    },

    /**
     * Show the next quiz card
     */
    showNextCard: function() {
      const self = this;
      const words = window.currentWords || [];
      
      if (words.length === 0) return;
      
      const randomWord = words[Math.floor(Math.random() * words.length)];
      this.currentWord = randomWord;
      this.state = 'showing-options';
      this.selectedOptionId = null;
      
      // Update global state
      window.currentQuizWord = randomWord;
      
      // Fetch quiz options from backend
      fetch('/quiz/options', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({word_id: randomWord.id})
      })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.error) {
          console.error(data.error);
          return;
        }
        
        self.currentOptions = data;
        window.currentQuizOptions = data;
        
        // Display word on card
        self.renderCard(randomWord, data.options);
      })
      .catch(function(err) {
        console.error('Error fetching quiz options:', err);
      });
    },

    /**
     * Render the quiz card
     * @param {Object} word - The word to display
     * @param {Array} options - The answer options
     */
    renderCard: function(word, options) {
      const self = this;
      const mode = this.mode;
      
      // Display word on card (based on quiz mode)
      let wordText, speakerLang;
      if (mode === 'chinese') {
        wordText = word.pinyin;
        speakerLang = 'playChinese';
      } else if (mode === 'japanese') {
        wordText = word.japanese_romaji || word.japanese_kanji || '';
        speakerLang = 'playJapanese';
      } else {
        wordText = word.french;
        speakerLang = 'playFrench';
      }
      
      const wordEsc = (wordText || '').replace(/'/g, "\\'");
      
      if (this.elements.card) {
        this.elements.card.innerHTML = 
          '<div style="font-size:2.6em; margin-bottom:20px; line-height:1.2;">' + (wordText || '') + '</div>' +
          '<button style="background:none; border:none; cursor:pointer; font-size:2.2em; padding:0; line-height:1;" onclick="event.stopPropagation(); ' + speakerLang + '(\'' + wordEsc + '\')">🔊</button>';
      }
      
      // Auto-play word
      if (mode === 'chinese' && typeof playChinese === 'function') {
        playChinese(word.hanzi);
      } else if (mode === 'japanese' && typeof playJapanese === 'function') {
        playJapanese(word.japanese_kanji || word.japanese_romaji);
      } else if (typeof playFrench === 'function') {
        playFrench(word.french);
      }
      
      // Display answer options
      this.renderOptions(options);
      
      // Show options container, hide result
      if (this.elements.optionsContainer) {
        this.elements.optionsContainer.style.display = 'block';
      }
      if (this.elements.resultFeedback) {
        this.elements.resultFeedback.style.display = 'none';
      }
      if (this.elements.validateBtn) {
        this.elements.validateBtn.disabled = true;
        this.elements.validateBtn.style.display = 'inline-block';
      }
      if (this.elements.nextBtn) {
        this.elements.nextBtn.style.display = 'none';
      }
    },

    /**
     * Render quiz options
     * @param {Array} options - The answer options
     */
    renderOptions: function(options) {
      const self = this;
      const mode = this.mode;
      
      if (!this.elements.options) return;
      
      this.elements.options.innerHTML = '';
      
      options.forEach(function(opt) {
        const btn = document.createElement('button');
        btn.className = 'quiz-option-btn';

        // Choose display text depending on quiz mode
        let topText = '';
        let bottomText = '';
        if (mode === 'french') {
          topText = opt.english || '';
          bottomText = '';
        } else if (mode === 'japanese') {
          topText = opt.english || '';
          bottomText = '';
        } else {
          topText = '';
          bottomText = opt.hanzi || '';
        }

        btn.innerHTML = '<div class="option-top">' + topText + '</div>' +
                        '<div class="option-hanzi">' + bottomText + '</div>';

        btn.style.cssText = 
          'padding: 12px;' +
          'border: 2px solid var(--border-color);' +
          'background: var(--card-bg);' +
          'border-radius: 8px;' +
          'cursor: pointer;' +
          'transition: all 0.3s;' +
          'display: flex;' +
          'flex-direction: column;' +
          'align-items: center;' +
          'justify-content: center;' +
          'text-align: center;' +
          'min-height: 110px;';

        btn.onclick = function() {
          self.selectOption(opt.id, btn, opt);
        };

        self.elements.options.appendChild(btn);
      });
    },

    /**
     * Select a quiz option
     * @param {number} optionId - The option ID
     * @param {HTMLElement} btnElement - The clicked button
     * @param {Object} optionData - The option data
     */
    selectOption: function(optionId, btnElement, optionData) {
      const mode = this.mode;
      
      // Deselect previous
      if (this.selectedOptionId !== null) {
        document.querySelectorAll('.quiz-option-btn').forEach(function(b) {
          b.style.background = 'var(--card-bg)';
          b.style.borderColor = 'var(--border-color)';
        });
      }
      
      this.selectedOptionId = optionId;
      window.selectedOptionId = optionId;
      
      // Highlight selected (green)
      btnElement.style.background = '#51cf66';
      btnElement.style.borderColor = '#40c057';
      btnElement.style.color = 'white';
      
      // Play selected word
      if (mode === 'chinese' && typeof playChinese === 'function') {
        playChinese(optionData.hanzi || optionData.pinyin);
      } else if (typeof playFrench === 'function') {
        playFrench(optionData.french);
      }
      
      // Enable validate button
      if (this.elements.validateBtn) {
        this.elements.validateBtn.disabled = false;
      }
    },

    /**
     * Validate the selected answer
     */
    validateAnswer: function() {
      const self = this;
      
      if (this.selectedOptionId === null) return;
      
      // Get the selected option for tracking
      const selectedOption = this.currentOptions.options.find(function(o) {
        return o.id === self.selectedOptionId;
      });
      
      fetch('/quiz/check', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          correct_id: this.currentOptions.correct_id,
          selected_id: this.selectedOptionId
        })
      })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.error) {
          console.error(data.error);
          return;
        }
        
        const isCorrect = data.correct;
        const explanation = data.explanation || 'Well done!';
        const correctWord = self.currentOptions.correct_word;
        
        // Track session stats
        VocabApp.session.total++;
        
        // Track detailed result
        VocabApp.addSessionResult({
          vocabulary_id: correctWord.id,
          word_hanzi: correctWord.hanzi || '',
          word_pinyin: correctWord.pinyin || '',
          word_english: correctWord.english || '',
          word_french: correctWord.french || '',
          question_type: self.mode === 'chinese' ? 'chinese_to_meaning' : 'french_to_meaning',
          question_text: self.mode === 'chinese' ? correctWord.pinyin : correctWord.french,
          user_answer: selectedOption ? (self.mode === 'chinese' ? selectedOption.hanzi : selectedOption.english) : '',
          correct_answer: self.mode === 'chinese' ? correctWord.hanzi : correctWord.english,
          is_correct: isCorrect
        });
        
        // Show result
        if (self.elements.optionsContainer) {
          self.elements.optionsContainer.style.display = 'none';
        }
        if (self.elements.resultFeedback) {
          self.elements.resultFeedback.style.display = 'block';
        }
        
        if (isCorrect) {
          if (self.elements.resultStatus) {
            self.elements.resultStatus.innerHTML = '✅ Correct!';
            self.elements.resultStatus.style.color = '#51cf66';
          }
          self.addWin();
          VocabApp.session.score++;
        } else {
          if (self.elements.resultStatus) {
            self.elements.resultStatus.innerHTML = '❌ Incorrect';
            self.elements.resultStatus.style.color = '#ff6b6b';
          }
          self.resetWins();
        }
        
        // Render explanation with sentences
        self.renderExplanation(correctWord, explanation);
        
        self.state = 'showing-result';
        window.currentQuizState = 'showing-result';
      })
      .catch(function(err) {
        console.error('Error validating answer:', err);
      });
    },

    /**
     * Render the result explanation
     * @param {Object} correctWord - The correct word
     * @param {string} explanation - The explanation text
     */
    renderExplanation: function(correctWord, explanation) {
      if (!this.elements.resultExplanation) return;
      
      const sentenceEnglish = correctWord.sent_english || '';
      const langSettings = VocabApp.langSettings;
      
      // Build sentence display for all enabled languages
      let sentenceLines = [];
      
      // Chinese sentence (if enabled)
      if (langSettings.chinese && correctWord.sent_hanzi) {
        const hanziText = correctWord.sent_hanzi.replace(/'/g, "\\'");
        sentenceLines.push('<div style="margin-bottom:8px;">' +
          '<button style="background:none; border:none; cursor:pointer; font-size:1.3em; padding:0; margin-right:8px; line-height:1;" onclick="event.stopPropagation(); VocabApp.speak(\'' + hanziText + '\', \'zh-CN\');">🇨🇳</button>' +
          '<span style="font-size:0.95em; color:var(--text-muted);">' + correctWord.sent_hanzi + '</span>' +
        '</div>');
        if (correctWord.sent_pinyin) {
          sentenceLines.push('<div style="font-size:0.9em; color:var(--text-muted); margin-left:38px; margin-top:4px;">' + correctWord.sent_pinyin + '</div>');
        }
      }
      
      // Japanese sentence (if enabled)
      if (langSettings.japanese && correctWord.sent_japanese_kanji) {
        const jpText = correctWord.sent_japanese_kanji.replace(/'/g, "\\'");
        sentenceLines.push('<div style="margin-bottom:8px; margin-top:10px;">' +
          '<button style="background:none; border:none; cursor:pointer; font-size:1.3em; padding:0; margin-right:8px; line-height:1;" onclick="event.stopPropagation(); VocabApp.speak(\'' + jpText + '\', \'ja-JP\');">🇯🇵</button>' +
          '<span style="font-size:0.95em; color:var(--text-muted);">' + correctWord.sent_japanese_kanji + '</span>' +
        '</div>');
        if (correctWord.sent_japanese_romaji) {
          sentenceLines.push('<div style="font-size:0.9em; color:var(--text-muted); margin-left:38px; margin-top:4px;">' + correctWord.sent_japanese_romaji + '</div>');
        }
      }
      
      // French sentence (if enabled)
      if (langSettings.french && correctWord.sent_french) {
        const frText = correctWord.sent_french.replace(/'/g, "\\'");
        sentenceLines.push('<div style="margin-bottom:8px; margin-top:10px;">' +
          '<button style="background:none; border:none; cursor:pointer; font-size:1.3em; padding:0; margin-right:8px; line-height:1;" onclick="event.stopPropagation(); VocabApp.speak(\'' + frText + '\', \'fr-FR\');">🇫🇷</button>' +
          '<span style="font-size:0.95em; color:var(--text-muted);">' + correctWord.sent_french + '</span>' +
        '</div>');
      }
      
      // English translation (always shown if available)
      if (sentenceEnglish) {
        sentenceLines.push('<div style="font-size:0.9em; color:var(--text-muted); font-style:italic; margin-left:38px; margin-top:8px;">' + sentenceEnglish + '</div>');
      }
      
      let sentenceDisplay = '';
      if (sentenceLines.length > 0) {
        sentenceDisplay = '<div style="margin-top:15px; padding-top:15px; border-top:1px solid var(--border-color);">' +
          sentenceLines.join('') +
        '</div>';
      }
      
      this.elements.resultExplanation.innerHTML = '<strong>Explanation:</strong> ' + explanation + sentenceDisplay;
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      WordsQuiz.init();
    });
  } else {
    WordsQuiz.init();
  }

  // Expose to VocabApp namespace
  window.VocabApp = window.VocabApp || {};
  window.VocabApp.WordsQuiz = WordsQuiz;

  // Global functions for backward compatibility
  window.startQuiz = function(mode) {
    WordsQuiz.start(mode, window.currentWords);
  };
  
  window.exitQuiz = function() {
    WordsQuiz.exit();
  };
  
  window.showRandomCard = function() {
    WordsQuiz.showNextCard();
  };
  
  window.selectQuizOption = function(optionId, btnElement, optionData) {
    WordsQuiz.selectOption(optionId, btnElement, optionData);
  };
  
  window.validateQuizAnswer = function() {
    WordsQuiz.validateAnswer();
  };
  
  window.addQuizWin = function() {
    VocabApp.session.score++;
    WordsQuiz.addWin();
  };
  
  window.addQuizAttempt = function() {
    VocabApp.session.total++;
  };
  
  window.resetQuizWins = function() {
    WordsQuiz.resetWins();
  };
  
  window.loadQuizWins = function() {
    WordsQuiz.loadWins();
  };
  
  window.showTrophy = function() {
    WordsQuiz.showTrophy();
  };

})();
