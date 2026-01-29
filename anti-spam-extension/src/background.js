// Service worker entry point for Anti Spam
// Handles message routing and server communication

// Load the API client module
async function checkUrlsWithServer(serverBase, urls, email) {
  if (!serverBase) {
    return { ok: false, error: 'no-server-url' };
  }
  const endpoint = serverBase.replace(/\/+$/, '') + '/check';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);

  const payload = { urls };
  if (email) {
    payload.email = email;
  }

  return fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: controller.signal
  }).then(async (res) => {
    clearTimeout(timeout);
    if (!res.ok) {
      return { ok: false, status: res.status, error: 'server-error' };
    }
    try {
      const json = await res.json();
      return json;
    } catch (e) {
      return { ok: false, error: 'invalid-json' };
    }
  }).catch((err) => {
    clearTimeout(timeout);
    console.warn('checkUrlsWithServer fetch error:', err);
    return { ok: false, error: 'network-error' };
  });
}

async function sendReportToServer(serverBase, data) {
  if (!serverBase) {
    return { ok: false, error: 'no-server-url' };
  }
  const endpoint = serverBase.replace(/\/+$/, '') + '/report';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);

  return fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    signal: controller.signal
  }).then(async (res) => {
    clearTimeout(timeout);
    if (!res.ok) return { ok: false, status: res.status };
    try {
      const json = await res.json();
      return { ok: true, result: json };
    } catch (e) {
      return { ok: true };
    }
  }).catch((err) => {
    clearTimeout(timeout);
    console.warn('sendReportToServer fetch error:', err);
    return { ok: false, error: 'network-error' };
  });
}

async function sendComplaint(badUrl) {
  if (!badUrl) {
    console.warn('sendComplaint: no URL provided');
    return { ok: false, error: 'no-url' };
  }
  const endpoint = 'http://localhost:8787/complaint';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);

  return fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain' },
    body: "This website has been identified and reported as spam.\n" +
      "A complaint was submitted by an anti spam tool member after detecting unsolicited or malicious behavior originating from this site.\n" +
      "Future transmissions of this website to a members will result in additional complaints.\n" +
      "To prevent further complaints, visit:\n" +
      "http://localhost:3000/filter",
    signal: controller.signal
  }).then(async (res) => {
    clearTimeout(timeout);
    console.log('sendComplaint for', badUrl, '- received response', res.status);
    if (!res.ok) return { ok: false, status: res.status };
    try {
      const json = await res.json();
      return { ok: true, result: json };
    } catch (e) {
      return { ok: true };
    }
  }).catch((err) => {
    clearTimeout(timeout);
    console.warn('sendComplaint fetch error:', err);
    return { ok: false, error: 'network-error' };
  });
}

// Called when the extension is installed or updated
chrome.runtime.onInstalled.addListener(() => {
  // Initialize defaults if desired
  console.log('Anti Spam service worker installed.');
});

// Keep last check results per tab (in-memory cache) Keyed by tabId
const lastResultsByTab = new Map();

// Helper to get settings directly from chrome.storage
function _getSettings() {
  return new Promise((resolve) => {
    try {
      chrome.storage.sync.get(['serverUrl', 'autoSend'], (items) => {
        if (chrome.runtime.lastError) {
          console.warn('chrome.storage.sync.get error in background:', chrome.runtime.lastError);
          resolve({ serverUrl: 'http://localhost:3000', autoSend: false });
          return;
        }
        resolve({
          serverUrl: items.serverUrl || 'http://localhost:3000',
          autoSend: typeof items.autoSend === 'boolean' ? items.autoSend : false
        });
      });
    } catch (e) {
      console.warn('_getSettings exception:', e);
      resolve({ serverUrl: 'http://localhost:3000', autoSend: false });
    }
  });
}

// Message handling: content script will send { type: 'checkUrls', urls: [...] }
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || !message.type) return;

  if (message.type === 'checkUrls') {
    const urls = Array.isArray(message.urls) ? message.urls : [];
    const email = message.email || null;
    const tabId = sender && sender.tab ? sender.tab.id : null;

    console.log('checkUrls message received with email:', email);

    // Async response
    (async () => {
      const settings = await _getSettings();
      if (!settings.serverUrl) {
        const resp = { ok: false, error: 'no-server-configured' };
        if (sendResponse) sendResponse(resp);
        return;
      }

      // Call server to decide whether URLs are spam
      const result = await checkUrlsWithServer(settings.serverUrl, urls, email);
      console.log('checkUrls: server result:', result);

      // Store last results for UI (popup) lookup
      if (tabId != null) {
        lastResultsByTab.set(tabId, { urls, result, timestamp: Date.now() });
      }

      // Check if any bad URLs were found
      if (result.ok && result.results && Array.isArray(result.results)) {
        const badUrls = result.results.filter(r => r.spam === true);
        if (badUrls.length > 0) {
          // Send a complaint for each bad URL found
          for (const badUrlObj of badUrls) {
            if (badUrlObj.url) {
              await sendComplaint(badUrlObj.url);
            }
          }
        }
      }

      if (sendResponse) sendResponse(result);
    })();

    // Keep the message channel open for async response
    return true;
  }

  if (message.type === 'sendReport') {
    const payload = message.data || {};
    (async () => {
      const settings = await _getSettings();
      if (!settings.serverUrl) {
        if (sendResponse) sendResponse({ ok: false, error: 'no-server-configured' });
        return;
      }
      const resp = await sendReportToServer(settings.serverUrl, payload);

      // Also send a complaint for each URL in the report
      if (Array.isArray(payload.urls) && payload.urls.length > 0) {
        for (const url of payload.urls) {
          await sendComplaint(url);
        }
      }

      if (sendResponse) sendResponse(resp);
    })();
    return true;
  }

  if (message.type === 'getEmailStatus') {
    // Expect { tabId } optionally
    const tabId = message.tabId || (sender && sender.tab && sender.tab.id);
    const data = tabId != null ? lastResultsByTab.get(tabId) || null : null;
    if (sendResponse) sendResponse({ ok: true, data });
    return;
  }
});
