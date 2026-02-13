/**
 * Speaking Practice Game Module
 * Practice pronunciation with speech recognition
 */

(function() {
  'use strict';

  const SpeakingGame = {
    // State
    words: [],
    currentIndex: 0,
    score: 0,
    total: 0,
    language: 'chinese',
    mode: 'words',
    recognition: null,
    mediaRecorder: null,
    isRecording: false,

    // DOM elements (cached on init)
    elements: {},

    /**
     * Initialize the Speaking game
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
        modal: document.getElementById('practiceTalkingModal'),
        section: document.getElementById('pt_section'),
        count: document.getElementById('pt_count'),
        configSection: document.getElementById('talkingConfigSection'),
        practiceSection: document.getElementById('talkingPracticeSection'),
        targetText: document.getElementById('talkingTargetText'),
        pinyinText: document.getElementById('talkingPinyinText'),
        englishText: document.getElementById('talkingEnglishText'),
        score: document.getElementById('talkingScore'),
        total: document.getElementById('talkingTotal'),
        feedback: document.getElementById('talkingFeedback'),
        feedbackText: document.getElementById('talkingFeedbackText'),
        recognizedText: document.getElementById('talkingRecognizedText'),
        recordBtn: document.getElementById('talkingRecordBtn'),
        playBtn: document.getElementById('talkingPlayBtn'),
        skipBtn: document.getElementById('talkingSkipBtn'),
        exitBtn: document.getElementById('talkingExitBtn'),
        startBtn: document.getElementById('startPracticeTalking'),
        langChinese: document.getElementById('pt_lang_chinese'),
        langJapanese: document.getElementById('pt_lang_japanese'),
        langFrench: document.getElementById('pt_lang_french')
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
      
      if (this.elements.playBtn) {
        this.elements.playBtn.addEventListener('click', function() {
          self.playCurrentWord();
        });
      }
      
      if (this.elements.recordBtn) {
        this.elements.recordBtn.addEventListener('click', function() {
          self.startRecording();
        });
      }
      
      if (this.elements.skipBtn) {
        this.elements.skipBtn.addEventListener('click', function() {
          self.skipCurrentWord();
        });
      }
      
      if (this.elements.exitBtn) {
        this.elements.exitBtn.addEventListener('click', function() {
          self.close();
        });
      }
    },

    /**
     * Open the Speaking practice modal
     */
    open: function() {
      if (this.elements.modal) {
        this.elements.modal.style.display = 'flex';
      }
      if (this.elements.configSection) {
        this.elements.configSection.style.display = 'block';
      }
      if (this.elements.practiceSection) {
        this.elements.practiceSection.style.display = 'none';
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
      const chineseRadio = document.querySelector('#pt_lang_chinese input');
      const japaneseRadio = document.querySelector('#pt_lang_japanese input');
      const frenchRadio = document.querySelector('#pt_lang_french input');
      
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
      
      // Populate categories
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
    },

    /**
     * Close the Speaking practice modal
     */
    close: function() {
      // Only save if we have attempts AND not at completion
      if (this.total > 0 && this.currentIndex < this.words.length) {
        VocabApp.session.score = this.score;
        VocabApp.session.total = this.total;
        VocabApp.savePracticeScore();
      }
      
      if (this.elements.modal) {
        this.elements.modal.style.display = 'none';
      }
      this.stopRecognition();
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
      this.language = 'chinese';
      this.mode = 'words';
      this.recognition = null;
      this.mediaRecorder = null;
      this.isRecording = false;
    },

    /**
     * Stop recording/recognition
     */
    stopRecognition: function() {
      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.stop();
      }
      this.isRecording = false;
      if (this.elements.recordBtn) {
        this.elements.recordBtn.textContent = '🎤 Record';
        this.elements.recordBtn.classList.remove('recording');
      }
    },

    /**
     * Start the Speaking practice game
     */
    start: async function() {
      const langRadio = document.querySelector('input[name="pt_lang"]:checked');
      const modeRadio = document.querySelector('input[name="pt_mode"]:checked');
      const lang = langRadio ? langRadio.value : 'chinese';
      const mode = modeRadio ? modeRadio.value : 'words';
      const section = this.elements.section ? this.elements.section.value : 'all';
      const count = this.elements.count ? parseInt(this.elements.count.value) : 10;

      // Start unified practice session tracking
      VocabApp.startPracticeSession('speaking');

      try {
        const response = await fetch('/random_words?section=' + encodeURIComponent(section) + '&limit=' + count);
        if (!response.ok) throw new Error('Failed to fetch words');
        const words = await response.json();

        if (!words || words.length === 0) {
          VocabApp.showToast('No words found for this category', 'error');
          return;
        }

        this.words = words;
        this.currentIndex = 0;
        this.score = 0;
        this.total = 0;
        this.language = lang;
        this.mode = mode;

        if (this.elements.configSection) {
          this.elements.configSection.style.display = 'none';
        }
        if (this.elements.practiceSection) {
          this.elements.practiceSection.style.display = 'block';
        }
        
        this.showNextWord();
      } catch (err) {
        console.error('Error starting practice:', err);
        VocabApp.showToast('Error loading words. Please try again.', 'error');
      }
    },

    /**
     * Show the next word for speaking practice
     */
    showNextWord: function() {
      if (this.currentIndex >= this.words.length) {
        this.showCompletion();
        return;
      }

      const word = this.words[this.currentIndex];
      const lang = this.language;
      const mode = this.mode;

      // Reset feedback
      if (this.elements.feedback) {
        this.elements.feedback.style.display = 'none';
      }

      // Display the word/sentence
      if (mode === 'words') {
        let targetText, pinyinText;
        if (lang === 'chinese') {
          targetText = word.hanzi;
          pinyinText = word.pinyin;
        } else if (lang === 'japanese') {
          targetText = word.japanese_kanji || '';
          pinyinText = word.japanese_romaji || '';
        } else {
          targetText = word.french;
          pinyinText = '';
        }
        
        if (this.elements.targetText) {
          this.elements.targetText.textContent = targetText;
        }
        if (this.elements.pinyinText) {
          this.elements.pinyinText.textContent = pinyinText;
        }
        if (this.elements.englishText) {
          this.elements.englishText.textContent = word.english;
        }
      } else {
        // Sentences mode
        let targetText, pinyinText;
        if (lang === 'chinese') {
          targetText = word.sent_hanzi;
          pinyinText = word.sent_pinyin;
        } else if (lang === 'japanese') {
          targetText = word.sent_japanese_kanji || '';
          pinyinText = word.sent_japanese_romaji || '';
        } else {
          targetText = word.sent_french;
          pinyinText = '';
        }
        
        if (this.elements.targetText) {
          this.elements.targetText.textContent = targetText || 'No example available';
        }
        if (this.elements.pinyinText) {
          this.elements.pinyinText.textContent = pinyinText;
        }
        if (this.elements.englishText) {
          this.elements.englishText.textContent = word.sent_english || word.english;
        }
      }

      // Update progress
      if (this.elements.score) {
        this.elements.score.textContent = this.score;
      }
      if (this.elements.total) {
        this.elements.total.textContent = this.total;
      }
    },

    /**
     * Play the current word's audio
     */
    playCurrentWord: function() {
      const word = this.words[this.currentIndex];
      if (!word) return;
      
      const lang = this.language;
      const mode = this.mode;
      
      let langCode, textToSpeak;
      if (lang === 'chinese') {
        langCode = 'zh-CN';
        textToSpeak = mode === 'words' ? word.hanzi : word.sent_hanzi;
      } else if (lang === 'japanese') {
        langCode = 'ja-JP';
        textToSpeak = mode === 'words' ? (word.japanese_kanji || word.japanese_romaji) : (word.sent_japanese_kanji || word.sent_japanese_romaji);
      } else {
        langCode = 'fr-FR';
        textToSpeak = mode === 'words' ? word.french : word.sent_french;
      }

      if (textToSpeak) {
        VocabApp.speak(textToSpeak, langCode);
      }
    },

    /**
     * Start recording audio
     */
    startRecording: function() {
      const self = this;
      
      if (this.isRecording) {
        this.stopRecognition();
        return;
      }

      // Server-side recording for better mobile compatibility
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        VocabApp.showToast('Microphone access not supported in this browser', 'error');
        return;
      }

      if (this.elements.recordBtn) {
        this.elements.recordBtn.textContent = '⏹️ Stop';
        this.elements.recordBtn.classList.add('recording');
      }
      this.isRecording = true;

      const word = this.words[this.currentIndex];
      const lang = this.language;
      const mode = this.mode;
      
      let langCode, expectedText;
      if (lang === 'chinese') {
        langCode = 'zh-CN';
        expectedText = mode === 'words' ? word.hanzi : word.sent_hanzi;
      } else if (lang === 'japanese') {
        langCode = 'ja-JP';
        expectedText = mode === 'words' ? (word.japanese_kanji || word.japanese_romaji) : (word.sent_japanese_kanji || word.sent_japanese_romaji);
      } else {
        langCode = 'fr-FR';
        expectedText = mode === 'words' ? word.french : word.sent_french;
      }

      // Start recording audio
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
          const mediaRecorder = new MediaRecorder(stream);
          const audioChunks = [];

          mediaRecorder.ondataavailable = function(event) {
            audioChunks.push(event.data);
          };

          mediaRecorder.onstop = async function() {
            // Stop all tracks
            stream.getTracks().forEach(function(track) { track.stop(); });
            
            // Create audio blob
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            
            // Send to server for transcription
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('expected_text', expectedText);
            formData.append('language_code', langCode);
            formData.append('vocab_id', word.id);

            try {
              const response = await fetch('/transcribe_audio', {
                method: 'POST',
                body: formData
              });

              const result = await response.json();

              if (result.error) {
                VocabApp.showToast('Transcription error: ' + result.error, 'error');
                self.stopRecognition();
                return;
              }

              if (!result.success) {
                self.showFeedback(false, result.recognized || '', 0, result.message);
                self.stopRecognition();
                return;
              }

              // Show feedback
              self.showFeedback(result.is_correct, result.recognized, result.confidence);
              
            } catch (error) {
              console.error('Transcription request failed:', error);
              VocabApp.showToast('Failed to process recording. Please try again.', 'error');
            } finally {
              self.stopRecognition();
            }
          };

          mediaRecorder.start();
          self.mediaRecorder = mediaRecorder;

          // Auto-stop after 5 seconds
          setTimeout(function() {
            if (self.isRecording && mediaRecorder.state === 'recording') {
              mediaRecorder.stop();
            }
          }, 5000);

        })
        .catch(function(error) {
          console.error('Microphone access denied:', error);
          VocabApp.showToast('Microphone access denied. Please allow microphone access.', 'error');
          self.stopRecognition();
        });
    },

    /**
     * Show feedback after recording
     * @param {boolean} isCorrect - Whether the answer was correct
     * @param {string} recognized - The recognized text
     * @param {number} confidence - Confidence score (0-1)
     * @param {string} customMessage - Optional custom message
     */
    showFeedback: function(isCorrect, recognized, confidence, customMessage) {
      const self = this;
      
      // Get current word for result tracking
      const currentWord = this.words[this.currentIndex];
      const lang = this.language;
      const mode = this.mode;
      let expectedText = '';
      if (mode === 'words') {
        expectedText = lang === 'chinese' ? currentWord.hanzi : currentWord.french;
      } else {
        expectedText = lang === 'chinese' ? currentWord.sent_hanzi : currentWord.sent_french;
      }

      if (this.elements.feedback) {
        this.elements.feedback.style.display = 'block';
      }
      
      if (customMessage) {
        if (this.elements.feedback) {
          this.elements.feedback.style.background = 'rgba(255, 193, 7, 0.1)';
          this.elements.feedback.style.border = '2px solid #ffc107';
        }
        if (this.elements.feedbackText) {
          this.elements.feedbackText.innerHTML = '⚠️ ' + customMessage;
          this.elements.feedbackText.style.color = '#ffc107';
        }
        if (this.elements.recognizedText) {
          this.elements.recognizedText.textContent = recognized ? 'You said: "' + recognized + '"' : '';
        }
        this.total++;
        
        // Track quiz attempts (if global functions exist)
        if (typeof addQuizAttempt === 'function') addQuizAttempt();
        
        VocabApp.addSessionResult({
          vocabulary_id: currentWord ? currentWord.id : null,
          word_hanzi: currentWord ? currentWord.hanzi || '' : '',
          word_pinyin: currentWord ? currentWord.pinyin || '' : '',
          word_english: currentWord ? currentWord.english || '' : '',
          word_french: currentWord ? currentWord.french || '' : '',
          question_type: 'speaking_' + mode,
          question_text: expectedText,
          user_answer: recognized || 'No response',
          correct_answer: expectedText,
          is_correct: false
        });
      } else if (isCorrect) {
        if (this.elements.feedback) {
          this.elements.feedback.style.background = 'rgba(40, 167, 69, 0.1)';
          this.elements.feedback.style.border = '2px solid #28a745';
        }
        if (this.elements.feedbackText) {
          this.elements.feedbackText.innerHTML = '✅ <strong>Correct!</strong> Great pronunciation!';
          this.elements.feedbackText.style.color = '#28a745';
        }
        
        this.score++;
        this.total++;
        
        // Track quiz attempts
        if (typeof addQuizAttempt === 'function') addQuizAttempt();
        if (typeof addQuizWin === 'function') addQuizWin();
        
        VocabApp.addSessionResult({
          vocabulary_id: currentWord ? currentWord.id : null,
          word_hanzi: currentWord ? currentWord.hanzi || '' : '',
          word_pinyin: currentWord ? currentWord.pinyin || '' : '',
          word_english: currentWord ? currentWord.english || '' : '',
          word_french: currentWord ? currentWord.french || '' : '',
          question_type: 'speaking_' + mode,
          question_text: expectedText,
          user_answer: recognized || '',
          correct_answer: expectedText,
          is_correct: true
        });
        
        // Auto-advance after 1.5 seconds
        setTimeout(function() {
          self.currentIndex++;
          self.showNextWord();
        }, 1500);
      } else {
        if (this.elements.feedback) {
          this.elements.feedback.style.background = 'rgba(220, 53, 69, 0.1)';
          this.elements.feedback.style.border = '2px solid #dc3545';
        }
        if (this.elements.feedbackText) {
          this.elements.feedbackText.innerHTML = '❌ <strong>Try again!</strong> Listen and repeat.';
          this.elements.feedbackText.style.color = '#dc3545';
        }
        
        this.total++;
        
        // Track quiz attempts
        if (typeof addQuizAttempt === 'function') addQuizAttempt();
        
        VocabApp.addSessionResult({
          vocabulary_id: currentWord ? currentWord.id : null,
          word_hanzi: currentWord ? currentWord.hanzi || '' : '',
          word_pinyin: currentWord ? currentWord.pinyin || '' : '',
          word_english: currentWord ? currentWord.english || '' : '',
          word_french: currentWord ? currentWord.french || '' : '',
          question_type: 'speaking_' + mode,
          question_text: expectedText,
          user_answer: recognized || '',
          correct_answer: expectedText,
          is_correct: false
        });
      }

      if (!customMessage && this.elements.recognizedText) {
        const confidencePercent = Math.round((confidence || 0) * 100);
        this.elements.recognizedText.textContent = 'You said: "' + recognized + '" (' + confidencePercent + '% confidence)';
      }
      
      // Update progress
      if (this.elements.score) {
        this.elements.score.textContent = this.score;
      }
      if (this.elements.total) {
        this.elements.total.textContent = this.total;
      }
    },

    /**
     * Skip the current word
     */
    skipCurrentWord: function() {
      // Get current word for result tracking
      const currentWord = this.words[this.currentIndex];
      const lang = this.language;
      const mode = this.mode;
      let expectedText = '';
      if (mode === 'words') {
        expectedText = lang === 'chinese' ? currentWord.hanzi : currentWord.french;
      } else {
        expectedText = lang === 'chinese' ? currentWord.sent_hanzi : currentWord.sent_french;
      }
      
      this.total++;
      
      // Track quiz attempts
      if (typeof addQuizAttempt === 'function') addQuizAttempt();
      
      VocabApp.addSessionResult({
        vocabulary_id: currentWord ? currentWord.id : null,
        word_hanzi: currentWord ? currentWord.hanzi || '' : '',
        word_pinyin: currentWord ? currentWord.pinyin || '' : '',
        word_english: currentWord ? currentWord.english || '' : '',
        word_french: currentWord ? currentWord.french || '' : '',
        question_type: 'speaking_' + mode,
        question_text: expectedText,
        user_answer: '(skipped)',
        correct_answer: expectedText,
        is_correct: false
      });
      
      this.currentIndex++;
      this.showNextWord();
    },

    /**
     * Show completion screen
     */
    showCompletion: function() {
      const score = this.score;
      const total = this.total;
      const percentage = total > 0 ? Math.round((score / total) * 100) : 0;
      
      // Sync with session tracking before saving
      VocabApp.session.score = score;
      VocabApp.session.total = total;
      
      // Save speaking practice score using unified system
      VocabApp.savePracticeScore();

      if (this.elements.targetText) {
        this.elements.targetText.textContent = '🎉 Practice Complete!';
      }
      if (this.elements.pinyinText) {
        this.elements.pinyinText.textContent = '';
      }
      if (this.elements.englishText) {
        this.elements.englishText.textContent = 'Final Score: ' + score + '/' + total + ' (' + percentage + '%)';
      }
      
      if (this.elements.feedback) {
        this.elements.feedback.style.display = 'block';
        this.elements.feedback.style.background = 'rgba(40, 167, 69, 0.1)';
        this.elements.feedback.style.border = '2px solid #28a745';
      }
      
      if (this.elements.feedbackText) {
        if (percentage >= 80) {
          this.elements.feedbackText.innerHTML = '🌟 <strong>Excellent work!</strong> Your pronunciation is great!';
        } else if (percentage >= 60) {
          this.elements.feedbackText.innerHTML = '👍 <strong>Good job!</strong> Keep practicing!';
        } else {
          this.elements.feedbackText.innerHTML = '💪 <strong>Keep going!</strong> Practice makes perfect!';
        }
        this.elements.feedbackText.style.color = '#28a745';
      }
      
      if (this.elements.recognizedText) {
        this.elements.recognizedText.textContent = '';
      }

      // Hide record and skip buttons, show only exit
      if (this.elements.recordBtn) {
        this.elements.recordBtn.style.display = 'none';
      }
      if (this.elements.skipBtn) {
        this.elements.skipBtn.style.display = 'none';
      }
      if (this.elements.playBtn) {
        this.elements.playBtn.style.display = 'none';
      }
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      SpeakingGame.init();
    });
  } else {
    SpeakingGame.init();
  }

  // Expose to VocabApp namespace
  window.VocabApp = window.VocabApp || {};
  window.VocabApp.SpeakingGame = SpeakingGame;

  // Global functions for backward compatibility
  window.openPracticeTalkingModal = function() {
    SpeakingGame.open();
  };
  
  window.closePracticeTalkingModal = function() {
    SpeakingGame.close();
  };
  
  window.resetPracticeTalking = function() {
    SpeakingGame.reset();
  };

})();
