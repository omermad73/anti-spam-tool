// Popup script for Anti Spam
// Queries the background script for current email status and allows manual spam reporting

document.addEventListener('DOMContentLoaded', () => {
  const reportBtn = document.getElementById('report-spam');
  if (reportBtn) {
    reportBtn.addEventListener('click', async () => {
      // When user clicks, send the extracted URLs from the active tab's last scan to the server
      try {
        const tabs = await new Promise((res) => chrome.tabs.query({ active: true, currentWindow: true }, res));
        const active = tabs && tabs[0];
        const tabId = active ? active.id : null;
        // Request last result from background
        chrome.runtime.sendMessage({ type: 'getEmailStatus', tabId }, (resp) => {
          if (!resp || !resp.ok || !resp.data) {
            // No cached data in background, try asking the content script directly
            if (tabId != null) {
              chrome.tabs.sendMessage(tabId, { type: 'getForcedUrls' }, (csResp) => {
                if (chrome.runtime.lastError) {
                  console.warn('Unable to contact content script for report:', chrome.runtime.lastError.message);
                  return;
                }
                if (csResp && csResp.ok && Array.isArray(csResp.urls) && csResp.urls.length > 0) {
                  const payload = { urls: csResp.urls, fromTabId: tabId, note: 'Reported by user via popup' };
                  chrome.runtime.sendMessage({ type: 'sendReport', data: payload }, (r) => {
                    console.log('Report sent successfully:', r);
                  });
                } else {
                  console.warn('No URLs available from content script to report.');
                }
              });
              return;
            }
            console.warn('No extracted URLs available to report.');
            return;
          }
          const urls = resp.data.urls || [];
          if (!Array.isArray(urls) || urls.length === 0) {
            console.warn('No URLs to report for this email.');
            return;
          }
          // Build complaint payload containing the extracted URLs and metadata
          const payload = { urls: urls, fromTabId: tabId, note: 'Reported by user via popup' };
          chrome.runtime.sendMessage({ type: 'sendReport', data: payload }, (r) => {
            console.log('Report sent successfully:', r);
          });
        });
      } catch (e) {
        console.error('Error while attempting to report spam:', e);
      }
    });
  }

  // Populate status area with last known result for active tab
  (async function updateStatus() {
    const statusEl = document.getElementById('email-info');
    try {
      const tabs = await new Promise((res) => chrome.tabs.query({ active: true, currentWindow: true }, res));
      const active = tabs && tabs[0];
      const tabId = active ? active.id : null;
      chrome.runtime.sendMessage({ type: 'getEmailStatus', tabId }, (resp) => {
        if (!resp || !resp.ok || !resp.data) {
          // No cached data available in background, try asking the content script directly
          if (tabId != null) {
            chrome.tabs.sendMessage(tabId, { type: 'getForcedUrls' }, (csResp) => {
              // If the content script is not present in the tab, chrome.runtime.lastError will be set
              if (chrome.runtime.lastError) {
                console.warn('Unable to contact content script:', chrome.runtime.lastError.message);
                if (statusEl) statusEl.innerHTML = '<p class="muted">Content script not present in this tab. Reload the page or ensure you are on Gmail.</p>';
                return;
              }
              if (csResp && csResp.ok && Array.isArray(csResp.urls) && csResp.urls.length > 0) {
                // Update UI with these urls
                let html = '<div>';
                html += `<p>Found ${csResp.urls.length} forced URLs.</p>`;
                html += '<pre style="white-space:pre-wrap;max-height:120px;overflow:auto;">' + JSON.stringify(csResp.urls, null, 2) + '</pre>';
                html += '</div>';
                if (statusEl) statusEl.innerHTML = html;
              } else {
                if (statusEl) statusEl.innerHTML = '<p class="muted">No recent scan data available.</p>';
              }
            });
            return;
          }
          if (statusEl) statusEl.innerHTML = '<p class="muted">No recent scan data available.</p>';
          return;
        }
        const d = resp.data;
        let html = '<div>';
        html += `<p>Found ${ (d.urls && d.urls.length) || 0 } unique URLs.</p>`;
        html += '<pre style="white-space:pre-wrap;max-height:120px;overflow:auto;">' + JSON.stringify(d.result, null, 2) + '</pre>';
        html += '</div>';
        if (statusEl) statusEl.innerHTML = html;
      });
    } catch (e) {
      if (statusEl) statusEl.innerHTML = '<p class="muted">Error retrieving status.</p>';
    }
  })();
});
