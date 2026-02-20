// ===== Hamburger Menu & Photo Upload =====
  // Hamburger menu functionality
  const hamburgerBtn = document.getElementById('hamburgerBtn');
  const hamburgerMenu = document.getElementById('hamburgerMenu');
  const menuAddWord = document.getElementById('menuAddWord');
  const menuUploadCamera = document.getElementById('menuUploadCamera');
  const menuUploadLibrary = document.getElementById('menuUploadLibrary');
  const menuPractice = document.getElementById('menuPractice');
  const practiceSubmenu = document.getElementById('practiceSubmenu');
  const menuPracticeListening = document.getElementById('menuPracticeListening');
  const menuPracticeWords = document.getElementById('menuPracticeWords');
  const menuPracticeTalking = document.getElementById('menuPracticeTalking');
  const menuPracticeDrawing = document.getElementById('menuPracticeDrawing');
  const menuAddWords = document.getElementById('menuAddWords');
  const addWordsSubmenu = document.getElementById('addWordsSubmenu');

  hamburgerBtn.addEventListener('click', () => {
    hamburgerMenu.classList.toggle('show');
    practiceSubmenu.classList.remove('show');
    addWordsSubmenu.classList.remove('show');
  });

  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.menu-container')) {
      hamburgerMenu.classList.remove('show');
      practiceSubmenu.classList.remove('show');
      addWordsSubmenu.classList.remove('show');
    }
  });

  // Practice submenu toggle (click for mobile)
  menuPractice.addEventListener('click', (e) => {
    e.stopPropagation();
    practiceSubmenu.classList.toggle('show');
    addWordsSubmenu.classList.remove('show');
  });

  // Add Words submenu toggle (click for mobile)
  menuAddWords.addEventListener('click', (e) => {
    e.stopPropagation();
    addWordsSubmenu.classList.toggle('show');
    practiceSubmenu.classList.remove('show');
  });

  // Note: Listening, Words, Talking, Drawing menu handlers are registered later
  // in the second script block after their modal functions are defined

  const photoInputCamera = document.getElementById('photoUploadCamera');
  const photoInputLibrary = document.getElementById('photoUploadLibrary');

  menuAddWord.addEventListener('click', () => {
    hamburgerMenu.classList.remove('show');
    addWordsSubmenu.classList.remove('show');
    openEditModal({});
  });

  menuUploadCamera.addEventListener('click', () => {
    hamburgerMenu.classList.remove('show');
    addWordsSubmenu.classList.remove('show');
    photoInputCamera.click();
  });

  menuUploadLibrary.addEventListener('click', () => {
    hamburgerMenu.classList.remove('show');
    addWordsSubmenu.classList.remove('show');
    photoInputLibrary.click();
  });

  function openPracticeWordsModal() {
    practiceWordsModal.style.display = 'flex';
    practiceWordsStatus.style.display = 'none';
    
    // Update language options visibility based on settings
    document.getElementById('pw_lang_chinese').style.display = langSettings.chinese ? 'flex' : 'none';
    document.getElementById('pw_lang_japanese').style.display = langSettings.japanese ? 'flex' : 'none';
    document.getElementById('pw_lang_french').style.display = langSettings.french ? 'flex' : 'none';
    
    // Ensure a valid language is selected
    const chineseRadio = document.querySelector('#pw_lang_chinese input');
    const japaneseRadio = document.querySelector('#pw_lang_japanese input');
    const frenchRadio = document.querySelector('#pw_lang_french input');
    
    chineseRadio.checked = false;
    japaneseRadio.checked = false;
    frenchRadio.checked = false;
    
    if (langSettings.chinese) {
      chineseRadio.checked = true;
    } else if (langSettings.japanese) {
      japaneseRadio.checked = true;
    } else if (langSettings.french) {
      frenchRadio.checked = true;
    }
  }

  function closePracticeWordsModal() {
    practiceWordsModal.style.display = 'none';
  }

  function showToast(message, type = 'success', persist = false, duration = 6000) {
    const toast = document.getElementById('uploadToast');
    const content = document.getElementById('toastContent');
    content.innerHTML = message;
    toast.className = `show ${type}`;
    if (!persist) {
      setTimeout(() => {
        toast.classList.remove('show');
      }, duration);
    }
  }

  function handlePhotoFiles(fileList) {
    if (!fileList || !fileList.length) return;
    const files = Array.from(fileList);
    const total = files.length;
    const selectedSection = (sectionSelect && sectionSelect.value && sectionSelect.value !== 'all') ? sectionSelect.value : '';

    const uploadOne = (file, index) => {
      showToast(`⏳ OCR scanning... (${index + 1}/${total})`, 'info', true);
      const formData = new FormData();
      formData.append('photo', file);
      if (selectedSection) formData.append('section', selectedSection);

      // Step 1: OCR preview
      return fetch('/ocr_preview', { method: 'POST', body: formData })
      .then(r => r.json())
      .then(pre => {
        if (pre && !pre.error) {
          const linesPre = [
            `📄 OCR: ${pre.ocr_excerpt || file.name}`,
            `🌐 Language: <strong>${pre.detected_language || 'unknown'}</strong>`,
            `⏳ Processing content...`
          ];
          showToast(linesPre.join('<br>'), 'info', true);
        }
        // Step 2: Full processing
        return fetch('/process_photo', {
          method: 'POST',
          body: formData
        });
      })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          showToast(`❌ Error (${file.name}): ${data.error}`, 'error', true);
          return;
        }
        const preview = Array.isArray(data.entries_preview) ? data.entries_preview : [];
        const list = (data.added_words || [])
          .map((w, idx) => {
            const entry = preview[idx];
            const eng = entry && entry.english ? entry.english : '';
            return eng || w || '';
          })
          .filter(Boolean)
          .slice(0, 10);

        const lang = data.detected_language ? data.detected_language : 'unknown';
        const ocrLine = data.ocr_excerpt ? data.ocr_excerpt : file.name;
        const created = data.created ?? data.added ?? 0;
        const duplicates = data.updated ?? 0;
        const totalEntries = data.total_entries ?? (created + duplicates);

        const lines = [
          `📄 OCR: ${ocrLine}`,
          `🌐 Language: <strong>${lang}</strong>`,
          `⏳ Processing content...`,
          `✅ New: <strong>${created}</strong> &nbsp; | &nbsp; 🔁 Duplicates: <strong>${duplicates}</strong> &nbsp; | &nbsp; Total: ${totalEntries}`
        ];

        if (list.length) {
          lines.push(`<div style="margin-top:8px; font-weight:600;">Top new words:</div>${list.map(w => `• ${w}`).join('<br>')}`);
        }

        const html = lines.join('<br>');
        showToast(html, 'success', true);
        performSearch();
        loadSections();
      })
      .catch(err => {
        showToast(`❌ Upload failed for ${file.name}`, 'error', true);
        console.error(err);
      });
    };

    // Process sequentially to keep toasts readable and ensure per-file log entries
    files.reduce((p, file, idx) => p.then(() => uploadOne(file, idx)), Promise.resolve());
  }

  photoInputCamera.addEventListener('change', () => {
    handlePhotoFiles(photoInputCamera.files);
    photoInputCamera.value = '';
  });

  photoInputLibrary.addEventListener('change', () => {
    handlePhotoFiles(photoInputLibrary.files);
    photoInputLibrary.value = '';
  });

