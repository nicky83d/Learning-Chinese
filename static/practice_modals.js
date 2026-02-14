// practice_modals.js
// Hide language selection if only one non-English language is enabled
function updatePracticeLanguageSelectors(enabledLangs) {
  console.log('updatePracticeLanguageSelectors called with:', enabledLangs);
  // enabledLangs: array of non-English languages enabled, e.g. ['chinese'], ['chinese','french']
  // Hide language selection unless 2 or more enabled non-English languages
  // Practice Words
  const pwLangArea = document.getElementById('pw_lang_select_area');
  if (pwLangArea) {
    if (enabledLangs.length >= 2) {
      pwLangArea.style.display = '';
    } else {
      pwLangArea.style.display = 'none';
      if (enabledLangs.length === 1) {
        document.querySelector('input[name="pw_lang"][value="'+enabledLangs[0]+'"]').checked = true;
      }
    }
  }
  // Practice Listening
  const plLangArea = document.getElementById('pl_lang_options');
  if (plLangArea) {
    if (enabledLangs.length >= 2) {
      plLangArea.parentElement.style.display = '';
    } else {
      plLangArea.parentElement.style.display = 'none';
      if (enabledLangs.length === 1) {
        document.querySelector('input[name="pl_lang"][value="'+enabledLangs[0]+'"]').checked = true;
      }
    }
  }
  // Practice Speaking
  const ptLangArea = document.getElementById('pt_lang_options');
  if (ptLangArea) {
    if (enabledLangs.length >= 2) {
      ptLangArea.parentElement.style.display = '';
    } else {
      ptLangArea.parentElement.style.display = 'none';
      if (enabledLangs.length === 1) {
        document.querySelector('input[name="pt_lang"][value="'+enabledLangs[0]+'"]').checked = true;
      }
    }
  }
}
// Example usage: updatePracticeLanguageSelectors(['chinese']);
