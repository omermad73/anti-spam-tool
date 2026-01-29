// API client for Anti Spam extension
// Handles communication with the central spam detection server

/**
 * Check URLs with the central server
 * @param {string} serverBase base URL of the server
 * @param {string[]} urls
 * @returns {Promise<object>} parsed JSON response
 */
function checkUrlsWithServer(serverBase, urls) {
  if (!serverBase) {
    return Promise.resolve({ ok: false, error: 'no-server-url' });
  }
  const endpoint = serverBase.replace(/\/+$/, '') + '/check';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000); // 10s timeout

  return fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ urls }),
    signal: controller.signal
  }).then(async (res) => {
    clearTimeout(timeout);
    if (!res.ok) {
      return { ok: false, status: res.status, error: 'server-error' };
    }
    try {
      const json = await res.json();
      return { ok: true, results: json };
    } catch (e) {
      return { ok: false, error: 'invalid-json' };
    }
  }).catch((err) => {
    clearTimeout(timeout);
    console.warn('checkUrlsWithServer fetch error:', err);
    return { ok: false, error: 'network-error' };
  });
}

/**
 * Send a complaint to the central server
 * @param {string} serverBase
 * @param {object} data
 */
function sendComplaintToServer(serverBase, data) {
  if (!serverBase) {
    return Promise.resolve({ ok: false, error: 'no-server-url' });
  }
  const endpoint = serverBase.replace(/\/+$/, '') + '/complaint';
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
    console.warn('sendComplaintToServer fetch error:', err);
    return { ok: false, error: 'network-error' };
  });
}

window.AntiSpamApi = { checkUrlsWithServer, sendComplaintToServer };
