// Options page script for Anti Spam
// Will use chrome.storage.sync or chrome.storage.local to persist settings

function loadSettings() {
  const serverInput = document.getElementById('serverUrl');
  const autoSendInput = document.getElementById('autoSend');
  if (!window.AntiSpamStorage) return;
  window.AntiSpamStorage.getSettings().then((s) => {
    if (serverInput) serverInput.value = s.serverUrl || '';
    if (autoSendInput) autoSendInput.checked = !!s.autoSend;
  }).catch((e) => console.warn('loadSettings error:', e));
}

function saveSettings() {
  const serverInput = document.getElementById('serverUrl');
  const autoSendInput = document.getElementById('autoSend');
  const settings = {
    serverUrl: serverInput ? serverInput.value.trim() : '',
    autoSend: autoSendInput ? !!autoSendInput.checked : false
  };
  if (!window.AntiSpamStorage) return;
  window.AntiSpamStorage.saveSettings(settings).then(() => {
    // feedback
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
      saveBtn.textContent = 'Saved';
      setTimeout(() => (saveBtn.textContent = 'Save'), 1200);
    }
  }).catch((e) => {
    console.warn('saveSettings error:', e);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const saveBtn = document.getElementById('save-btn');
  if (saveBtn) saveBtn.addEventListener('click', saveSettings);

  // Load settings initially
  loadSettings();
});
