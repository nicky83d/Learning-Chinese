/**
 * Listening Practice Game Module
 * Practice identifying words by listening to audio
 */

(function() {
  'use strict';

  const ListeningGame = {
    // State
    words: [],
    currentIndex: 0,
    score: 0,
    total: 0,
    language: 'chinese',
    currentWord: null,
    answered: false,

    // DOM elements (cached on init)
    elements: {},

    /**
     * Initialize the Listening game
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
        modal: document.getElementById('practiceModal'),
        section: document.getElementById('pl_section'),
        count: document.getElementById('pl_count'),
        configSection: document.getElementById('listeningConfigSection'),
        practiceSection: document.getElementById('listeningPracticeSection'),
        current: document.getElementById('listeningCurrent'),
        total: document.getElementById('listeningTotal'),
        score: document.getElementById('listeningScore'),
        options: document.getElementById('listeningOptions'),
        feedback: document.getElementById('listeningFeedback'),
        nextBtn: document.getElementById('listeningNextBtn'),
        playBtn: document.getElementById('listeningPlayBtn'),
        startBtn: document.getElementById('startPracticeListening'),
        langChinese: document.getElementById('pl_lang_chinese'),
        langJapanese: document.getElementById('pl_lang_japanese'),
        langFrench: document.getElementById('pl_lang_french')
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
      
      if (this.elements.nextBtn) {
        this.elements.nextBtn.addEventListener('click', function() {
          self.nextWord();
        });
      }
      
      if (this.elements.playBtn) {
        this.elements.playBtn.addEventListener('click', function() {
          self.playAudio();
        });
      }
    },

    /**
     * Open the Listening practice modal
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
      
      // Update language options visibility based on settings
      const langSettings = VocabApp.langSettings;
      if (this.elements.langChinese) {
        this.elements.langChinese.style.display = langSettings.chinese ? 'flex' : 'none';
      }
      if (this.elements.langJapanese) {
        this.elements.langJapanese.style.display = langSettings.japanese ? 'flex' : 'none';
      }
      if (this.elements.langFrench) {
        this.elements.langFrench.style.display = langSettings.french ? 'flex' : 'none';
      }
      
      // Ensure a valid language is selected
      const chineseRadio = document.querySelector('#pl_lang_chinese input');
      const japaneseRadio = document.querySelector('#pl_lang_japanese input');
      const frenchRadio = document.querySelector('#pl_lang_french input');
      
      if (chineseRadio) chineseRadio.checked = false;
      if (japaneseRadio) japaneseRadio.checked = false;
      if (frenchRadio) frenchRadio.checked = false;
      
      // Select the first available language
      if (langSettings.chinese && chineseRadio) {
        chineseRadio.checked = true;
      } else if (langSettings.japanese && japaneseRadio) {
        japaneseRadio.checked = true;
      } else if (langSettings.french && frenchRadio) {
        frenchRadio.checked = true;
      }
      
      if (this.elements.modal) {
        this.elements.modal.style.display = 'flex';
      }
    },

    /**
     * Close the Listening practice modal
     */
    close: function() {
      // Save score if there are any attempts before closing (but not if at completion)
      if (this.total > 0 && this.currentIndex < this.words.length) {
        VocabApp.session.score = this.score;
        VocabApp.session.total = this.total;
        VocabApp.savePracticeScore();
      }
      
      if (this.elements.modal) {
        this.elements.modal.style.display = 'none';
      }
      window.speechSynthesis.cancel();
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
      this.answered = false;
      
      if (this.elements.configSection) {
        this.elements.configSection.style.display = 'block';
      }
      if (this.elements.practiceSection) {
        this.elements.practiceSection.style.display = 'none';
      }
    },

    /**
     * Start the Listening practice game
     */
    start: async function() {
      const langRadio = document.querySelector('input[name="pl_lang"]:checked');
      const lang = langRadio ? langRadio.value : 'chinese';
      const section = this.elements.section ? this.elements.section.value : 'all';
      const count = this.elements.count ? parseInt(this.elements.count.value) : 10;

      // Start unified practice session tracking
      VocabApp.startPracticeSession('listening');
      this.language = lang;
      this.score = 0;
      this.total = 0;

      try {
        const response = await fetch(`/random_words?section=${encodeURIComponent(section)}&limit=${count}`);
        if (!response.ok) throw new Error('Failed to fetch words');
        const words = await response.json();

        if (!words || words.length === 0) {
          VocabApp.showToast('No words found for this category', 'error');
          return;
        }

        this.words = words;
        this.currentIndex = 0;

        if (this.elements.configSection) {
          this.elements.configSection.style.display = 'none';
        }
        if (this.elements.practiceSection) {
          this.elements.practiceSection.style.display = 'block';
        }
        
        this.showNextWord();
      } catch (err) {
        console.error('Error starting listening practice:', err);
        VocabApp.showToast('Error loading words. Please try again.', 'error');
      }
    },

    /**
     * Show the next word for listening practice
     */
    showNextWord: function() {
      const self = this;
      
      if (this.currentIndex >= this.words.length) {
        this.showCompletion();
        return;
      }

      this.answered = false;
      const word = this.words[this.currentIndex];
      this.currentWord = word;

      // Generate 3 random wrong options from the quiz word set
      const wrongOptions = this.words
        .filter(function(v) { return v.english && v.english !== word.english; })
        .sort(function() { return Math.random() - 0.5; })
        .slice(0, 3)
        .map(function(v) { return v.english; });

      // Add correct answer and shuffle
      const options = wrongOptions.concat([word.english]).sort(function() { return Math.random() - 0.5; });

      // Update UI
      if (this.elements.current) {
        this.elements.current.textContent = this.currentIndex + 1;
      }
      if (this.elements.total) {
        this.elements.total.textContent = this.words.length;
      }
      if (this.elements.score) {
        this.elements.score.textContent = this.score;
      }
      if (this.elements.feedback) {
        this.elements.feedback.style.display = 'none';
      }
      if (this.elements.nextBtn) {
        this.elements.nextBtn.style.display = 'none';
      }

      // Create option buttons
      if (this.elements.options) {
        this.elements.options.innerHTML = options.map(function(opt, i) {
          const escapedOpt = opt.replace(/'/g, "\\'");
          return '<button class="listening-option secondary" data-option="' + escapedOpt + '" style="padding:12px; text-align:left; font-size:1em;">' +
            String.fromCharCode(65 + i) + '. ' + opt +
          '</button>';
        }).join('');
        
        // Bind click events
        const buttons = this.elements.options.querySelectorAll('.listening-option');
        buttons.forEach(function(btn) {
          btn.addEventListener('click', function() {
            self.selectOption(this, this.dataset.option);
          });
        });
      }

      // Auto-play the audio after a brief delay
      setTimeout(function() {
        self.playAudio();
      }, 300);
    },

    /**
     * Play audio for the current word
     */
    playAudio: function() {
      const word = this.currentWord;
      if (!word) return;

      const lang = this.language;
      let targetWord, langCode;
      
      if (lang === 'chinese') {
        targetWord = word.hanzi;
        langCode = 'zh-CN';
      } else if (lang === 'japanese') {
        targetWord = word.japanese_kanji || word.japanese_romaji;
        langCode = 'ja-JP';
      } else {
        targetWord = word.french;
        langCode = 'fr-FR';
      }
      
      VocabApp.speak(targetWord, langCode);
    },

    /**
     * Handle option selection
     * @param {HTMLElement} btn - The clicked button
     * @param {string} selected - The selected answer
     */
    selectOption: function(btn, selected) {
      if (this.answered) return;
      this.answered = true;

      const word = this.currentWord;
      const correct = word.english;
      const isCorrect = selected === correct;

      this.total++;
      if (isCorrect) this.score++;

      // Update session tracking
      VocabApp.session.total = this.total;
      VocabApp.session.score = this.score;

      // Track detailed result
      const lang = this.language;
      let targetWord;
      if (lang === 'chinese') {
        targetWord = word.hanzi;
      } else if (lang === 'japanese') {
        targetWord = word.japanese_kanji || word.japanese_romaji;
      } else {
        targetWord = word.french;
      }
      
      VocabApp.addSessionResult({
        vocabulary_id: word.id,
        word_hanzi: word.hanzi || '',
        word_pinyin: word.pinyin || '',
        word_english: word.english || '',
        word_french: word.french || '',
        question_type: 'listening',
        question_text: 'Identify: "' + targetWord + '"',
        user_answer: selected,
        correct_answer: correct,
        is_correct: isCorrect
      });

      // Mark all buttons
      const buttons = document.querySelectorAll('.listening-option');
      buttons.forEach(function(b) {
        const optText = b.textContent.substring(3).trim(); // Remove "A. " prefix
        if (optText === correct) {
          b.style.background = 'var(--success)';
          b.style.color = 'white';
        } else if (b === btn && !isCorrect) {
          b.style.background = 'var(--danger)';
          b.style.color = 'white';
        }
        b.disabled = true;
      });

      // Show feedback
      if (this.elements.feedback) {
        let display;
        if (lang === 'chinese') {
          display = word.hanzi + ' (' + (word.pinyin || '') + ')';
        } else if (lang === 'japanese') {
          display = (word.japanese_kanji || '') + ' (' + (word.japanese_romaji || '') + ')';
        } else {
          display = word.french;
        }
        
        if (isCorrect) {
          this.elements.feedback.innerHTML = '✅ Correct! <strong>' + display + '</strong> = ' + correct;
          this.elements.feedback.style.background = 'rgba(76, 175, 80, 0.2)';
        } else {
          this.elements.feedback.innerHTML = '❌ Wrong! <strong>' + display + '</strong> = ' + correct;
          this.elements.feedback.style.background = 'rgba(244, 67, 54, 0.2)';
        }
        this.elements.feedback.style.display = 'block';
      }

      // Update score display
      if (this.elements.score) {
        this.elements.score.textContent = this.score;
      }

      // Show next button
      if (this.elements.nextBtn) {
        this.elements.nextBtn.style.display = 'inline-block';
      }
    },

    /**
     * Move to the next word
     */
    nextWord: function() {
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

      if (this.elements.options) {
        this.elements.options.innerHTML = 
          '<div style="text-align:center; padding:20px;">' +
            '<h3 style="color:var(--primary); margin-bottom:10px;">🎉 Practice Complete!</h3>' +
            '<p style="font-size:1.2em;">Score: <strong>' + score + '/' + total + '</strong> (' + pct + '%)</p>' +
            '<button class="primary" id="listeningPlayAgainBtn" style="margin-top:15px; padding:12px 24px;">Play Again</button>' +
          '</div>';
        
        // Bind play again button
        const playAgainBtn = document.getElementById('listeningPlayAgainBtn');
        if (playAgainBtn) {
          playAgainBtn.addEventListener('click', function() {
            self.reset();
          });
        }
      }
      
      if (this.elements.feedback) {
        this.elements.feedback.style.display = 'none';
      }
      if (this.elements.nextBtn) {
        this.elements.nextBtn.style.display = 'none';
      }
      if (this.elements.playBtn) {
        this.elements.playBtn.style.display = 'none';
      }
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      ListeningGame.init();
    });
  } else {
    ListeningGame.init();
  }

  // Expose to VocabApp namespace
  window.VocabApp = window.VocabApp || {};
  window.VocabApp.ListeningGame = ListeningGame;

  // Global functions for backward compatibility
  window.openPracticeListeningModal = function() {
    ListeningGame.open();
  };
  
  window.closePracticeModal = function() {
    ListeningGame.close();
  };
  
  window.selectListeningOption = function(btn, selected) {
    ListeningGame.selectOption(btn, selected);
  };
  
  window.nextListeningWord = function() {
    ListeningGame.nextWord();
  };
  
  window.playListeningAudio = function() {
    ListeningGame.playAudio();
  };
  
  window.resetListeningPractice = function() {
    ListeningGame.reset();
  };

})();
