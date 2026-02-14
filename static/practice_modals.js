// practice_modals.js
// Hide language selection if only one non-English language is enabled
function updatePracticeLanguageSelectors(enabledLangs) {
  // enabledLangs: array of non-English languages enabled, e.g. ['chinese'], ['chinese','french']
  // Hide language selection unless 2 or more enabled non-English languages
  // Practice Words
  const pwLangArea = document.getElementById('pw_lang_select_area');
  if (pwLangArea) {
    if (enabledLangs.length < 2) {
      pwLangArea.style.display = 'none';
      if (enabledLangs.length === 1) {
        document.querySelector('input[name="pw_lang"][value="'+enabledLangs[0]+'"]').checked = true;
      }
    } else {
      pwLangArea.style.display = '';
    }
  }
  // Practice Listening
  const plLangArea = document.getElementById('pl_lang_options');
  if (plLangArea) {
    if (enabledLangs.length < 2) {
      plLangArea.parentElement.style.display = 'none';
      if (enabledLangs.length === 1) {
        document.querySelector('input[name="pl_lang"][value="'+enabledLangs[0]+'"]').checked = true;
      }
    } else {
      plLangArea.parentElement.style.display = '';
    }
  }
  // Practice Speaking
  const ptLangArea = document.getElementById('pt_lang_options');
  if (ptLangArea) {
    if (enabledLangs.length < 2) {
      ptLangArea.parentElement.style.display = 'none';
      if (enabledLangs.length === 1) {
        document.querySelector('input[name="pt_lang"][value="'+enabledLangs[0]+'"]').checked = true;
      }
    } else {
      ptLangArea.parentElement.style.display = '';
    }
  }
}
// Example usage: updatePracticeLanguageSelectors(['chinese']);
