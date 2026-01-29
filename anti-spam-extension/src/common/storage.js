// Storage helper for Anti Spam extension
// Wraps chrome.storage API for settings persistence

/**
 * Get extension settings from chrome.storage.
 * @returns {Promise<object>} Settings object with serverUrl and autoSend
 */
function getSettings() {
  // Read settings from chrome.storage.sync; fall back to local if necessary
  return new Promise((resolve) => {
    try {
      chrome.storage.sync.get(['serverUrl', 'autoSend'], (items) => {
        if (chrome.runtime.lastError) {
          // On error or unavailable, return defaults
          console.warn('chrome.storage.sync.get error, returning defaults:', chrome.runtime.lastError);
          resolve({ serverUrl: '', autoSend: false });
          return;
        }
        resolve({
          // default to local server for development
          serverUrl: items.serverUrl || 'http://localhost:3000',
          autoSend: typeof items.autoSend === 'boolean' ? items.autoSend : false
        });
      });
    } catch (e) {
      console.warn('getSettings() exception, returning defaults:', e);
      resolve({ serverUrl: '', autoSend: false });
    }
  });
}

/**
 * Save extension settings to chrome.storage
 * @param {object} settings - Settings object with serverUrl and autoSend
 * @returns {Promise<void>}
 */
function saveSettings(settings) {
  return new Promise((resolve, reject) => {
    try {
      chrome.storage.sync.set({
        serverUrl: settings.serverUrl || '',
        autoSend: !!settings.autoSend
      }, () => {
        if (chrome.runtime.lastError) {
          console.warn('chrome.storage.sync.set error:', chrome.runtime.lastError);
          reject(chrome.runtime.lastError);
          return;
        }
        resolve();
      });
    } catch (e) {
      console.warn('saveSettings() exception:', e);
      reject(e);
    }
  });
}

// Export functions for other modules
window.AntiSpamStorage = { getSettings, saveSettings };
