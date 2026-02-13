/**
 * Drawing Practice Game Module
 * Practice writing Chinese characters stroke by stroke using HanziWriter
 */

(function() {
  'use strict';

  const DrawingGame = {
    // State
    words: [],
    currentIndex: 0,
    score: 0,
    total: 0,
    currentWord: null,
    characters: [],
    currentCharIndex: 0,
    charMistakes: 0,
    currentWriter: null,

    // DOM elements (cached on init)
    elements: {},

    /**
     * Initialize the Drawing game
     */
    init: function() {
      this.cacheElements();
      this.bindEvents();
    },

    /**
     * Cache DOM elements for performance
     */
    cacheElements: function() {
      this.elements = {
        modal: document.getElementById('practiceDrawingModal'),
        section: document.getElementById('pd_section'),
        count: document.getElementById('pd_count'),
        configSection: document.getElementById('drawingConfigSection'),
        practiceSection: document.getElementById('drawingPracticeSection'),
        canvasContainer: document.getElementById('drawingCanvasContainer'),
        english: document.getElementById('drawingEnglish'),
        pinyin: document.getElementById('drawingPinyin'),
        current: document.getElementById('drawingCurrent'),
        total: document.getElementById('drawingTotal'),
        score: document.getElementById('drawingScore'),
        charCurrent: document.getElementById('drawingCharCurrent'),
        charTotal: document.getElementById('drawingCharTotal'),
        startBtn: document.getElementById('startPracticeDrawing'),
        skipBtn: document.getElementById('drawingSkipBtn'),
        exitBtn: document.getElementById('drawingExitBtn')
      };
    },

    /**
     * Bind event listeners
     */
    bindEvents: function() {
      const self = this;
      
      if (this.elements.startBtn) {
        this.elements.startBtn.addEventListener('click', function() {
          self.start();
        });
      }
      
      if (this.elements.skipBtn) {
        this.elements.skipBtn.addEventListener('click', function() {
          self.skipWord();
        });
      }
      
      if (this.elements.exitBtn) {
        this.elements.exitBtn.addEventListener('click', function() {
          self.close();
        });
      }
    },

    /**
     * Open the Drawing practice modal
     */
    open: function() {
      this.reset();
      
      // Populate categories from main sectionSelect
      const mainSection = document.getElementById('sectionSelect');
      if (this.elements.section && mainSection) {
        this.elements.section.innerHTML = '<option value="all">All Categories</option>';
        const options = Array.from(mainSection.options).slice(1);
        options.forEach(function(opt) {
          const newOpt = document.createElement('option');
          newOpt.value = opt.value;
          newOpt.textContent = opt.textContent;
          this.elements.section.appendChild(newOpt);
        }, this);
      }
      
      if (this.elements.modal) {
        this.elements.modal.style.display = 'flex';
      }
    },

    /**
     * Close the Drawing practice modal
     */
    close: function() {
      // Save score if there are any attempts before closing (but not if already at completion)
      if (this.total > 0 && this.currentIndex < this.words.length) {
        VocabApp.session.score = this.score;
        VocabApp.session.total = this.total;
        VocabApp.savePracticeScore();
      }
      
      if (this.elements.modal) {
        this.elements.modal.style.display = 'none';
      }
      this.reset();
    },

    /**
     * Reset the game state
     */
    reset: function() {
      this.words = [];
      this.currentIndex = 0;
      this.score = 0;
      this.total = 0;
      this.currentWord = null;
      this.characters = [];
      this.currentCharIndex = 0;
      this.charMistakes = 0;
      this.currentWriter = null;
      
      if (this.elements.configSection) {
        this.elements.configSection.style.display = 'block';
      }
      if (this.elements.practiceSection) {
        this.elements.practiceSection.style.display = 'none';
      }
      if (this.elements.canvasContainer) {
        this.elements.canvasContainer.innerHTML = '';
      }
    },

    /**
     * Start the Drawing practice game
     */
    start: async function() {
      const section = this.elements.section ? this.elements.section.value : 'all';
      const count = this.elements.count ? parseInt(this.elements.count.value) : 10;

      // Start unified practice session tracking
      VocabApp.startPracticeSession('drawing');
      this.score = 0;
      this.total = 0;

      try {
        const response = await fetch(`/random_words?section=${encodeURIComponent(section)}&limit=${count}`);
        if (!response.ok) throw new Error('Failed to fetch words');
        const words = await response.json();

        // Filter to only words with hanzi characters
        const validWords = words.filter(function(w) {
          return w.hanzi && w.hanzi.trim().length > 0;
        });

        if (!validWords || validWords.length === 0) {
          VocabApp.showToast('No Chinese words found for this category', 'error');
          return;
        }

        this.words = validWords;
        this.currentIndex = 0;

        if (this.elements.configSection) {
          this.elements.configSection.style.display = 'none';
        }
        if (this.elements.practiceSection) {
          this.elements.practiceSection.style.display = 'block';
        }
        
        this.showNextWord();
      } catch (err) {
        console.error('Error starting drawing practice:', err);
        VocabApp.showToast('Error loading words. Please try again.', 'error');
      }
    },

    /**
     * Show the next word to practice
     */
    showNextWord: function() {
      if (this.currentIndex >= this.words.length) {
        this.showCompletion();
        return;
      }

      const word = this.words[this.currentIndex];
      this.currentWord = word;
      this.characters = word.hanzi.split('');
      this.currentCharIndex = 0;
      
      // Update UI
      if (this.elements.english) {
        this.elements.english.textContent = word.english || '';
      }
      if (this.elements.pinyin) {
        this.elements.pinyin.textContent = word.pinyin || '';
      }
      if (this.elements.current) {
        this.elements.current.textContent = this.currentIndex + 1;
      }
      if (this.elements.total) {
        this.elements.total.textContent = this.words.length;
      }
      if (this.elements.score) {
        this.elements.score.textContent = this.score;
      }
      if (this.elements.charTotal) {
        this.elements.charTotal.textContent = this.characters.length;
      }
      
      // Show first character
      this.showCharacter(0);
    },

    /**
     * Show a specific character for drawing practice
     * @param {number} charIndex - Index of character in current word
     */
    showCharacter: function(charIndex) {
      const self = this;
      const characters = this.characters;
      
      if (charIndex >= characters.length) {
        // Word complete, move to next word
        this.currentIndex++;
        setTimeout(function() {
          self.showNextWord();
        }, 500);
        return;
      }

      this.currentCharIndex = charIndex;
      this.charMistakes = 0;
      
      // Update character progress
      if (this.elements.charCurrent) {
        this.elements.charCurrent.textContent = charIndex + 1;
      }
      
      if (!this.elements.canvasContainer) return;
      
      this.elements.canvasContainer.innerHTML = '';
      
      const char = characters[charIndex];
      const charDiv = document.createElement('div');
      charDiv.style.cssText = 'width:250px; height:250px; border:2px solid var(--border-color); border-radius:12px; background:white;';
      charDiv.id = 'drawChar_current';
      this.elements.canvasContainer.appendChild(charDiv);

      const writer = HanziWriter.create(charDiv, char, {
        width: 250,
        height: 250,
        padding: 10,
        showOutline: true,
        strokeAnimationSpeed: 1,
        delayBetweenStrokes: 100,
        showCharacter: false,
        showHintAfterMisses: 3,
        onLoadCharDataSuccess: function() {
          // Start quiz once character is loaded
          self.total++;
          VocabApp.session.total = self.total;
          
          writer.quiz({
            showHintAfterMisses: 3,
            onMistake: function() {
              self.charMistakes++;
            },
            onComplete: function() {
              const isCorrect = self.charMistakes <= 1;
              if (isCorrect) {
                self.score++;
                VocabApp.session.score = self.score;
              }
              
              // Update score display
              if (self.elements.score) {
                self.elements.score.textContent = self.score;
              }
              
              // Move to next character
              setTimeout(function() {
                self.showCharacter(charIndex + 1);
              }, 400);
            }
          });
        },
        onLoadCharDataError: function() {
          console.error('Failed to load character:', char);
          // Skip this character
          setTimeout(function() {
            self.showCharacter(charIndex + 1);
          }, 400);
        }
      });
      
      this.currentWriter = writer;
    },

    /**
     * Skip the current word
     */
    skipWord: function() {
      // Mark remaining characters as skipped
      if (this.currentWord) {
        const characters = this.characters;
        for (let i = this.currentCharIndex; i < characters.length; i++) {
          this.total++;
        }
        VocabApp.session.total = this.total;
      }
      
      this.currentIndex++;
      this.showNextWord();
    },

    /**
     * Show completion screen
     */
    showCompletion: function() {
      const score = this.score;
      const total = this.total;
      const pct = total > 0 ? Math.round((score / total) * 100) : 0;
      const self = this;
      
      // Save score
      VocabApp.session.score = score;
      VocabApp.session.total = total;
      VocabApp.savePracticeScore();

      if (this.elements.canvasContainer) {
        this.elements.canvasContainer.innerHTML = `
          <div style="text-align:center; padding:30px; width:100%;">
            <h3 style="color:var(--primary); margin-bottom:10px;">🎉 Practice Complete!</h3>
            <p style="font-size:1.2em;">Score: <strong>${score}/${total}</strong> (${pct}%)</p>
            <button class="primary" id="drawingPlayAgainBtn" style="margin-top:15px; padding:12px 24px;">Play Again</button>
          </div>
        `;
        
        // Bind play again button
        const playAgainBtn = document.getElementById('drawingPlayAgainBtn');
        if (playAgainBtn) {
          playAgainBtn.addEventListener('click', function() {
            self.reset();
          });
        }
      }
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      DrawingGame.init();
    });
  } else {
    DrawingGame.init();
  }

  // Expose to VocabApp namespace
  window.VocabApp = window.VocabApp || {};
  window.VocabApp.DrawingGame = DrawingGame;

  // Global function for backward compatibility (used by HTML onclick)
  window.openPracticeDrawingModal = function() {
    DrawingGame.open();
  };

})();
