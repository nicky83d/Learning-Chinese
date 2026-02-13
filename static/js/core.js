/**
 * Core utilities shared across all modules
 * This file should be loaded before game modules
 */

// ==================== SESSION TRACKING ====================
window.VocabApp = window.VocabApp || {};

VocabApp.session = {
  score: 0,
  total: 0,
  startTime: null,
  gameType: null, // 'listening', 'words', 'speaking', 'drawing'
  results: []
};

VocabApp.startPracticeSession = function(gameType) {
  console.log('startPracticeSession:', gameType);
  VocabApp.session.score = 0;
  VocabApp.session.total = 0;
  VocabApp.session.startTime = Date.now();
  VocabApp.session.gameType = gameType;
  VocabApp.session.results = [];
};

VocabApp.addSessionResult = function(result) {
  VocabApp.session.results.push({
    ...result,
    question_number: VocabApp.session.results.length + 1
  });
};

VocabApp.savePracticeScore = async function() {
  const session = VocabApp.session;
  console.log('savePracticeScore called:', { 
    gameType: session.gameType, 
    score: session.score, 
    total: session.total, 
    resultsCount: session.results.length 
  });
  
  if (!session.gameType || session.total === 0) {
    console.log('Skipping save - no game type or zero total');
    return null;
  }
  
  const duration = session.startTime ? Math.round((Date.now() - session.startTime) / 1000) : 0;
  
  try {
    const payload = {
      game_type: session.gameType,
      score: session.score,
      total_questions: session.total,
      duration: duration,
      results: session.results
    };
    console.log('Saving practice score:', payload);
    
    const response = await fetch('/api/user/practice/save', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    
    const data = await response.json();
    if (data.error) {
      console.error('Server error saving score:', data.error);
      return null;
    }
    console.log('Practice score saved successfully, id:', data.id);
    return data.id;
  } catch (e) {
    console.error('Could not save practice score:', e);
    return null;
  }
};

// ==================== LANGUAGE SETTINGS ====================
VocabApp.getLanguageSettings = function() {
  const settings = JSON.parse(localStorage.getItem('languageSettings') || '{}');
  return {
    chinese: settings.chinese !== false,
    japanese: settings.japanese === true,
    french: settings.french === true
  };
};

VocabApp.langSettings = VocabApp.getLanguageSettings();

// Listen for language settings changes
window.addEventListener('storage', (e) => {
  if (e.key === 'languageSettings') {
    VocabApp.langSettings = VocabApp.getLanguageSettings();
  }
});

// ==================== TOAST NOTIFICATIONS ====================
VocabApp.showToast = function(message, type = 'success', persist = false, duration = 6000) {
  const toast = document.getElementById('uploadToast');
  const content = document.getElementById('toastContent');
  if (!toast || !content) return;
  
  content.innerHTML = message;
  toast.className = `show ${type}`;
  
  if (!persist) {
    setTimeout(() => {
      toast.classList.remove('show');
    }, duration);
  }
};

// ==================== SPEECH SYNTHESIS ====================
let voicesLoaded = false;
if (window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => { voicesLoaded = true; };
}

VocabApp.speak = function(text, lang = 'zh-CN') {
  if (!text || text.trim() === '' || !window.speechSynthesis) return;
  
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
};

VocabApp.speakAsync = function(text, lang) {
  return new Promise((resolve) => {
    if (!window.speechSynthesis || !text) {
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
};

// ==================== THEME ====================
VocabApp.initTheme = function() {
  const themeBtn = document.getElementById('themeBtn');
  if (!themeBtn) return;
  
  function updateThemeButton(theme) {
    themeBtn.textContent = theme === 'dark' ? '☀️ Light Mode' : '🌓 Dark Mode';
  }
  
  themeBtn.onclick = () => {
    const next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeButton(next);
  };
  
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeButton(savedTheme);
  
  // Listen for theme changes from other pages/tabs
  window.addEventListener('storage', (e) => {
    if (e.key === 'theme') {
      const newTheme = e.newValue || 'light';
      document.documentElement.setAttribute('data-theme', newTheme);
      updateThemeButton(newTheme);
    }
  });
  
  // Listen for language settings changes from preferences page
  window.addEventListener('storage', (e) => {
    if (e.key === 'languageSettings') {
      VocabApp.langSettings = VocabApp.getLanguageSettings();
    }
  });
};

// ==================== UTILITIES ====================
VocabApp.sleep = function(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Helper to populate section dropdowns from main filter
VocabApp.populateSectionDropdown = function(selectId, sourceSelect) {
  const targetSelect = document.getElementById(selectId);
  if (!targetSelect || !sourceSelect) return;
  
  targetSelect.innerHTML = '<option value="all">All Categories</option>';
  const options = Array.from(sourceSelect.options).slice(1);
  options.forEach(opt => {
    const newOpt = document.createElement('option');
    newOpt.value = opt.value;
    newOpt.textContent = opt.textContent;
    targetSelect.appendChild(newOpt);
  });
};

// Initialize theme on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    VocabApp.initTheme();
  });
} else {
  VocabApp.initTheme();
}

console.log('VocabApp core loaded');