// ===== Main Application Logic =====
  const searchInput = document.getElementById('searchInput');
  const grid = document.getElementById('resultsGrid');
  const modal = document.getElementById('wordModal');
  const sectionSelect = document.getElementById('sectionSelect');
  const startChineseQuizBtn = document.getElementById('startChineseQuiz');
  const startFrenchQuizBtn = document.getElementById('startFrenchQuiz');
  const exitQuizBtn = document.getElementById('exitQuiz');
  const quizContainer = document.getElementById('quizContainer');
  const quizCard = document.getElementById('quizCard');
  const nextQuizBtn = document.getElementById('nextQuizCard');
  const quizCounter = document.getElementById('quizCounter');
  const mainControls = document.getElementById('mainControls');
  const quizHeader = document.getElementById('quizHeader');
  const practiceWordsModal = document.getElementById('practiceWordsModal');
  const practiceWordsSection = document.getElementById('pw_section');
  const practiceWordsStatus = document.getElementById('practiceWordsStatus');

  let currentWords = [];
  let currentHanziWriters = [];
  let currentQuizMode = 'chinese'; // default
  let currentQuizWord = null;
  let currentQuizOptions = null;
  let currentQuizState = 'showing-options'; // 'showing-options' or 'showing-result'
  let selectedOptionId = null;
  let quizWins = 0;
  
  // Session score tracking for practice games
  let sessionScore = 0;
  let sessionTotal = 0;
  let sessionStartTime = null;
  let currentGameType = null; // 'listening', 'words', 'speaking', 'drawing'
  let sessionResults = []; // Detailed results for each question
  let sessionTargetRounds = 0; // Target number of rounds for current game
  let practiceSaveToken = 0;
  let practiceSaveInFlight = null;
  let practiceSavedToken = null;

  // Theme Logic
  const themeBtn = document.getElementById('themeBtn');
  
  function updateThemeButton(theme) {
    if (theme === 'dark') {
      themeBtn.textContent = '☀️ Light Mode';
    } else {
      themeBtn.textContent = '🌓 Dark Mode';
    }
  }
  
  themeBtn.onclick = () => {
    const next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeButton(next);
  };
  
  // Set initial theme and button text
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeButton(savedTheme);

  // Language display settings (default: Chinese on, Japanese/French off)
  function getLanguageSettings() {
    const settings = JSON.parse(localStorage.getItem('languageSettings') || '{}');
    return {
      chinese: settings.chinese !== false,
      japanese: settings.japanese === true,
      french: settings.french === true
    };
  }
  let langSettings = getLanguageSettings();

  async function syncLanguageSettingsFromServer() {
    try {
      const response = await fetch('/api/user/languages');
      if (!response.ok) {
        return;
      }
      const data = await response.json();
      const langs = Array.isArray(data.languages) ? data.languages : [];
      const nextSettings = {
        chinese: langs.includes('chinese'),
        japanese: langs.includes('japanese'),
        french: langs.includes('french')
      };
      localStorage.setItem('languageSettings', JSON.stringify(nextSettings));
      localStorage.setItem('enabledLangs', JSON.stringify(langs.length ? langs : ['chinese']));
      langSettings = getLanguageSettings();
      performSearch();
    } catch (error) {
      console.warn('Language settings sync failed:', error);
    }
  }
  
  // Listen for language settings changes from preferences page
  window.addEventListener('storage', (e) => {
    if (e.key === 'languageSettings') {
      langSettings = getLanguageSettings();
      performSearch(); // Re-render cards with new settings
    }
  });

  // Listen for theme changes from other pages/tabs
  window.addEventListener('storage', (e) => {
    if (e.key === 'theme') {
      const newTheme = e.newValue || 'light';
      document.documentElement.setAttribute('data-theme', newTheme);
      updateThemeButton(newTheme);
    }
  });

  // Quiz wins tracking
  function loadQuizWins() {
    quizWins = parseInt(localStorage.getItem('quizWins') || '0');
    updateStreakDisplay();
  }
  function saveQuizWins() {
    localStorage.setItem('quizWins', quizWins.toString());
    updateStreakDisplay();
  }
  function updateStreakDisplay() {
    const streakEl = document.getElementById('streakCount');
    if (streakEl) {
      streakEl.textContent = quizWins % 5;
    }
  }
  function resetQuizWins() {
    quizWins = 0;
    saveQuizWins();
  }
  function addQuizWin() {
    quizWins++;
    sessionScore++;
    saveQuizWins();
  }
  function addQuizAttempt() {
    sessionTotal++;
    console.log('addQuizAttempt:', { sessionTotal, sessionScore, currentGameType });
  }
  function startPracticeSession(gameType) {
    console.log('startPracticeSession:', gameType);
    sessionScore = 0;
    sessionTotal = 0;
    sessionStartTime = Date.now();
    currentGameType = gameType;
    sessionResults = []; // Reset detailed results
    practiceSaveToken += 1;
    practiceSaveInFlight = null;
    practiceSavedToken = null;
  }
  
  function addSessionResult(result) {
    // Add a detailed result for this question
    sessionResults.push({
      vocabulary_id: result.vocabulary_id || null,
      word_hanzi: result.word_hanzi || '',
      word_pinyin: result.word_pinyin || '',
      word_english: result.word_english || '',
      word_french: result.word_french || '',
      question_type: result.question_type || currentGameType,
      question_text: result.question_text || '',
      user_answer: result.user_answer || '',
      correct_answer: result.correct_answer || '',
      is_correct: result.is_correct || false,
      score: result.score || 0
    });
  }
  
  async function savePracticeScore() {
    console.log('savePracticeScore called:', { currentGameType, sessionScore, sessionTotal, resultsCount: sessionResults.length });
    if (!currentGameType || sessionTotal === 0) {
      console.log('Skipping save - no game type or zero total');
      return null;
    }
    if (practiceSavedToken === practiceSaveToken) {
      console.log('Skipping save - already saved for this session');
      return null;
    }
    if (practiceSaveInFlight) {
      return practiceSaveInFlight;
    }
    const duration = sessionStartTime ? Math.round((Date.now() - sessionStartTime) / 1000) : 0;
    try {
      const payload = {
        game_type: currentGameType,
        score: sessionScore,
        total_questions: sessionTotal,
        duration: duration,
        results: sessionResults
      };
      console.log('Saving practice score:', payload);
      practiceSaveInFlight = fetch('/api/user/practice/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      })
        .then(async (response) => {
          const data = await response.json();
          if (data.error) {
            console.error('Server error saving score:', data.error);
            return null;
          }
          console.log('Practice score saved successfully, id:', data.id);
          practiceSavedToken = practiceSaveToken;
          return data.id;
        })
        .catch((error) => {
          console.error('Could not save practice score:', error);
          return null;
        })
        .finally(() => {
          practiceSaveInFlight = null;
        });
      return await practiceSaveInFlight;
    } catch (e) {
      console.error('Could not save practice score:', e);
      return null;
    }
  }
  
  loadQuizWins();

  // Speech Synthesis
  let voicesLoaded = false;
  window.speechSynthesis.onvoiceschanged = () => { voicesLoaded = true; };

  function speak(text, lang = 'zh-CN') {
    if (!text || text.trim() === '') return;
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text.trim());
    utterance.lang = lang;
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    if (voicesLoaded) {
      const voices = speechSynthesis.getVoices();
      const preferred = voices.find(v => v.lang.startsWith(lang));
      if (preferred) utterance.voice = preferred;
    }
    utterance.onerror = (e) => console.warn('Speech error:', e);
    speechSynthesis.speak(utterance);
  }

  function playChinese(text) { speak(text, 'zh-CN'); }
  function playEnglish(text) { speak(text, 'en-GB'); }
  function playFrench(text) { speak(text, 'fr-FR'); }
  function playJapanese(text) { speak(text, 'ja-JP'); }

  function performSearch() {
    const q = searchInput.value.trim();
    const field = document.getElementById('fieldSelect').value;
    const section = sectionSelect.value;

    return fetch(`/search?q=${encodeURIComponent(q)}&field=${field}`)
      .then(r => r.json())
      .then(data => {
        grid.innerHTML = '';
        let filtered = (section === 'all') ? data : data.filter(r => r.section === section);
        currentWords = filtered;

        filtered.forEach(row => {
          const card = document.createElement('div');
          card.className = 'vocab-card';

          // Hanzi text (always use hanzi-cell class)
          const hanziText = (row.hanzi || '').trim();
          const hanziEsc = hanziText.replace(/'/g, "\\'");

          // Build card HTML based on language settings
          let cardHtml = '';
          
          // Chinese section (if enabled)
          if (langSettings.chinese) {
            cardHtml += `
              <div class="hanzi-cell" style="margin-bottom:3px;">${hanziText}</div>
              <div style="position:relative; margin:3px -12px; width:calc(100% + 24px); box-sizing:border-box;">
                <button class="speak-btn" onclick="event.stopPropagation(); playChinese('${hanziEsc}')" style="position:absolute; left:12px; top:50%; transform:translateY(-50%); background:none; border:none; cursor:pointer; font-size:1.3em; padding:0; line-height:1; z-index:1;">🇨🇳</button>
                <div class="pinyin-text" onclick="event.stopPropagation(); playChinese('${hanziEsc}')" style="text-align:left; width:100%; cursor:pointer; padding-left:47px; padding-right:12px;">${row.pinyin || ''}</div>
              </div>`;
          }

          // Japanese section (if enabled)
          if (langSettings.japanese && (row.japanese_kanji || row.japanese_romaji)) {
            const jpKanjiEsc = (row.japanese_kanji || '').replace(/'/g, "\\'");
            if (!langSettings.chinese) {
              // Japanese is primary: big kanji + romaji below (same layout as Chinese)
              cardHtml += `
                <div class="hanzi-cell" style="margin-bottom:3px;">${row.japanese_kanji || ''}</div>
                <div style="position:relative; margin:3px -12px; width:calc(100% + 24px); box-sizing:border-box;">
                  <button class="speak-btn" onclick="event.stopPropagation(); playJapanese('${jpKanjiEsc}')" style="position:absolute; left:12px; top:50%; transform:translateY(-50%); background:none; border:none; cursor:pointer; font-size:1.3em; padding:0; line-height:1; z-index:1;">🇯🇵</button>
                  <div class="pinyin-text" onclick="event.stopPropagation(); playJapanese('${jpKanjiEsc}')" style="text-align:left; width:100%; cursor:pointer; padding-left:47px; padding-right:12px;">${row.japanese_romaji || ''}</div>
                </div>`;
            } else {
              // Japanese is secondary (Chinese is primary): compact row
              cardHtml += `
                <div style="position:relative; margin:2px -12px; width:calc(100% + 24px); box-sizing:border-box;">
                  <button class="speak-btn" onclick="event.stopPropagation(); playJapanese('${jpKanjiEsc}')" style="position:absolute; left:12px; top:50%; transform:translateY(-50%); background:none; border:none; cursor:pointer; font-size:1.3em; padding:0; line-height:1; z-index:1;">🇯🇵</button>
                  <div class="pinyin-text" style="text-align:left; width:100%; padding-left:47px; padding-right:12px;">${row.japanese_kanji || ''} ${row.japanese_romaji ? '(' + row.japanese_romaji + ')' : ''}</div>
                </div>`;
            }
          }

          // French section (if enabled)
          if (langSettings.french) {
            cardHtml += `
              <div style="position:relative; margin:2px -12px; width:calc(100% + 24px); box-sizing:border-box;">
                <button class="speak-btn" onclick="event.stopPropagation(); playFrench('${(row.french || '').replace(/'/g, "\\'")}')" style="position:absolute; left:12px; top:50%; transform:translateY(-50%); background:none; border:none; cursor:pointer; font-size:1.3em; padding:0; line-height:1; z-index:1;">🇫🇷</button>
                <div class="pinyin-text" onclick="event.stopPropagation(); playFrench('${(row.french || '').replace(/'/g, "\\'")}')" style="text-align:left; width:100%; cursor:pointer; padding-left:47px; padding-right:12px;">${row.french || ''}</div>
              </div>`;
          }

          // English (always shown)
          cardHtml += `<div class="translation-text" style="margin-top:8px; text-align:center; width:100%;">${row.english || ''}</div>`;

          card.innerHTML = cardHtml;
          card.onclick = () => openEditModal(row);
          grid.appendChild(card);
        });

        if (quizContainer.style.display !== 'none') {
          const modeText = currentQuizMode === 'chinese' ? 'Chinese → Translations' : 'Français → Translations';
          quizCounter.textContent = `Words in quiz: ${filtered.length} (${modeText})`;
          if (filtered.length === 0) {
            quizCard.innerHTML = '<p>No words match current filters.</p>';
          } else {
            showRandomCard();
          }
        }
        });
  }

  function startQuiz(mode) {
    if (currentWords.length === 0) {
      alert("No words available with current filters. Try broadening your search or category.");
      return;
    }

    currentQuizMode = mode;

    mainControls.style.display = 'none';
    grid.style.display = 'none';

    quizHeader.style.display = 'block';
    quizContainer.style.display = 'block';
    
    // Get target rounds from pw_count input
    sessionTargetRounds = parseInt(document.getElementById('pw_count').value) || 10;
    
    // Start tracking session for 'words' practice
    startPracticeSession('words');

    let modeText;
    if (mode === 'chinese') {
      modeText = 'Chinese → Translations';
    } else if (mode === 'japanese') {
      modeText = 'Japanese → Translations';
    } else {
      modeText = 'Français → Translations';
    }
    quizCounter.textContent = `Words in quiz: ${currentWords.length} (${modeText})`;
    showRandomCard();
  }

  function exitQuiz() {
    // Just hide the quiz UI, don't show results yet
    quizContainer.style.display = 'none';
    quizHeader.style.display = 'none';
    mainControls.style.display = 'block';
    grid.style.display = 'grid';
  }

  function showGameCompletion() {
    // Save the current score
    savePracticeScore();
    
    // Hide active game UI elements
    document.getElementById('quizCard').style.display = 'none';
    document.getElementById('quizOptionsContainer').style.display = 'none';
    document.getElementById('quizResultFeedback').style.display = 'none';
    document.getElementById('streakProgress').style.display = 'none';
    document.getElementById('trophyDisplay').style.display = 'none';
    document.getElementById('exitQuizBtn').style.display = 'none';
    document.getElementById('listeningOptions').style.display = 'none';
    document.getElementById('listeningFeedback').style.display = 'none';
    document.getElementById('listeningNextBtn').style.display = 'none';
    document.getElementById('listeningPlayBtn').style.display = 'none';
    
    // Calculate stats
    const score = sessionScore;
    const total = sessionTotal;
    const pct = total > 0 ? Math.round((score / total) * 100) : 0;
    const duration = sessionStartTime ? Math.round((Date.now() - sessionStartTime) / 1000) : 0;
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    
    // Update stats display
    document.getElementById('gameCompletionScore').textContent = `${score}/${total}`;
    document.getElementById('gameCompletionPercentage').textContent = pct;
    document.getElementById('gameCompletionDuration').textContent = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
    
    // Build detailed review
    let reviewHtml = '';
    if (sessionResults && sessionResults.length > 0) {
      reviewHtml = sessionResults.map((result, idx) => {
        const isCorrect = result.is_correct;
        const statusIcon = isCorrect ? '✅' : '❌';
        const statusColor = isCorrect ? '#51cf66' : '#ff6b6b';
        const isDrawing = result.question_type === 'drawing';
        
        return `
          <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 12px; background: ${isCorrect ? '#f0fdf4' : '#fef2f2'};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
              <span style="font-weight: bold; font-size: 1.05em;">${idx + 1}. ${statusIcon}</span>
              <span style="color: ${statusColor}; font-weight: bold;">${isCorrect ? 'Correct' : 'Incorrect'}</span>
            </div>
            ${isDrawing ? `
              <div style="margin: 10px 0; padding: 10px; background: var(--card-bg); border-radius: 6px;">
                <div style="font-size: 1.3em; font-weight: bold; margin: 5px 0;">${result.word_hanzi || ''}</div>
                <div style="font-size: 0.95em; color: var(--text-muted); margin: 5px 0;">${result.word_pinyin || ''}</div>
                <div style="font-size: 0.9em; color: var(--text-muted);">${result.word_english || ''} ${result.word_french ? '/ ' + result.word_french : ''}</div>
              </div>
            ` : `
              <div style="margin: 10px 0; padding: 10px; background: var(--card-bg); border-radius: 6px;">
                <div style="font-size: 0.9em; color: var(--text-muted);">Question:</div>
                <div style="font-size: 1.1em; font-weight: 500; margin: 5px 0;">${result.question_text || ''}</div>
              </div>
            `}
            <div style="margin: 10px 0;">
              <div style="font-size: 0.9em; color: var(--text-muted); margin-bottom: 5px;">Result:</div>
              <div style="font-weight: 500; color: ${isCorrect ? '#51cf66' : '#ff6b6b'};">${result.user_answer || 'N/A'}</div>
            </div>
            ${!isCorrect && !isDrawing ? `
              <div style="margin: 10px 0;">
                <div style="font-size: 0.9em; color: var(--text-muted); margin-bottom: 5px;">Correct answer:</div>
                <div style="font-weight: 500; color: #51cf66;">${result.correct_answer || 'N/A'}</div>
              </div>
            ` : ''}
          </div>
        `;
      }).join('');
    }
    
    document.getElementById('gameReviewContent').innerHTML = reviewHtml;
    
    // Show completion page
    document.getElementById('gameCompletionPage').style.display = 'block';
  }

  function endQuizSession() {
    showGameCompletion();
  }

  function showListeningCompletion() {
    const score = listeningState.score;
    const total = listeningState.total;
    const pct = total > 0 ? Math.round((score / total) * 100) : 0;
    
    // Save score
    sessionScore = score;
    sessionTotal = total;
    savePracticeScore();

    // Hide practice section, show results
    const practiceSection = document.getElementById('listeningPracticeSection');
    const resultsSection = document.getElementById('listeningResultsSection');
    if (practiceSection) practiceSection.style.display = 'none';
    if (resultsSection) {
      resultsSection.style.display = 'block';
      
      // Update stats
      const scoreEl = document.getElementById('listeningResultsScore');
      const accEl = document.getElementById('listeningResultsAccuracy');
      if (scoreEl) scoreEl.textContent = `${score}/${total}`;
      if (accEl) accEl.textContent = `${pct}%`;
      
      // Build review
      let reviewHtml = '';
      if (sessionResults && sessionResults.length > 0) {
        reviewHtml = sessionResults.map((result, idx) => {
          const isCorrect = result.is_correct;
          const statusIcon = isCorrect ? '✅' : '❌';
          const statusColor = isCorrect ? '#51cf66' : '#ff6b6b';
          
          return `
            <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 10px; background: ${isCorrect ? '#f0fdf4' : '#fef2f2'};">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: bold;">${idx + 1}. ${statusIcon}</span>
                <span style="color: ${statusColor}; font-weight: bold;">${isCorrect ? 'Correct' : 'Incorrect'}</span>
              </div>
              <div style="font-size: 0.9em; color: var(--text-muted);">Your answer: <strong>${result.user_answer || 'N/A'}</strong></div>
              ${!isCorrect ? `<div style="font-size: 0.9em; color: #51cf66;">Correct: <strong>${result.correct_answer || 'N/A'}</strong></div>` : ''}
            </div>
          `;
        }).join('');
      }
      
      const reviewEl = document.getElementById('listeningResultsReview');
      if (reviewEl) reviewEl.innerHTML = reviewHtml;
    }
  }

  function showRandomCard() {
    // Check if we've completed the target rounds
    if (sessionTargetRounds > 0 && sessionTotal >= sessionTargetRounds) {
      showGameCompletion();
      return;
    }
    
    if (currentWords.length === 0) return;
    
    const randomWord = currentWords[Math.floor(Math.random() * currentWords.length)];
    currentQuizWord = randomWord;
    currentQuizState = 'showing-options';
    selectedOptionId = null;
    
    // Fetch quiz options from backend
    fetch('/quiz/options', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({word_id: randomWord.id})
    })
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        console.error(data.error);
        return;
      }
      
      currentQuizOptions = data;
      
      // Display word on card (based on quiz mode)
      let wordText, speakerLang;
      if (currentQuizMode === 'chinese') {
        wordText = randomWord.pinyin;
        speakerLang = 'playChinese';
      } else if (currentQuizMode === 'japanese') {
        wordText = randomWord.japanese_romaji || randomWord.japanese_kanji || '';
        speakerLang = 'playJapanese';
      } else {
        wordText = randomWord.french;
        speakerLang = 'playFrench';
      }
      const wordEsc = (wordText || '').replace(/'/g, "\\'");
      
      quizCard.innerHTML = `
        <div style="font-size:2.6em; margin-bottom:20px; line-height:1.2;">${wordText || ''}</div>
        <button style="background:none; border:none; cursor:pointer; font-size:2.2em; padding:0; line-height:1;" onclick="event.stopPropagation(); ${speakerLang}('${wordEsc}')">🔊</button>
      `;
      
      // Auto-play word
      if (currentQuizMode === 'chinese') {
        playChinese(randomWord.hanzi);
      } else if (currentQuizMode === 'japanese') {
        playJapanese(randomWord.japanese_kanji || randomWord.japanese_romaji);
      } else {
        playFrench(randomWord.french);
      }
      
      // Display answer options
      renderQuizOptions(data.options);
      
      // Show options container, hide result
      document.getElementById('quizOptionsContainer').style.display = 'block';
      document.getElementById('quizResultFeedback').style.display = 'none';
    })
    .catch(err => {
      console.error('Error fetching quiz options:', err);
    });
  }
  
  function renderQuizOptions(options) {
    const container = document.getElementById('quizOptions');
    container.innerHTML = '';
    
    options.forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'quiz-option-btn';

      // Choose display text depending on quiz mode
      let topText = '';
      let bottomText = '';
      if (currentQuizMode === 'french') {
        // For French quiz, show ONLY English (no French - that gives answer away)
        topText = opt.english || '';
        bottomText = '';
      } else if (currentQuizMode === 'japanese') {
        // For Japanese quiz: show English
        topText = opt.english || '';
        bottomText = '';
      } else {
        // For Chinese quiz: show ONLY Hanzi (no pinyin - that gives answer away)
        topText = '';
        bottomText = opt.hanzi || '';
      }

      btn.innerHTML = `<div class="option-top">${topText}</div>` +
                      `<div class="option-hanzi">${bottomText}</div>`;

      btn.style.cssText = `
        padding: 12px;
        border: 2px solid var(--border-color);
        background: var(--card-bg);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        min-height: 110px;
      `;

      btn.onclick = () => {
        selectQuizOption(opt.id, btn, opt);
      };

      container.appendChild(btn);
    });
  }
  
  function selectQuizOption(optionId, btnElement, optionData) {
    // If we've already answered, ignore
    if (currentQuizState === 'showing-result') return;
    
    // Deselect previous
    if (selectedOptionId !== null) {
      document.querySelectorAll('.quiz-option-btn').forEach(b => {
        b.style.background = 'var(--card-bg)';
        b.style.borderColor = 'var(--border-color)';
      });
    }
    
    selectedOptionId = optionId;
    
    // Highlight selected (green)
    btnElement.style.background = '#51cf66';
    btnElement.style.borderColor = '#40c057';
    btnElement.style.color = 'white';
    
    // Disable all buttons to prevent further clicks
    document.querySelectorAll('.quiz-option-btn').forEach(b => {
      b.style.cursor = 'not-allowed';
      b.style.opacity = '0.7';
    });
    
    // Play selected word
    if (currentQuizMode === 'chinese') {
      playChinese(optionData.hanzi || optionData.pinyin);
    } else {
      playFrench(optionData.french);
    }
    
    // IMMEDIATE VALIDATION - click is final answer
    validateQuizAnswer();
  }
  
  function validateQuizAnswer() {
    if (selectedOptionId === null) return;
    
    // Get the selected option for tracking
    const selectedOption = currentQuizOptions.options.find(o => o.id === selectedOptionId);
    
    fetch('/quiz/check', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        correct_id: currentQuizOptions.correct_id,
        selected_id: selectedOptionId
      })
    })
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        console.error(data.error);
        return;
      }
      
      const isCorrect = data.correct;
      const explanation = data.explanation || 'Well done!';
      const correctWord = currentQuizOptions.correct_word;
      
      // Track session stats
      addQuizAttempt();
      
      // Track detailed result
      addSessionResult({
        vocabulary_id: correctWord.id,
        word_hanzi: correctWord.hanzi || '',
        word_pinyin: correctWord.pinyin || '',
        word_english: correctWord.english || '',
        word_french: correctWord.french || '',
        question_type: currentQuizMode === 'chinese' ? 'chinese_to_meaning' : 'french_to_meaning',
        question_text: currentQuizMode === 'chinese' ? correctWord.pinyin : correctWord.french,
        user_answer: selectedOption ? (currentQuizMode === 'chinese' ? selectedOption.hanzi : selectedOption.english) : '',
        correct_answer: currentQuizMode === 'chinese' ? correctWord.hanzi : correctWord.english,
        is_correct: isCorrect,
        score: isCorrect ? 100 : 0
      });
      
      // Show result
      document.getElementById('quizOptionsContainer').style.display = 'none';
      document.getElementById('quizResultFeedback').style.display = 'block';
      
      const resultStatus = document.getElementById('resultStatus');
      const resultExpl = document.getElementById('resultExplanation');
      
      if (isCorrect) {
        resultStatus.innerHTML = '✅ Correct!';
        resultStatus.style.color = '#51cf66';
        addQuizWin();
      } else {
        resultStatus.innerHTML = '❌ Incorrect';
        resultStatus.style.color = '#ff6b6b';
        resetQuizWins();
      }
      
      // Add sentences based on user's preferred languages
      const sentenceEnglish = correctWord.sent_english || '';
      const currentLangSettings = getLanguageSettings();
      
      // Build sentence display for all enabled languages
      let sentenceLines = [];
      
      // Chinese sentence (if enabled)
      if (currentLangSettings.chinese && correctWord.sent_hanzi) {
        const hanziText = correctWord.sent_hanzi.replace(/'/g, "\\'");
        sentenceLines.push(`<div style="margin-bottom:8px;">
          <button style="background:none; border:none; cursor:pointer; font-size:1.3em; padding:0; margin-right:8px; line-height:1;" onclick="event.stopPropagation(); speak('${hanziText}', 'zh-CN');">🇨🇳</button>
          <span style="font-size:0.95em; color:var(--text-muted);">${correctWord.sent_hanzi}</span>
        </div>`);
        if (correctWord.sent_pinyin) {
          sentenceLines.push(`<div style="font-size:0.9em; color:var(--text-muted); margin-left:38px; margin-top:4px;">${correctWord.sent_pinyin}</div>`);
        }
      }
      
      // Japanese sentence (if enabled)
      if (currentLangSettings.japanese && correctWord.sent_japanese_kanji) {
        const jpText = correctWord.sent_japanese_kanji.replace(/'/g, "\\'");
        sentenceLines.push(`<div style="margin-bottom:8px; margin-top:10px;">
          <button style="background:none; border:none; cursor:pointer; font-size:1.3em; padding:0; margin-right:8px; line-height:1;" onclick="event.stopPropagation(); speak('${jpText}', 'ja-JP');">🇯🇵</button>
          <span style="font-size:0.95em; color:var(--text-muted);">${correctWord.sent_japanese_kanji}</span>
        </div>`);
        if (correctWord.sent_japanese_romaji) {
          sentenceLines.push(`<div style="font-size:0.9em; color:var(--text-muted); margin-left:38px; margin-top:4px;">${correctWord.sent_japanese_romaji}</div>`);
        }
      }
      
      // French sentence (if enabled)
      if (currentLangSettings.french && correctWord.sent_french) {
        const frText = correctWord.sent_french.replace(/'/g, "\\'");
        sentenceLines.push(`<div style="margin-bottom:8px; margin-top:10px;">
          <button style="background:none; border:none; cursor:pointer; font-size:1.3em; padding:0; margin-right:8px; line-height:1;" onclick="event.stopPropagation(); speak('${frText}', 'fr-FR');">🇫🇷</button>
          <span style="font-size:0.95em; color:var(--text-muted);">${correctWord.sent_french}</span>
        </div>`);
      }
      
      // English translation (always shown if available)
      if (sentenceEnglish) {
        sentenceLines.push(`<div style="font-size:0.9em; color:var(--text-muted); font-style:italic; margin-left:38px; margin-top:8px;">${sentenceEnglish}</div>`);
      }
      
      let sentenceDisplay = '';
      if (sentenceLines.length > 0) {
        sentenceDisplay = `<div style="margin-top:15px; padding-top:15px; border-top:1px solid var(--border-color);">
          ${sentenceLines.join('')}
        </div>`;
      }
      
      resultExpl.innerHTML = `<strong>Explanation:</strong> ${explanation}${sentenceDisplay}`;
      currentQuizState = 'showing-result';
    })
    .catch(err => {
      console.error('Error validating answer:', err);
    });
  }
  
  function showTrophy() {
    const qualityPct = 90 + Math.random() * 10; // 90-100%
    document.getElementById('trophyQuality').innerHTML = `Quality Score: <strong>${qualityPct.toFixed(0)}%</strong>`;
    document.getElementById('trophyDisplay').style.display = 'block';
  }

  function updateModalFooter() {
    const deleteBtn = document.getElementById('deleteModalBtn');
    const wordId = document.getElementById('mw_id').value;
    deleteBtn.style.display = wordId ? 'block' : 'none';
  }

  function openEditModal(row) {
    document.getElementById('modalTitle').innerText = row ? "Edit Word" : "Add Word";
    document.getElementById('mw_id').value = row ? row.id : "";
    const hanzi = row ? (row.hanzi || "").trim() : "";

    document.getElementById('mw_hanzi').value = hanzi;
    document.getElementById('mw_sent_hanzi').value = row ? row.sent_hanzi : "";

    document.getElementById('mw_pinyin').value = row ? row.pinyin : "";
    document.getElementById('mw_sent_pinyin').value = row ? row.sent_pinyin : "";

    document.getElementById('mw_japanese_kanji').value = row ? (row.japanese_kanji || "") : "";
    document.getElementById('mw_sent_japanese_kanji').value = row ? (row.sent_japanese_kanji || "") : "";
    document.getElementById('mw_japanese_romaji').value = row ? (row.japanese_romaji || "") : "";
    document.getElementById('mw_sent_japanese_romaji').value = row ? (row.sent_japanese_romaji || "") : "";

    document.getElementById('mw_french').value = row ? row.french : "";
    document.getElementById('mw_sent_french').value = row ? row.sent_french : "";

    document.getElementById('mw_english').value = row ? row.english : "";
    document.getElementById('mw_sent_english').value = row ? row.sent_english : "";
    
    // Show/hide language sections based on settings
    document.getElementById('stroke_chinese_section').style.display = langSettings.chinese ? 'block' : 'none';
    document.getElementById('modal_chinese_section').style.display = langSettings.chinese ? 'block' : 'none';
    document.getElementById('stroke_japanese_section').style.display = langSettings.japanese ? 'block' : 'none';
    document.getElementById('modal_japanese_section').style.display = langSettings.japanese ? 'block' : 'none';
    document.getElementById('modal_french_section').style.display = langSettings.french ? 'block' : 'none';
    
    // Populate category suggestions (datalist) and set value
    const sectionInput = document.getElementById('mw_section');
    const rowSection = row ? row.section : "";

    fetch('/sections')
      .then(r => r.json())
      .then(secs => {
        const dl = document.getElementById('mw_sections_list');
        dl.innerHTML = '';
        secs.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s;
          dl.appendChild(opt);
        });

        // Set the input value to the row's section if present
        sectionInput.value = rowSection || '';
      })
      .catch(() => { sectionInput.value = rowSection || ''; });

    // Chinese stroke animation setup
    const container = document.getElementById('strokeAnimContainer');
    container.innerHTML = '';
    currentHanziWriters = [];

    if (langSettings.chinese) {
      if (hanzi.length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted); padding-top:60px; font-size:0.9rem;">No Hanzi to practice</p>';
      } else if (hanzi.length > 10) {
        container.innerHTML = '<p style="color:var(--text-muted); padding-top:60px; font-size:0.9rem;">Too many characters (max 10)</p>';
      } else {
        const scrollWrapper = document.createElement('div');
        scrollWrapper.style.display = 'flex';
        scrollWrapper.style.alignItems = 'center';
        scrollWrapper.style.gap = '0px';
        scrollWrapper.style.padding = '0 10px';
        scrollWrapper.style.height = '100%';
        container.appendChild(scrollWrapper);

        const charSize = 140;

        for (let i = 0; i < hanzi.length; i++) {
          const char = hanzi[i];
          const charContainer = document.createElement('div');
          charContainer.style.width = `${charSize}px`;
          charContainer.style.height = `${charSize}px`;
          charContainer.style.flexShrink = '0';
          if (i < hanzi.length - 1) {
            charContainer.style.marginRight = '-25px';
          }
          scrollWrapper.appendChild(charContainer);

          const writer = HanziWriter.create(charContainer, char, {
            width: charSize,
            height: charSize,
            padding: 10,
            showOutline: true,
            showCharacter: true,
            strokeColor: '#168',
            radicalColor: '#168',
            delayBetweenStrokes: 700,
            delayBetweenLoops: 3000
          });

          writer.loopCharacterAnimation();
          currentHanziWriters.push(writer);
        }
      }
    }
    
    // Japanese stroke animation setup
    const japaneseContainer = document.getElementById('strokeAnimContainerJapanese');
    japaneseContainer.innerHTML = '';
    
    if (langSettings.japanese) {
      const japaneseKanji = row ? (row.japanese_kanji || "").trim() : "";
      // Filter to only include kanji characters (CJK unified ideographs)
      const kanjiChars = japaneseKanji.split('').filter(char => {
        const code = char.charCodeAt(0);
        return (code >= 0x4E00 && code <= 0x9FFF) || // CJK Unified Ideographs
               (code >= 0x3400 && code <= 0x4DBF);   // CJK Extension A
      });
      
      if (kanjiChars.length === 0) {
        japaneseContainer.innerHTML = '<p style="color:var(--text-muted); padding-top:60px; font-size:0.9rem;">No Kanji to practice</p>';
      } else if (kanjiChars.length > 10) {
        japaneseContainer.innerHTML = '<p style="color:var(--text-muted); padding-top:60px; font-size:0.9rem;">Too many characters (max 10)</p>';
      } else {
        const scrollWrapper = document.createElement('div');
        scrollWrapper.style.display = 'flex';
        scrollWrapper.style.alignItems = 'center';
        scrollWrapper.style.gap = '0px';
        scrollWrapper.style.padding = '0 10px';
        scrollWrapper.style.height = '100%';
        japaneseContainer.appendChild(scrollWrapper);

        const charSize = 140;

        for (let i = 0; i < kanjiChars.length; i++) {
          const char = kanjiChars[i];
          const charContainer = document.createElement('div');
          charContainer.style.width = `${charSize}px`;
          charContainer.style.height = `${charSize}px`;
          charContainer.style.flexShrink = '0';
          if (i < kanjiChars.length - 1) {
            charContainer.style.marginRight = '-25px';
          }
          scrollWrapper.appendChild(charContainer);

          try {
            const writer = HanziWriter.create(charContainer, char, {
              width: charSize,
              height: charSize,
              padding: 10,
              showOutline: true,
              showCharacter: true,
              strokeColor: '#c41',
              radicalColor: '#c41',
              delayBetweenStrokes: 700,
              delayBetweenLoops: 3000
            });
            writer.loopCharacterAnimation();
            currentHanziWriters.push(writer);
          } catch (e) {
            // Character not supported by HanziWriter
            charContainer.innerHTML = `<div style="display:flex; align-items:center; justify-content:center; height:100%; font-size:3em;">${char}</div>`;
          }
        }
      }
    }

    modal.style.display = 'flex';
    updateModalFooter();
  }

  function closeModal() {
    modal.style.display = 'none';
    const container = document.getElementById('strokeAnimContainer');
    container.innerHTML = '';
    const japaneseContainer = document.getElementById('strokeAnimContainerJapanese');
    japaneseContainer.innerHTML = '';
    currentHanziWriters = [];
  }

  // Removed animate strokes button functionality

  document.getElementById('saveModal').onclick = () => {
    // Get section from the editable input (datalist) - user can type or pick
    const finalSection = document.getElementById('mw_section').value.trim();
    
    const payload = {
      hanzi: document.getElementById('mw_hanzi').value.trim(),
      pinyin: document.getElementById('mw_pinyin').value.trim(),
      japanese_kanji: document.getElementById('mw_japanese_kanji').value.trim(),
      japanese_romaji: document.getElementById('mw_japanese_romaji').value.trim(),
      french: document.getElementById('mw_french').value.trim(),
      english: document.getElementById('mw_english').value.trim(),
      section: finalSection,
      sent_hanzi: document.getElementById('mw_sent_hanzi').value.trim(),
      sent_pinyin: document.getElementById('mw_sent_pinyin').value.trim(),
      sent_japanese_kanji: document.getElementById('mw_sent_japanese_kanji').value.trim(),
      sent_japanese_romaji: document.getElementById('mw_sent_japanese_romaji').value.trim(),
      sent_french: document.getElementById('mw_sent_french').value.trim(),
      sent_english: document.getElementById('mw_sent_english').value.trim()
    };
    
    if (!payload.section) {
      alert("Category / Section is required!");
      return;
    }
    if (!payload.hanzi && !payload.pinyin && !payload.english && !payload.french) {
      alert("At least one of Hanzi, Pinyin, English or French is required!");
      return;
    }

    const wordId = document.getElementById('mw_id').value;
    const url = wordId ? '/update' : '/add_word';
    const method = 'POST';

    let body;
    let headers = {};
    if (wordId) {
      payload.id = wordId;
      body = JSON.stringify(payload);
      headers['Content-Type'] = 'application/json';
    } else {
      const formData = new FormData();
      for (const key in payload) {
        formData.append(key, payload[key]);
      }
      body = formData;
    }

    fetch(url, {
      method,
      headers,
      body
    })
    .then(r => r.json())
    .then(data => {
      if (data.ok === false || data.error) {
        alert("Error: " + (data.error || "Save failed"));
        return;
      }
      const currentCategory = sectionSelect.value;
      closeModal();
      loadSections();
      // Restore category selection after reload
      setTimeout(() => {
        sectionSelect.value = currentCategory;
        performSearch();
      }, 100);
    })
    .catch(err => {
      console.error(err);
      alert("Network error while saving");
    });
  };

  document.getElementById('deleteModalBtn').addEventListener('click', () => {
    const wordId = document.getElementById('mw_id').value;
    const hanzi = document.getElementById('mw_hanzi').value.trim() || "this word";

    if (!confirm(`Are you sure you want to permanently delete "${hanzi}"?`)) return;

    fetch('/delete', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({id: wordId})
    })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        const currentCategory = sectionSelect.value;
        closeModal();
        loadSections();
        // Restore category selection after reload
        setTimeout(() => {
          sectionSelect.value = currentCategory;
          performSearch();
        }, 100);
      } else {
        alert("Error deleting: " + (data.error || "Unknown error"));
      }
    })
    .catch(err => {
      console.error(err);
      alert("Network error while deleting");
    });
  });

  function loadSections() {
    fetch('/sections').then(r => r.json()).then(secs => {
      const ss = document.getElementById('sectionSelect');
      ss.innerHTML = '<option value="all">All Categories</option>';
      secs.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s; opt.textContent = s; ss.appendChild(opt);
      });

      if (practiceWordsSection) {
        practiceWordsSection.innerHTML = '<option value="all">All Categories</option>';
        secs.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s; opt.textContent = s; practiceWordsSection.appendChild(opt);
        });
      }
    });
  }

  loadSections();
  performSearch();

  // Event Listeners
  searchInput.addEventListener('input', performSearch);
  document.getElementById('clearSearch').onclick = () => { searchInput.value = ''; performSearch(); };
  sectionSelect.addEventListener('change', performSearch);

  if (startChineseQuizBtn) startChineseQuizBtn.addEventListener('click', () => startQuiz('chinese'));
  if (startFrenchQuizBtn) startFrenchQuizBtn.addEventListener('click', () => startQuiz('french'));
  
  // Exit Quiz - single listener that handles both trophy hiding and exit
  if (exitQuizBtn) {
    exitQuizBtn.addEventListener('click', () => {
      const trophy = document.getElementById('trophyDisplay');
      if (trophy) trophy.style.display = 'none';
      exitQuiz();
    });
  }
  
  // Quiz-specific event listeners (with safety checks)
  const quizValidateBtn = document.getElementById('quizValidateBtn');
  if (quizValidateBtn) quizValidateBtn.addEventListener('click', validateQuizAnswer);
  
  const nextQuizCardAlt = document.getElementById('nextQuizCardAlt');
  if (nextQuizCardAlt) nextQuizCardAlt.addEventListener('click', showRandomCard);
  
  const continueQuizBtn = document.getElementById('continueQuizBtn');
  if (continueQuizBtn) {
    continueQuizBtn.addEventListener('click', () => {
      const trophy = document.getElementById('trophyDisplay');
      if (trophy) trophy.style.display = 'none';
      showRandomCard();
    });
  }
  
  const resetTrophyBtn = document.getElementById('resetTrophyBtn');
  if (resetTrophyBtn) {
    resetTrophyBtn.addEventListener('click', () => {
      const trophy = document.getElementById('trophyDisplay');
      if (trophy) trophy.style.display = 'none';
      resetQuizWins();
      showRandomCard();
    });
  }
  
  // Unified game completion handlers (with safety checks)
  const gamePlayAgainBtn = document.getElementById('gamePlayAgainBtn');
  if (gamePlayAgainBtn) {
    gamePlayAgainBtn.addEventListener('click', () => {
      const page = document.getElementById('gameCompletionPage');
      if (page) page.style.display = 'none';
      
      // Reset session for replay
      sessionScore = 0;
      sessionTotal = 0;
      sessionStartTime = Date.now();
      sessionResults = [];
      
      // Re-show game UI based on game type
      if (currentGameType === 'words') {
        // Make sure quiz container is visible
        if (quizContainer) quizContainer.style.display = 'block';
        if (quizHeader) quizHeader.style.display = 'block';
        const card = document.getElementById('quizCard');
        const streak = document.getElementById('streakProgress');
        const exitBtn = document.getElementById('exitQuizBtn');
        const feedback = document.getElementById('quizResultFeedback');
        const options = document.getElementById('quizOptionsContainer');
        if (card) card.style.display = 'flex';
        if (streak) streak.style.display = 'block';
        if (exitBtn) exitBtn.style.display = 'block';
        if (feedback) feedback.style.display = 'none';
        if (options) options.style.display = 'none';
        showRandomCard();
      } else if (currentGameType === 'listening') {
        const opts = document.getElementById('listeningOptions');
        const fb = document.getElementById('listeningFeedback');
        if (opts) opts.style.display = 'grid';
        if (fb) fb.style.display = 'none';
        showNextListeningWord();
      } else if (currentGameType === 'speaking') {
        const section = document.getElementById('talkingPracticeSection');
        const recordBtn = document.getElementById('talkingRecordBtn');
        const skipBtn = document.getElementById('talkingSkipBtn');
        const playBtn = document.getElementById('talkingPlayBtn');
        if (section) section.style.display = 'block';
        if (recordBtn) recordBtn.style.display = 'inline-block';
        if (skipBtn) skipBtn.style.display = 'inline-block';
        if (playBtn) playBtn.style.display = 'inline-block';
        // Reset speaking practice state
        practiceTalkingState.currentIndex = 0;
        practiceTalkingState.score = 0;
        practiceTalkingState.total = 0;
        showNextWord();
      } else if (currentGameType === 'drawing') {
        const section = document.getElementById('drawingPracticeSection');
        if (section) section.style.display = 'block';
        // Reset drawing practice state
        drawingPracticeState.currentIndex = 0;
        drawingPracticeState.score = 0;
        drawingPracticeState.total = 0;
        showNextDrawingWord();
      }
    });
  }
  
  const gameExitBtn = document.getElementById('gameExitBtn');
  if (gameExitBtn) {
    gameExitBtn.addEventListener('click', () => {
      // Exit based on game type
      if (currentGameType === 'words') {
        if (quizContainer) quizContainer.style.display = 'none';
        if (quizHeader) quizHeader.style.display = 'none';
        if (mainControls) mainControls.style.display = 'block';
        if (grid) grid.style.display = 'grid';
      } else if (currentGameType === 'listening') {
        closePracticeModal();
      } else if (currentGameType === 'speaking') {
        closePracticeTalkingModal();
      } else if (currentGameType === 'drawing') {
        closePracticeDrawingModal();
      }
      const page = document.getElementById('gameCompletionPage');
      if (page) page.style.display = 'none';
    });
  }
  
  // Practice Modal Functions
  function closePracticeModal() {
    // Save score if there are any attempts before closing (but not if at completion)
    if (listeningState.total > 0 && listeningState.currentIndex < listeningState.words.length) {
      sessionScore = listeningState.score;
      sessionTotal = listeningState.total;
      savePracticeScore();
    }
    document.getElementById('practiceModal').style.display = 'none';
    window.speechSynthesis.cancel();
    resetListeningPractice();
  }

  // Listening Quiz State
  const listeningState = {
    words: [],
    currentIndex: 0,
    score: 0,
    total: 0,
    language: 'chinese',
    currentWord: null,
    answered: false
  };

  function resetListeningPractice() {
    listeningState.words = [];
    listeningState.currentIndex = 0;
    listeningState.score = 0;
    listeningState.total = 0;
    listeningState.currentWord = null;
    listeningState.answered = false;
    sessionResults = [];
    sessionScore = 0;
    sessionTotal = 0;
    
    const configSection = document.getElementById('listeningConfigSection');
    const practiceSection = document.getElementById('listeningPracticeSection');
    const resultsSection = document.getElementById('listeningResultsSection');
    if (configSection) configSection.style.display = 'block';
    if (practiceSection) practiceSection.style.display = 'none';
    if (resultsSection) resultsSection.style.display = 'none';
  }

  function openPracticeListeningModal() {
    resetListeningPractice();
    // Populate categories from main sectionSelect (same as other games)
    const plSection = document.getElementById('pl_section');
    if (plSection && sectionSelect) {
      plSection.innerHTML = '<option value="all">All Categories</option>';
      const options = Array.from(sectionSelect.options).slice(1);
      options.forEach(opt => {
        const newOpt = document.createElement('option');
        newOpt.value = opt.value;
        newOpt.textContent = opt.textContent;
        plSection.appendChild(newOpt);
      });
    }
    
    // Update language options visibility based on settings
    document.getElementById('pl_lang_chinese').style.display = langSettings.chinese ? 'flex' : 'none';
    document.getElementById('pl_lang_japanese').style.display = langSettings.japanese ? 'flex' : 'none';
    document.getElementById('pl_lang_french').style.display = langSettings.french ? 'flex' : 'none';
    
    // Ensure a valid language is selected
    const chineseRadio = document.querySelector('#pl_lang_chinese input');
    const japaneseRadio = document.querySelector('#pl_lang_japanese input');
    const frenchRadio = document.querySelector('#pl_lang_french input');
    
    // Select the first available language
    chineseRadio.checked = false;
    japaneseRadio.checked = false;
    frenchRadio.checked = false;
    
    if (langSettings.chinese) {
      chineseRadio.checked = true;
    } else if (langSettings.japanese) {
      japaneseRadio.checked = true;
    } else if (langSettings.french) {
      frenchRadio.checked = true;
    }
    
    document.getElementById('practiceModal').style.display = 'flex';
  }

  async function startListeningPractice() {
    const lang = (document.querySelector('input[name="pl_lang"]:checked') || {}).value || 'chinese';
    const section = document.getElementById('pl_section').value || 'all';
    const count = parseInt(document.getElementById('pl_count').value) || 10;

    // Start unified practice session tracking
    startPracticeSession('listening');
    sessionTargetRounds = count;  // Set target rounds
    listeningState.language = lang;
    listeningState.score = 0;
    listeningState.total = 0;

    try {
      const response = await fetch(`/random_words?section=${encodeURIComponent(section)}&limit=${count}`);
      if (!response.ok) throw new Error('Failed to fetch words');
      const words = await response.json();

      if (!words || words.length === 0) {
        showToast('No words found for this category', 'error');
        return;
      }

      listeningState.words = words;
      listeningState.currentIndex = 0;

      document.getElementById('listeningConfigSection').style.display = 'none';
      document.getElementById('listeningPracticeSection').style.display = 'block';
      
      showNextListeningWord();
    } catch (err) {
      console.error('Error starting listening practice:', err);
      showToast('Error loading words. Please try again.', 'error');
    }
  }

  function showNextListeningWord() {
    // Check if we've reached target rounds
    if (sessionTargetRounds > 0 && sessionTotal >= sessionTargetRounds) {
      showListeningCompletion();
      return;
    }
    
    if (listeningState.currentIndex >= listeningState.words.length) {
      showListeningCompletion();
      return;
    }

    listeningState.answered = false;
    const word = listeningState.words[listeningState.currentIndex];
    listeningState.currentWord = word;

    // Generate 3 random wrong options from the quiz word set
    const wrongOptions = listeningState.words
      .filter(v => v.english && v.english !== word.english)
      .sort(() => Math.random() - 0.5)
      .slice(0, 3)
      .map(v => v.english);

    // Add correct answer and shuffle
    const options = [...wrongOptions, word.english].sort(() => Math.random() - 0.5);

    // Update UI
    document.getElementById('listeningCurrent').textContent = listeningState.currentIndex + 1;
    document.getElementById('listeningTotal').textContent = listeningState.words.length;
    document.getElementById('listeningScore').textContent = listeningState.score;
    document.getElementById('listeningFeedback').style.display = 'none';
    document.getElementById('listeningNextBtn').style.display = 'none';

    // Create option buttons
    const optionsContainer = document.getElementById('listeningOptions');
    optionsContainer.innerHTML = options.map((opt, i) => `
      <button class="listening-option secondary" onclick="selectListeningOption(this, '${opt.replace(/'/g, "\\'")}')" style="padding:12px; text-align:left; font-size:1em;">
        ${String.fromCharCode(65 + i)}. ${opt}
      </button>
    `).join('');

    // Auto-play the audio after a brief delay
    setTimeout(() => playListeningAudio(), 300);
  }

  function playListeningAudio() {
    const word = listeningState.currentWord;
    if (!word) return;

    const lang = listeningState.language;
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
    
    speakText(targetWord, langCode);
  }

  function selectListeningOption(btn, selected) {
    if (listeningState.answered) return;
    listeningState.answered = true;

    const word = listeningState.currentWord;
    const correct = word.english;
    const isCorrect = selected === correct;

    listeningState.total++;
    if (isCorrect) listeningState.score++;

    // Update session tracking
    sessionTotal = listeningState.total;
    sessionScore = listeningState.score;

    // Track detailed result
    const lang = listeningState.language;
    let targetWord;
    if (lang === 'chinese') {
      targetWord = word.hanzi;
    } else if (lang === 'japanese') {
      targetWord = word.japanese_kanji || word.japanese_romaji;
    } else {
      targetWord = word.french;
    }
    addSessionResult({
      vocabulary_id: word.id,
      word_hanzi: word.hanzi || '',
      word_pinyin: word.pinyin || '',
      word_english: word.english || '',
      word_french: word.french || '',
      question_type: 'listening',
      question_text: `Identify: "${targetWord}"`,
      user_answer: selected,
      correct_answer: correct,
      is_correct: isCorrect,
      score: isCorrect ? 100 : 0
    });

    // Mark all buttons
    const buttons = document.querySelectorAll('.listening-option');
    buttons.forEach(b => {
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
    const feedback = document.getElementById('listeningFeedback');
    const lang2 = listeningState.language;
    let display;
    if (lang2 === 'chinese') {
      display = `${word.hanzi} (${word.pinyin || ''})`;
    } else if (lang2 === 'japanese') {
      display = `${word.japanese_kanji || ''} (${word.japanese_romaji || ''})`;
    } else {
      display = word.french;
    }
    if (isCorrect) {
      feedback.innerHTML = `✅ Correct! <strong>${display}</strong> = ${correct}`;
      feedback.style.background = 'rgba(76, 175, 80, 0.2)';
    } else {
      feedback.innerHTML = `❌ Wrong! <strong>${display}</strong> = ${correct}`;
      feedback.style.background = 'rgba(244, 67, 54, 0.2)';
    }
    feedback.style.display = 'block';

    // Update score display
    document.getElementById('listeningScore').textContent = listeningState.score;

    // Show next button
    document.getElementById('listeningNextBtn').style.display = 'inline-block';
  }
  function nextListeningWord() {
    listeningState.currentIndex++;
    showNextListeningWord();
  }

  // Event listeners for Listening practice (with safety checks)
  const startPracListening = document.getElementById('startPracticeListening');
  if (startPracListening) startPracListening.addEventListener('click', startListeningPractice);
  
  const listeningPlayBtn = document.getElementById('listeningPlayBtn');
  if (listeningPlayBtn) listeningPlayBtn.addEventListener('click', playListeningAudio);
  
  const listeningNextBtn = document.getElementById('listeningNextBtn');
  if (listeningNextBtn) listeningNextBtn.addEventListener('click', nextListeningWord);
  
  const listeningExitBtn = document.getElementById('listeningExitBtn');
  if (listeningExitBtn) listeningExitBtn.addEventListener('click', closePracticeModal);

  function speakText(text, lang) {
    return new Promise((resolve, reject) => {
      if (!window.speechSynthesis) {
        resolve();
        return;
      }
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      utterance.rate = 0.9;
      utterance.pitch = 1;
      
      utterance.onend = () => resolve();
      utterance.onerror = (e) => {
        console.error('Speech error:', e);
        resolve();
      };
      
      window.speechSynthesis.speak(utterance);
    });
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  document.getElementById('startPracticeWords').addEventListener('click', async () => {
    const lang = (document.querySelector('input[name="pw_lang"]:checked') || {}).value || 'chinese';
    const sectionChoice = practiceWordsSection ? practiceWordsSection.value : 'all';
    practiceWordsStatus.style.display = 'block';
    practiceWordsStatus.textContent = 'Loading words...';

    // Apply selected section to main filter then refresh
    if (sectionSelect) {
      sectionSelect.value = sectionChoice;
    }

    try {
      await performSearch();
      if (!currentWords || currentWords.length === 0) {
        practiceWordsStatus.textContent = 'No words available for this category.';
        return;
      }

      closePracticeWordsModal();
      startQuiz(lang);
    } catch (err) {
      console.error('Practice Words error', err);
      practiceWordsStatus.textContent = 'Error loading words. Please try again.';
    }
  });

  // ============= PRACTICE TALKING FUNCTIONALITY =============
  
  let practiceTalkingState = {
    words: [],
    currentIndex: 0,
    score: 0,
    total: 0,
    language: 'chinese',
    mode: 'words',
    recognition: null,
    isRecording: false
  };

  function openPracticeTalkingModal() {
    document.getElementById('practiceTalkingModal').style.display = 'flex';
    document.getElementById('talkingConfigSection').style.display = 'block';
    document.getElementById('talkingPracticeSection').style.display = 'none';
    
    // Update language options visibility based on settings
    document.getElementById('pt_lang_chinese').style.display = langSettings.chinese ? 'flex' : 'none';
    document.getElementById('pt_lang_japanese').style.display = langSettings.japanese ? 'flex' : 'none';
    document.getElementById('pt_lang_french').style.display = langSettings.french ? 'flex' : 'none';
    
    // Ensure a valid language is selected
    const chineseRadio = document.querySelector('#pt_lang_chinese input');
    const japaneseRadio = document.querySelector('#pt_lang_japanese input');
    const frenchRadio = document.querySelector('#pt_lang_french input');
    
    chineseRadio.checked = false;
    japaneseRadio.checked = false;
    frenchRadio.checked = false;
    
    if (langSettings.chinese) {
      chineseRadio.checked = true;
    } else if (langSettings.japanese) {
      japaneseRadio.checked = true;
    } else if (langSettings.french) {
      frenchRadio.checked = true;
    }
    
    // Populate categories
    const ptSection = document.getElementById('pt_section');
    if (ptSection && sectionSelect) {
      ptSection.innerHTML = '<option value="all">All Categories</option>';
      const options = Array.from(sectionSelect.options).slice(1);
      options.forEach(opt => {
        const newOpt = document.createElement('option');
        newOpt.value = opt.value;
        newOpt.textContent = opt.textContent;
        ptSection.appendChild(newOpt);
      });
    }
  }

  function closePracticeTalkingModal() {
    // Only save if we have attempts AND showCompletionMessage hasn't already saved
    // Check if not already at completion (score hasn't been saved yet)
    if (practiceTalkingState.total > 0 && practiceTalkingState.currentIndex < practiceTalkingState.words.length) {
      // Sync session tracking with practiceTalkingState for saving
      sessionScore = practiceTalkingState.score;
      sessionTotal = practiceTalkingState.total;
      savePracticeScore();
    }
    
    document.getElementById('practiceTalkingModal').style.display = 'none';
    stopRecognition();
    window.speechSynthesis.cancel();
    resetPracticeTalking();
  }

  function resetPracticeTalking() {
    practiceTalkingState = {
      words: [],
      currentIndex: 0,
      score: 0,
      total: 0,
      language: 'chinese',
      mode: 'words',
      recognition: null,
      isRecording: false
    };
  }

  function stopRecognition() {
    if (practiceTalkingState.recognition) {
      try {
        practiceTalkingState.recognition.stop();
      } catch (e) {
        console.log('Recognition already stopped');
      }
    }
    practiceTalkingState.isRecording = false;
    const recordBtn = document.getElementById('talkingRecordBtn');
    if (recordBtn) {
      recordBtn.textContent = '🎤 Record';
      recordBtn.classList.remove('recording');
    }
  }

  async function startPracticeTalkingSession() {
    const lang = (document.querySelector('input[name="pt_lang"]:checked') || {}).value || 'chinese';
    const mode = (document.querySelector('input[name="pt_mode"]:checked') || {}).value || 'words';
    const section = document.getElementById('pt_section').value || 'all';
    const count = parseInt(document.getElementById('pt_count').value) || 10;

    // Start unified practice session tracking
    startPracticeSession('speaking');
    sessionTargetRounds = count;  // Set target rounds

    // Fetch words from backend
    try {
      const response = await fetch(`/random_words?section=${encodeURIComponent(section)}&limit=${count}`);
      if (!response.ok) throw new Error('Failed to fetch words');
      const words = await response.json();

      if (!words || words.length === 0) {
        showToast('No words found for this category', 'error');
        return;
      }

      practiceTalkingState.words = words;
      practiceTalkingState.currentIndex = 0;
      practiceTalkingState.score = 0;
      practiceTalkingState.total = 0;
      practiceTalkingState.language = lang;
      practiceTalkingState.mode = mode;

      document.getElementById('talkingConfigSection').style.display = 'none';
      document.getElementById('talkingPracticeSection').style.display = 'block';
      
      showNextWord();
    } catch (err) {
      console.error('Error starting practice:', err);
      showToast('Error loading words. Please try again.', 'error');
    }
  }

  function showNextWord() {
    // Check if we've reached target rounds
    if (sessionTargetRounds > 0 && sessionTotal >= sessionTargetRounds) {
      showCompletionMessage();
      return;
    }
    
    if (practiceTalkingState.currentIndex >= practiceTalkingState.words.length) {
      showCompletionMessage();
      return;
    }

    const word = practiceTalkingState.words[practiceTalkingState.currentIndex];
    const lang = practiceTalkingState.language;
    const mode = practiceTalkingState.mode;

    // Reset feedback
    const feedback = document.getElementById('talkingFeedback');
    feedback.style.display = 'none';

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
      
      document.getElementById('talkingTargetText').textContent = targetText;
      document.getElementById('talkingPinyinText').textContent = pinyinText;
      document.getElementById('talkingEnglishText').textContent = word.english;
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
      
      document.getElementById('talkingTargetText').textContent = targetText || 'No example available';
      document.getElementById('talkingPinyinText').textContent = pinyinText;
      document.getElementById('talkingEnglishText').textContent = word.sent_english || word.english;
    }

    // Update progress
    document.getElementById('talkingScore').textContent = practiceTalkingState.score;
    document.getElementById('talkingTotal').textContent = practiceTalkingState.total;
  }

  function playCurrentWord() {
    const word = practiceTalkingState.words[practiceTalkingState.currentIndex];
    const lang = practiceTalkingState.language;
    const mode = practiceTalkingState.mode;
    
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
      speakText(textToSpeak, langCode);
    }
  }

  function startRecording() {
    if (practiceTalkingState.isRecording) {
      stopRecognition();
      return;
    }

    // Server-side recording for better mobile compatibility
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showToast('Microphone access not supported in this browser', 'error');
      return;
    }

    const recordBtn = document.getElementById('talkingRecordBtn');
    recordBtn.textContent = '⏹️ Stop';
    recordBtn.classList.add('recording');
    practiceTalkingState.isRecording = true;

    const word = practiceTalkingState.words[practiceTalkingState.currentIndex];
    const lang = practiceTalkingState.language;
    const mode = practiceTalkingState.mode;
    
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
      .then(stream => {
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
          audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          // Stop all tracks
          stream.getTracks().forEach(track => track.stop());
          
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
              showToast('Transcription error: ' + result.error, 'error');
              stopRecognition();
              return;
            }

            if (!result.success) {
              showFeedback(false, result.recognized || '', 0, result.message);
              stopRecognition();
              return;
            }

            // Show feedback
            showFeedback(result.is_correct, result.recognized, result.confidence);
            
          } catch (error) {
            console.error('Transcription request failed:', error);
            showToast('Failed to process recording. Please try again.', 'error');
          } finally {
            stopRecognition();
          }
        };

        mediaRecorder.start();
        practiceTalkingState.mediaRecorder = mediaRecorder;

        // Auto-stop after 5 seconds
        setTimeout(() => {
          if (practiceTalkingState.isRecording && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
        }, 5000);

      })
      .catch(error => {
        console.error('Microphone access denied:', error);
        showToast('Microphone access denied. Please allow microphone access.', 'error');
        stopRecognition();
      });
  }

  function stopRecognition() {
    if (practiceTalkingState.mediaRecorder && practiceTalkingState.mediaRecorder.state === 'recording') {
      practiceTalkingState.mediaRecorder.stop();
    }
    practiceTalkingState.isRecording = false;
    const recordBtn = document.getElementById('talkingRecordBtn');
    if (recordBtn) {
      recordBtn.textContent = '🎤 Record';
      recordBtn.classList.remove('recording');
    }
  }

  function showFeedback(isCorrect, recognized, confidence, customMessage) {
    const feedback = document.getElementById('talkingFeedback');
    const feedbackText = document.getElementById('talkingFeedbackText');
    const recognizedText = document.getElementById('talkingRecognizedText');
    
    // Get current word for result tracking
    const currentWord = practiceTalkingState.words[practiceTalkingState.currentIndex];
    const lang = practiceTalkingState.language;
    const mode = practiceTalkingState.mode;
    let expectedText = '';
    if (mode === 'words') {
      expectedText = lang === 'chinese' ? currentWord.hanzi : currentWord.french;
    } else {
      expectedText = lang === 'chinese' ? currentWord.sent_hanzi : currentWord.sent_french;
    }

    feedback.style.display = 'block';
    
    if (customMessage) {
      feedback.style.background = 'rgba(255, 193, 7, 0.1)';
      feedback.style.border = '2px solid #ffc107';
      feedbackText.innerHTML = '⚠️ ' + customMessage;
      feedbackText.style.color = '#ffc107';
      recognizedText.textContent = recognized ? `You said: "${recognized}"` : '';
      practiceTalkingState.total++;
      addQuizAttempt();
      // Track as incorrect for custom messages (warnings)
      const confidenceScore = Math.round((confidence || 0) * 100);
      addSessionResult({
        vocabulary_id: currentWord?.id,
        word_hanzi: currentWord?.hanzi || '',
        word_pinyin: currentWord?.pinyin || '',
        word_english: currentWord?.english || '',
        word_french: currentWord?.french || '',
        question_type: 'speaking_' + mode,
        question_text: expectedText,
        user_answer: recognized || 'No response',
        correct_answer: expectedText,
        is_correct: false,
        score: confidenceScore
      });
    } else if (isCorrect) {
      feedback.style.background = 'rgba(40, 167, 69, 0.1)';
      feedback.style.border = '2px solid #28a745';
      feedbackText.innerHTML = '✅ <strong>Correct!</strong> Great pronunciation!';
      feedbackText.style.color = '#28a745';
      
      practiceTalkingState.score++;
      practiceTalkingState.total++;
      addQuizAttempt();
      addQuizWin();
      addSessionResult({
        vocabulary_id: currentWord?.id,
        word_hanzi: currentWord?.hanzi || '',
        word_pinyin: currentWord?.pinyin || '',
        word_english: currentWord?.english || '',
        word_french: currentWord?.french || '',
        question_type: 'speaking_' + mode,
        question_text: expectedText,
        user_answer: recognized || '',
        correct_answer: expectedText,
        is_correct: true,
        score: 100
      });
      
      // Auto-advance after 1.5 seconds
      setTimeout(() => {
        practiceTalkingState.currentIndex++;
        showNextWord();
      }, 1500);
    } else {
      feedback.style.background = 'rgba(220, 53, 69, 0.1)';
      feedback.style.border = '2px solid #dc3545';
      feedbackText.innerHTML = '❌ <strong>Try again!</strong> Listen and repeat.';
      feedbackText.style.color = '#dc3545';
      
      practiceTalkingState.total++;
      addQuizAttempt();
      const confidenceScore = Math.round((confidence || 0) * 100);
      addSessionResult({
        vocabulary_id: currentWord?.id,
        word_hanzi: currentWord?.hanzi || '',
        word_pinyin: currentWord?.pinyin || '',
        word_english: currentWord?.english || '',
        word_french: currentWord?.french || '',
        question_type: 'speaking_' + mode,
        question_text: expectedText,
        user_answer: recognized || '',
        correct_answer: expectedText,
        is_correct: false,
        score: confidenceScore
      });
    }

    if (!customMessage) {
      const confidencePercent = Math.round((confidence || 0) * 100);
      recognizedText.textContent = `You said: "${recognized}" (${confidencePercent}% confidence)`;
    }
    
    // Update progress
    document.getElementById('talkingScore').textContent = practiceTalkingState.score;
    document.getElementById('talkingTotal').textContent = practiceTalkingState.total;
  }

  function skipCurrentWord() {
    // Get current word for result tracking
    const currentWord = practiceTalkingState.words[practiceTalkingState.currentIndex];
    const lang = practiceTalkingState.language;
    const mode = practiceTalkingState.mode;
    let expectedText = '';
    if (mode === 'words') {
      expectedText = lang === 'chinese' ? currentWord.hanzi : currentWord.french;
    } else {
      expectedText = lang === 'chinese' ? currentWord.sent_hanzi : currentWord.sent_french;
    }
    
    practiceTalkingState.total++;
    addQuizAttempt();
    addSessionResult({
      vocabulary_id: currentWord?.id,
      word_hanzi: currentWord?.hanzi || '',
      word_pinyin: currentWord?.pinyin || '',
      word_english: currentWord?.english || '',
      word_french: currentWord?.french || '',
      question_type: 'speaking_' + mode,
      question_text: expectedText,
      user_answer: '(skipped)',
      correct_answer: expectedText,
      is_correct: false,
      score: 0
    });
    
    practiceTalkingState.currentIndex++;
    showNextWord();
  }

  function showCompletionMessage() {
    const score = sessionScore;
    const total = sessionTotal;
    const percentage = total > 0 ? Math.round((score / total) * 100) : 0;
    
    // Save speaking practice score using unified system
    savePracticeScore();

    // Hide practice section, show results section
    const practiceSection = document.getElementById('talkingPracticeSection');
    const resultsSection = document.getElementById('talkingResultsSection');
    if (practiceSection) practiceSection.style.display = 'none';
    if (resultsSection) {
      resultsSection.style.display = 'block';
      
      // Hide individual buttons
      const recordBtn = document.getElementById('talkingRecordBtn');
      const skipBtn = document.getElementById('talkingSkipBtn');
      const playBtn = document.getElementById('talkingPlayBtn');
      if (recordBtn) recordBtn.style.display = 'none';
      if (skipBtn) skipBtn.style.display = 'none';
      if (playBtn) playBtn.style.display = 'none';
      
      // Update score and accuracy displays
      const scoreEl = document.getElementById('talkingResultsScore');
      const accuracyEl = document.getElementById('talkingResultsAccuracy');
      if (scoreEl) scoreEl.textContent = `${score}/${total}`;
      if (accuracyEl) accuracyEl.textContent = `${percentage}%`;
      
      // Build review from sessionResults
      const reviewEl = document.getElementById('talkingResultsReview');
      if (reviewEl) {
        let reviewHtml = '';
        if (sessionResults && sessionResults.length > 0) {
          reviewHtml = sessionResults.map((result, idx) => {
            const isCorrect = result.is_correct;
            const statusIcon = isCorrect ? '✅' : '❌';
            const statusColor = isCorrect ? '#51cf66' : '#ff6b6b';
            const scoreDisplay = result.score || 0;
            
            return `
              <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 10px; background: ${isCorrect ? '#f0fdf4' : '#fef2f2'};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <span style="font-weight: bold;">${idx + 1}. ${statusIcon}</span>
                  <span style="color: ${statusColor}; font-weight: bold;">${scoreDisplay}%</span>
                </div>
                <div style="font-size: 0.85em; color: var(--text-muted); margin-bottom: 4px;">Asked: <strong>${result.question_text || 'N/A'}</strong></div>
                <div style="font-size: 0.85em; color: var(--text-muted);">You said: <strong>${result.user_answer || '(no response)'}</strong></div>
              </div>
            `;
          }).join('');
        } else {
          reviewHtml = '<div style="text-align: center; color: var(--text-muted);">No results recorded</div>';
        }
        reviewEl.innerHTML = reviewHtml;
      }
    }
  }

  function resetSpeakingPractice() {
    practiceTalkingState.words = [];
    practiceTalkingState.currentIndex = 0;
    practiceTalkingState.score = 0;
    practiceTalkingState.total = 0;
    practiceTalkingState.currentWord = null;
    practiceTalkingState.attempts = [];
    
    // Reset session tracking
    sessionResults = [];
    sessionScore = 0;
    sessionTotal = 0;
    
    // Show config, hide practice and results
    const configSection = document.getElementById('talkingConfigSection');
    const practiceSection = document.getElementById('talkingPracticeSection');
    const resultsSection = document.getElementById('talkingResultsSection');
    if (configSection) configSection.style.display = 'block';
    if (practiceSection) practiceSection.style.display = 'none';
    if (resultsSection) resultsSection.style.display = 'none';
    
    // Hide practice buttons
    const recordBtn = document.getElementById('talkingRecordBtn');
    const skipBtn = document.getElementById('talkingSkipBtn');
    const playBtn = document.getElementById('talkingPlayBtn');
    if (recordBtn) recordBtn.style.display = 'block';  // Show again for next round
    if (skipBtn) skipBtn.style.display = 'block';
    if (playBtn) playBtn.style.display = 'block';
  }
  
  // saveSpeakingScore removed - now uses unified savePracticeScore()

  // Event listeners for Practice Talking (with safety checks)
  const startPracTalking = document.getElementById('startPracticeTalking');
  if (startPracTalking) startPracTalking.addEventListener('click', startPracticeTalkingSession);
  
  const talkingPlayBtn2 = document.getElementById('talkingPlayBtn');
  if (talkingPlayBtn2) talkingPlayBtn2.addEventListener('click', playCurrentWord);
  
  const talkingRecordBtn = document.getElementById('talkingRecordBtn');
  if (talkingRecordBtn) talkingRecordBtn.addEventListener('click', startRecording);
  
  const talkingSkipBtn = document.getElementById('talkingSkipBtn');
  if (talkingSkipBtn) talkingSkipBtn.addEventListener('click', skipCurrentWord);
  
  const talkingExitBtn2 = document.getElementById('talkingExitBtn');
  if (talkingExitBtn2) talkingExitBtn2.addEventListener('click', closePracticeTalkingModal);

  // ==================== DRAWING PRACTICE MODAL ====================
  
  const drawingPracticeState = {
    words: [],
    currentIndex: 0,
    score: 0,
    total: 0,
    currentWord: null,
    characters: [],
    currentCharIndex: 0,
    charMistakes: 0,
    currentWriter: null
  };

  function openPracticeDrawingModal() {
    resetDrawingPractice();
    // Populate categories from main sectionSelect (same as other games)
    const pdSection = document.getElementById('pd_section');
    if (pdSection && sectionSelect) {
      pdSection.innerHTML = '<option value="all">All Categories</option>';
      const options = Array.from(sectionSelect.options).slice(1);
      options.forEach(opt => {
        const newOpt = document.createElement('option');
        newOpt.value = opt.value;
        newOpt.textContent = opt.textContent;
        pdSection.appendChild(newOpt);
      });
    }
    document.getElementById('practiceDrawingModal').style.display = 'flex';
  }

  function closePracticeDrawingModal() {
    // Save score if there are any attempts before closing (but not if already at completion)
    if (drawingPracticeState.total > 0 && drawingPracticeState.currentIndex < drawingPracticeState.words.length) {
      sessionScore = drawingPracticeState.score;
      sessionTotal = drawingPracticeState.total;
      savePracticeScore();
    }
    document.getElementById('practiceDrawingModal').style.display = 'none';
    resetDrawingPractice();
  }

  function resetDrawingPractice() {
    drawingPracticeState.words = [];
    drawingPracticeState.currentIndex = 0;
    drawingPracticeState.score = 0;
    drawingPracticeState.total = 0;
    drawingPracticeState.currentWord = null;
    drawingPracticeState.characters = [];
    drawingPracticeState.currentCharIndex = 0;
    drawingPracticeState.charMistakes = 0;
    drawingPracticeState.currentWriter = null;
    
    // Reset session tracking
    sessionResults = [];
    sessionScore = 0;
    sessionTotal = 0;
    
    // Show config, hide practice and results
    document.getElementById('drawingConfigSection').style.display = 'block';
    document.getElementById('drawingPracticeSection').style.display = 'none';
    const resultsSection = document.getElementById('drawingResultsSection');
    if (resultsSection) resultsSection.style.display = 'none';
    document.getElementById('drawingCanvasContainer').innerHTML = '';
  }

  async function startDrawingPractice() {
    const section = document.getElementById('pd_section').value || 'all';
    const count = parseInt(document.getElementById('pd_count').value) || 10;

    // Start unified practice session tracking
    startPracticeSession('drawing');
    sessionTargetRounds = count;  // Set target rounds
    drawingPracticeState.score = 0;
    drawingPracticeState.total = 0;

    try {
      const response = await fetch(`/random_words?section=${encodeURIComponent(section)}&limit=${count}`);
      if (!response.ok) throw new Error('Failed to fetch words');
      const words = await response.json();

      // Filter to only words with hanzi characters
      const validWords = words.filter(w => w.hanzi && w.hanzi.trim().length > 0);

      if (!validWords || validWords.length === 0) {
        showToast('No Chinese words found for this category', 'error');
        return;
      }

      drawingPracticeState.words = validWords;
      drawingPracticeState.currentIndex = 0;

      document.getElementById('drawingConfigSection').style.display = 'none';
      document.getElementById('drawingPracticeSection').style.display = 'block';
      
      showNextDrawingWord();
    } catch (err) {
      console.error('Error starting drawing practice:', err);
      showToast('Error loading words. Please try again.', 'error');
    }
  }

  function showNextDrawingWord() {
    // Check if we've reached target rounds
    if (sessionTargetRounds > 0 && sessionTotal >= sessionTargetRounds) {
      showDrawingCompletion();
      return;
    }
    
    if (drawingPracticeState.currentIndex >= drawingPracticeState.words.length) {
      showDrawingCompletion();
      return;
    }

    const word = drawingPracticeState.words[drawingPracticeState.currentIndex];
    drawingPracticeState.currentWord = word;
    drawingPracticeState.characters = word.hanzi.split('');
    drawingPracticeState.currentCharIndex = 0;
    
    // Update UI
    document.getElementById('drawingEnglish').textContent = word.english || '';
    document.getElementById('drawingPinyin').textContent = word.pinyin || '';
    document.getElementById('drawingCurrent').textContent = drawingPracticeState.currentIndex + 1;
    document.getElementById('drawingTotal').textContent = drawingPracticeState.words.length;
    document.getElementById('drawingScore').textContent = drawingPracticeState.score;
    document.getElementById('drawingCharTotal').textContent = drawingPracticeState.characters.length;
    
    // Show first character
    showDrawingCharacter(0);
  }

  function showDrawingCharacter(charIndex) {
    const characters = drawingPracticeState.characters;
    if (charIndex >= characters.length) {
      // Word complete, move to next word
      drawingPracticeState.currentIndex++;
      setTimeout(() => showNextDrawingWord(), 500);
      return;
    }

    drawingPracticeState.currentCharIndex = charIndex;
    drawingPracticeState.charMistakes = 0;
    
    // Update character progress
    document.getElementById('drawingCharCurrent').textContent = charIndex + 1;
    
    const container = document.getElementById('drawingCanvasContainer');
    container.innerHTML = '';
    
    const char = characters[charIndex];
    const charDiv = document.createElement('div');
    charDiv.style.cssText = 'width:250px; height:250px; border:2px solid var(--border-color); border-radius:12px; background:white;';
    charDiv.id = 'drawChar_current';
    container.appendChild(charDiv);

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
        drawingPracticeState.total++;
        sessionTotal = drawingPracticeState.total;
        
        writer.quiz({
          showHintAfterMisses: 3,
          onMistake: () => {
            drawingPracticeState.charMistakes++;
          },
          onComplete: () => {
            const isCorrect = drawingPracticeState.charMistakes <= 1;
            if (isCorrect) {
              drawingPracticeState.score++;
              sessionScore = drawingPracticeState.score;
            }
            
            // Track result for this character
            const word = drawingPracticeState.currentWord || {};
            addSessionResult({
              vocabulary_id: word.id || null,
              word_hanzi: word.hanzi || char,
              word_pinyin: word.pinyin || '',
              word_english: word.english || '',
              word_french: word.french || '',
              question_type: 'drawing',
              question_text: `Draw: ${char} (${word.pinyin || ''})`,
              user_answer: isCorrect ? 'Drawn correctly' : `${drawingPracticeState.charMistakes} mistakes`,
              correct_answer: `Draw: ${char}`,
              is_correct: isCorrect,
              score: isCorrect ? 100 : 0
            });
            
            // Update score display
            document.getElementById('drawingScore').textContent = drawingPracticeState.score;
            
            // Move to next character
            setTimeout(() => showDrawingCharacter(charIndex + 1), 400);
          }
        });
      },
      onLoadCharDataError: function() {
        console.error('Failed to load character:', char);
        // Skip this character
        setTimeout(() => showDrawingCharacter(charIndex + 1), 400);
      }
    });
    
    drawingPracticeState.currentWriter = writer;
  }

  function skipDrawingWord() {
    // Mark remaining characters as skipped
    const word = drawingPracticeState.currentWord;
    if (word) {
      const characters = drawingPracticeState.characters;
      for (let i = drawingPracticeState.currentCharIndex; i < characters.length; i++) {
        const char = characters[i];
        drawingPracticeState.total++;
        
        // Track skipped character as incorrect
        addSessionResult({
          vocabulary_id: word.id || null,
          word_hanzi: word.hanzi || char,
          word_pinyin: word.pinyin || '',
          word_english: word.english || '',
          word_french: word.french || '',
          question_type: 'drawing',
          question_text: `Draw: ${char} (${word.pinyin || ''})`,
          user_answer: '(skipped)',
          correct_answer: `Draw: ${char}`,
          is_correct: false,
          score: 0
        });
      }
      sessionTotal = drawingPracticeState.total;
    }
    
    drawingPracticeState.currentIndex++;
    showNextDrawingWord();
  }

  function showDrawingCompletion() {
    const score = sessionScore;
    const total = sessionTotal;
    const percentage = total > 0 ? Math.round((score / total) * 100) : 0;
    
    // Save practice score
    savePracticeScore();

    // Hide practice section, show results section
    const practiceSection = document.getElementById('drawingPracticeSection');
    const resultsSection = document.getElementById('drawingResultsSection');
    if (practiceSection) practiceSection.style.display = 'none';
    if (resultsSection) {
      resultsSection.style.display = 'block';
      
      // Update score and accuracy displays
      const scoreEl = document.getElementById('drawingResultsScore');
      const accuracyEl = document.getElementById('drawingResultsAccuracy');
      if (scoreEl) scoreEl.textContent = `${score}/${total}`;
      if (accuracyEl) accuracyEl.textContent = `${percentage}%`;
      
      // Build review from sessionResults
      const reviewEl = document.getElementById('drawingResultsReview');
      if (reviewEl) {
        let reviewHtml = '';
        if (sessionResults && sessionResults.length > 0) {
          reviewHtml = sessionResults.map((result, idx) => {
            const isCorrect = result.is_correct;
            const statusIcon = isCorrect ? '✅' : '❌';
            const statusColor = isCorrect ? '#51cf66' : '#ff6b6b';
            const scoreDisplay = result.score || 0;
            
            return `
              <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 10px; background: ${isCorrect ? '#f0fdf4' : '#fef2f2'};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <span style="font-weight: bold;">${idx + 1}. ${statusIcon}</span>
                  <span style="color: ${statusColor}; font-weight: bold;">${scoreDisplay}%</span>
                </div>
                <div style="font-size: 0.85em; color: var(--text-muted);">Draw: <strong>${result.question_text || 'N/A'}</strong></div>
              </div>
            `;
          }).join('');
        } else {
          reviewHtml = '<div style="text-align: center; color: var(--text-muted);">No results recorded</div>';
        }
        reviewEl.innerHTML = reviewHtml;
      }
    }
  }

  // Event listeners for Drawing practice
  // Event listeners for Drawing practice (with safety checks)
  const startPracDrawing = document.getElementById('startPracticeDrawing');
  if (startPracDrawing) startPracDrawing.addEventListener('click', startDrawingPractice);
  
  const drawingSkipBtn = document.getElementById('drawingSkipBtn');
  if (drawingSkipBtn) drawingSkipBtn.addEventListener('click', skipDrawingWord);
  
  const drawingExitBtn = document.getElementById('drawingExitBtn');
  if (drawingExitBtn) drawingExitBtn.addEventListener('click', closePracticeDrawingModal);

  // ==================== MY SCORES MODAL ====================
  
  function openScoresModal() {
    document.getElementById('scoresModal').style.display = 'flex';
    loadScores();
  }
  
  function closeScoresModal() {
    document.getElementById('scoresModal').style.display = 'none';
  }
  
  async function resetMyScores() {
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
      alert(`✅ Reset complete! Deleted ${result.deleted_count} practice scores.`);
      
      // Reload the scores display
      loadScores();
    } catch (error) {
      console.error('Error resetting scores:', error);
      alert('Error resetting scores: ' + error.message);
    }
  }
  
  async function loadScores() {
    const loading = document.getElementById('scoresLoading');
    const content = document.getElementById('scoresContent');
    const empty = document.getElementById('scoresEmpty');
    
    loading.style.display = 'block';
    content.style.display = 'none';
    empty.style.display = 'none';
    
    try {
      // Fetch stats and history in parallel
      const [statsRes, historyRes] = await Promise.all([
        fetch('/api/user/practice/stats'),
        fetch('/api/user/practice/history?limit=10')
      ]);
      
      const stats = await statsRes.json();
      const history = await historyRes.json();
      
      if (statsRes.status === 401 || historyRes.status === 401) {
        loading.style.display = 'none';
        empty.style.display = 'block';
        empty.innerHTML = '<p style="font-size: 1.1em;">Please log in to save your scores.</p>';
        return;
      }
      
      // Check if there are any games played
      const totalGames = (stats.listening?.total_games || 0) + 
                         (stats.words?.total_games || 0) + 
                         (stats.speaking?.total_games || 0) +
                         (stats.drawing?.total_games || 0);
      
      if (totalGames === 0) {
        loading.style.display = 'none';
        empty.style.display = 'block';
        document.getElementById('resetScoresBtn').style.display = 'none';
        return;
      }
      
      // Show reset button when there are scores
      document.getElementById('resetScoresBtn').style.display = 'inline-block';
      
      // Populate stats table
      const statsBody = document.getElementById('scoresStatsBody');
      statsBody.innerHTML = `
        <tr>
          <td style="padding: 10px; border: 1px solid var(--border-color);">👂 Listening</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.listening?.total_games || 0}</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.listening?.average_percentage || 0}%</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.listening?.best_score || 0}%</td>
        </tr>
        <tr>
          <td style="padding: 10px; border: 1px solid var(--border-color);">📝 Words</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.words?.total_games || 0}</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.words?.average_percentage || 0}%</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.words?.best_score || 0}%</td>
        </tr>
        <tr>
          <td style="padding: 10px; border: 1px solid var(--border-color);">🎤 Speaking</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.speaking?.total_games || 0}</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.speaking?.average_percentage || 0}%</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.speaking?.best_score || 0}%</td>
        </tr>
        <tr>
          <td style="padding: 10px; border: 1px solid var(--border-color);">✍️ Drawing</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.drawing?.total_games || 0}</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.drawing?.average_percentage || 0}%</td>
          <td style="padding: 10px; text-align: center; border: 1px solid var(--border-color);">${stats.drawing?.best_score || 0}%</td>
        </tr>
      `;
      
      // Populate recent games
      const recentList = document.getElementById('scoresRecentList');
      if (history.length === 0) {
        recentList.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No recent games</p>';
      } else {
        recentList.innerHTML = history.map(game => {
          const gameIcon = game.game_type === 'words' ? '📝' : 
                          game.game_type === 'speaking' ? '🎤' : 
                          game.game_type === 'drawing' ? '✍️' : '👂';
          const gameLabel = game.game_type.charAt(0).toUpperCase() + game.game_type.slice(1);
          const date = game.played_at ? new Date(game.played_at).toLocaleDateString() : 'Unknown';
          const time = game.played_at ? new Date(game.played_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '';
          const scoreColor = game.percentage >= 80 ? '#51cf66' : 
                            game.percentage >= 60 ? '#fcc419' : '#ff6b6b';
          
          return `
            <div onclick="openGameDetailsModal(${game.id})" style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid var(--border-color); cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='var(--card-bg)'" onmouseout="this.style.background='transparent'">
              <div>
                <span style="font-size: 1.1em;">${gameIcon} ${gameLabel}</span>
                <span style="color: var(--text-muted); font-size: 0.85em; margin-left: 10px;">${date} ${time}</span>
              </div>
              <div style="text-align: right; display: flex; align-items: center; gap: 8px;">
                <span style="font-weight: 600; color: ${scoreColor};">${game.percentage || 0}%</span>
                <span style="color: var(--text-muted); font-size: 0.85em;">(${game.score}/${game.total_questions})</span>
                <span style="color: var(--text-muted); font-size: 0.9em;">→</span>
              </div>
            </div>
          `;
        }).join('');
      }
      
      loading.style.display = 'none';
      content.style.display = 'block';
      
    } catch (error) {
      console.error('Error loading scores:', error);
      loading.style.display = 'none';
      empty.style.display = 'block';
      empty.innerHTML = '<p style="font-size: 1.1em;">Error loading scores.</p><p style="color: var(--text-muted);">Please try again.</p>';
      document.getElementById('resetScoresBtn').style.display = 'none';
    }
  }
  
  // ==================== GAME DETAILS MODAL ====================
  
  function openGameDetailsModal(gameId) {
    document.getElementById('gameDetailsModal').style.display = 'flex';
    loadGameDetails(gameId);
  }
  
  function closeGameDetailsModal() {
    document.getElementById('gameDetailsModal').style.display = 'none';
  }
  
  async function loadGameDetails(gameId) {
    const loading = document.getElementById('gameDetailsLoading');
    const content = document.getElementById('gameDetailsContent');
    const summary = document.getElementById('gameDetailsSummary');
    const results = document.getElementById('gameDetailsResults');
    const resultsList = document.getElementById('gameDetailsResultsList');
    const empty = document.getElementById('gameDetailsEmpty');
    
    loading.style.display = 'block';
    content.style.display = 'none';
    
    try {
      const response = await fetch(`/api/user/practice/${gameId}/details`);
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
      document.getElementById('gameDetailsTitle').textContent = `${gameIcon} ${gameLabel} Results`;
      
      // Show summary
      summary.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
          <div>
            <div style="font-size: 1.3em; font-weight: 600; color: ${scoreColor};">${data.percentage || 0}%</div>
            <div style="color: var(--text-muted); font-size: 0.9em;">${data.score}/${data.total_questions} correct</div>
          </div>
          <div style="text-align: right;">
            <div style="color: var(--text-muted); font-size: 0.9em;">${date}</div>
            <div style="color: var(--text-muted); font-size: 0.85em;">${time}</div>
          </div>
        </div>
      `;
      
      // Show results or empty state
      if (data.results && data.results.length > 0) {
        results.style.display = 'block';
        empty.style.display = 'none';
        
        resultsList.innerHTML = data.results.map((r, idx) => {
          const statusIcon = r.is_correct ? '✅' : '❌';
          const statusColor = r.is_correct ? '#51cf66' : '#ff6b6b';
          
          return `
            <div style="padding: 12px; margin-bottom: 10px; background: var(--card-bg); border-radius: 8px; border-left: 4px solid ${statusColor};">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <div style="font-weight: 600;">${statusIcon} Question ${r.question_number}</div>
                ${r.word_hanzi ? `<div style="font-size: 1.2em;">${r.word_hanzi}</div>` : ''}
              </div>
              ${r.word_pinyin ? `<div style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 4px;">${r.word_pinyin}</div>` : ''}
              ${r.word_english ? `<div style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 8px;">${r.word_english}</div>` : ''}
              
              ${!r.is_correct ? `
                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border-color);">
                  <div style="font-size: 0.85em; margin-bottom: 4px;">
                    <span style="color: var(--text-muted);">Your answer:</span> 
                    <span style="color: #ff6b6b;">${r.user_answer || 'No answer'}</span>
                  </div>
                  <div style="font-size: 0.85em; margin-bottom: 8px;">
                    <span style="color: var(--text-muted);">Correct answer:</span> 
                    <span style="color: #51cf66;">${r.correct_answer || 'N/A'}</span>
                  </div>
                  ${r.feedback ? `
                    <div style="margin-top: 8px; padding: 10px; background: rgba(255, 193, 7, 0.1); border-radius: 6px; font-size: 0.9em;">
                      <div style="font-weight: 600; margin-bottom: 4px;">💡 AI Tip:</div>
                      ${r.feedback}
                    </div>
                  ` : `
                    <button onclick="requestFeedback(${gameId}, ${r.question_number}, this)" class="secondary" style="padding: 6px 12px; font-size: 0.85em; margin-top: 4px;">
                      💡 Get AI Tips
                    </button>
                  `}
                </div>
              ` : ''}
            </div>
          `;
        }).join('');
      } else {
        results.style.display = 'none';
        empty.style.display = 'block';
      }
      
      loading.style.display = 'none';
      content.style.display = 'block';
      
    } catch (error) {
      console.error('Error loading game details:', error);
      loading.style.display = 'none';
      content.style.display = 'block';
      summary.innerHTML = '<p style="color: var(--text-muted);">Error loading game details.</p>';
      results.style.display = 'none';
      empty.style.display = 'none';
    }
  }
  
  async function requestFeedback(gameId, questionNumber, buttonEl) {
    buttonEl.disabled = true;
    buttonEl.textContent = '⏳ Loading...';
    
    try {
      // First get the details to find this question
      const detailsRes = await fetch(`/api/user/practice/${gameId}/details`);
      const details = await detailsRes.json();
      
      const question = details.results.find(r => r.question_number === questionNumber);
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
        const feedbackHtml = `
          <div style="margin-top: 8px; padding: 10px; background: rgba(255, 193, 7, 0.1); border-radius: 6px; font-size: 0.9em;">
            <div style="font-weight: 600; margin-bottom: 4px;">💡 AI Tip: ${data.cached ? '(cached)' : ''}</div>
            ${data.feedback}
          </div>
        `;
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

  // ==================== USER AUTHENTICATION & ONBOARDING ====================

  // Handle clicks on disabled (login-required) buttons
  function handleDisabledClick(event, wrapper) {
    if (wrapper.classList.contains('disabled')) {
      event.preventDefault();
      event.stopPropagation();
      // Redirect to Google login, then return to this page
      window.location.href = '/auth/google?next=' + encodeURIComponent(window.location.pathname);
    }
  }

  // Check user authentication on page load
  let currentUser = null;

  async function checkUserAuth() {
    try {
      const response = await fetch('/api/user/check');
      const data = await response.json();
      
      // Get elements that require login
      const addWordsWrapper = document.getElementById('addWordsWrapper');
      const speakingWrapper = document.getElementById('speakingWrapper');
      
      if (data.authenticated) {
        currentUser = data;
        // Update UI
        document.getElementById('userGreeting').style.display = 'block';
        document.getElementById('userFirstName').textContent = data.first_name;
        document.getElementById('loginLink').style.display = 'none';
        document.getElementById('logoutLink').style.display = 'inline-block';
        document.getElementById('preferencesLink').style.display = 'inline-block';
        document.getElementById('myScoresLink').style.display = 'inline-block';
        
        // Enable login-required features
        if (addWordsWrapper) addWordsWrapper.classList.remove('disabled');
        if (speakingWrapper) speakingWrapper.classList.remove('disabled');
        
        if (data.is_admin) {
          document.getElementById('adminLink').style.display = 'inline-block';
        }

        await syncLanguageSettingsFromServer();
        
        // Show onboarding modal if not onboarded
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('onboarding') === 'true' && !data.is_onboarded) {
          showOnboardingModal();
        }
      } else {
        // User not logged in - show login button
        document.getElementById('loginLink').style.display = 'inline-block';
        document.getElementById('logoutLink').style.display = 'none';
        document.getElementById('adminLink').style.display = 'none';
        document.getElementById('preferencesLink').style.display = 'none';
        document.getElementById('myScoresLink').style.display = 'none';
        document.getElementById('userGreeting').style.display = 'none';
        
        // Disable login-required features
        if (addWordsWrapper) addWordsWrapper.classList.add('disabled');
        if (speakingWrapper) speakingWrapper.classList.add('disabled');
      }
    } catch (error) {
      console.error('Error checking auth:', error);
    }
  }

  async function showOnboardingModal() {
    const modal = document.getElementById('onboardingModal');
    modal.style.display = 'flex';
    
    // Load available categories
    try {
      const response = await fetch('/api/user/sections');
      const sections = await response.json();
      
      const categoryList = document.getElementById('categoryList');
      if (sections.length === 0) {
        categoryList.innerHTML = '<p style="text-align: center; color: var(--text-muted);">No categories available yet.</p>';
      } else {
        categoryList.innerHTML = sections.map(s => `
          <label style="display: flex; align-items: center; padding: 12px; border-radius: 6px; cursor: pointer; margin-bottom: 8px; background: var(--card-bg);" onmouseover="this.style.background='var(--hover-bg)'" onmouseout="this.style.background='var(--card-bg)'">
            <input type="checkbox" value="${s.name}" style="margin-right: 12px; width: 18px; height: 18px; cursor: pointer;">
            <span style="flex: 1; color: var(--text-main);">${s.name}</span>
            <span style="color: var(--text-muted); font-size: 0.9em;">${s.count} words</span>
          </label>
        `).join('');
      }
    } catch (error) {
      console.error('Error loading sections:', error);
      document.getElementById('categoryList').innerHTML = '<p style="color: #ff6b6b;">Error loading categories.</p>';
    }
  }

  // Start fresh - complete onboarding with no imports
  document.getElementById('startFreshBtn').addEventListener('click', async () => {
    try {
      const response = await fetch('/api/user/onboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sections: [] })
      });
      const data = await response.json();
      
      if (data.success) {
        document.getElementById('onboardingModal').style.display = 'none';
        showToast('🎉 Welcome! Start adding your first words!', 'success');
        setTimeout(() => {
          window.location.href = '/';
        }, 1000);
      }
    } catch (error) {
      console.error('Error:', error);
      showToast('Error completing setup', 'error');
    }
  });

  // Show import section
  document.getElementById('showImportBtn').addEventListener('click', () => {
    document.getElementById('importSection').style.display = 'block';
    document.getElementById('showImportBtn').style.display = 'none';
  });

  // Select all categories
  document.getElementById('selectAllBtn').addEventListener('click', () => {
    document.querySelectorAll('#categoryList input[type="checkbox"]').forEach(cb => cb.checked = true);
  });

  // Deselect all categories
  document.getElementById('deselectAllBtn').addEventListener('click', () => {
    document.querySelectorAll('#categoryList input[type="checkbox"]').forEach(cb => cb.checked = false);
  });

  // Import selected categories
  document.getElementById('importSelectedBtn').addEventListener('click', async () => {
    const checkboxes = document.querySelectorAll('#categoryList input[type="checkbox"]:checked');
    const selectedSections = Array.from(checkboxes).map(cb => cb.value);
    
    if (selectedSections.length === 0) {
      showToast('Please select at least one category', 'error');
      return;
    }
    
    try {
      const response = await fetch('/api/user/onboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sections: selectedSections })
      });
      const data = await response.json();
      
      if (data.success) {
        document.getElementById('onboardingModal').style.display = 'none';
        showToast(data.message, 'success');
        setTimeout(() => {
          window.location.href = '/';
        }, 1500);
      }
    } catch (error) {
      console.error('Error:', error);
      showToast('Error saving visible categories', 'error');
    }
  });

  // Check auth on page load
  checkUserAuth();

  // Register menu event listeners (after all functions are defined)

  // Example: get enabled languages from user preferences (replace with real logic)
  function getEnabledLanguages() {
    // Return the enabled languages based on current settings
    const enabled = [];
    if (langSettings.chinese) enabled.push('chinese');
    if (langSettings.japanese) enabled.push('japanese');
    if (langSettings.french) enabled.push('french');
    return enabled.length ? enabled : ['chinese'];
  }

  document.getElementById('menuPracticeWords').addEventListener('click', () => {
    document.getElementById('hamburgerMenu').classList.remove('show');
    document.getElementById('practiceSubmenu').classList.remove('show');
    document.getElementById('addWordsSubmenu').classList.remove('show');
    updatePracticeLanguageSelectors(getEnabledLanguages());
    openPracticeWordsModal();
  });

  document.getElementById('menuPracticeListening').addEventListener('click', () => {
    document.getElementById('hamburgerMenu').classList.remove('show');
    document.getElementById('practiceSubmenu').classList.remove('show');
    document.getElementById('addWordsSubmenu').classList.remove('show');
    updatePracticeLanguageSelectors(getEnabledLanguages());
    openPracticeListeningModal();
  });

  document.getElementById('menuPracticeTalking').addEventListener('click', () => {
    document.getElementById('hamburgerMenu').classList.remove('show');
    document.getElementById('practiceSubmenu').classList.remove('show');
    document.getElementById('addWordsSubmenu').classList.remove('show');
    updatePracticeLanguageSelectors(getEnabledLanguages());
    openPracticeTalkingModal();
  });

  document.getElementById('menuPracticeDrawing').addEventListener('click', () => {
    document.getElementById('hamburgerMenu').classList.remove('show');
    document.getElementById('practiceSubmenu').classList.remove('show');
    document.getElementById('addWordsSubmenu').classList.remove('show');
    openPracticeDrawingModal();
  });

