// Content script for Anti Spam
// Runs on https://mail.google.com/*
// Detects when emails are opened, extracts URLs, and sends them to the background script for checking

console.log('Anti Spam content script loaded.');

function extractUrls() {
	// Only extract if we find actual message containers (indicating an email is open)
	const selectors = ['div.a3s', 'div[role="article"]', 'div[role="listitem"]', 'div.ii'];
	let containers = [];
	selectors.forEach(sel => {
		try {
			containers = containers.concat(Array.from(document.querySelectorAll(sel)));
		} catch (e) {
			console.warn('Error querying selector', sel, ':', e);
		}
	});

	// If no message containers found, we're likely in the inbox view, not viewing an email
	// Return empty array to prevent sending checks for the inbox
	if (containers.length === 0) {
		return [];
	}

	let anchors = [];
	containers.forEach(c => {
		try {
			anchors = anchors.concat(Array.from(c.querySelectorAll('a[href]')));
		} catch (e) {
			console.warn('Error querying anchors in container:', e);
		}
	});

	const urls = new Set();

	// 1) Extract from <a> hrefs
	anchors.forEach(a => {
		try {
			const href = a.href;
			if (!href) return;
			if (href.startsWith('http://') || href.startsWith('https://')) urls.add(href);
		} catch (e) {
			// ignore malformed hrefs
		}
	});

	// 2) Also extract plain-text URLs inside containers
	// Simple regex matching http/https
	const urlRegex = /https?:\/\/[\w\-.:@%/?#=&+~;,%]+/gi;
	for (const el of containers) {
		try {
			const text = el.innerText || '';
			if (!text) continue;
			let m;
			while ((m = urlRegex.exec(text)) !== null) {
				const found = m[0];
				if (found && (found.startsWith('http://') || found.startsWith('https://'))) {
					urls.add(found);
				}
			}
		} catch (e) {
			console.warn('Error extracting text URLs:', e);
		}
	}

	return Array.from(urls);
}

function extractEmailAddress() {
	// Try to extract the current user's email from Gmail UI
	try {
		// Look for Gmail's account email button
		const accountButtons = document.querySelectorAll('[role="button"][aria-label*="@"], button[aria-label*="@"]');
		for (const btn of accountButtons) {
			const label = btn.getAttribute('aria-label') || '';
			const match = label.match(/^([\w\.-]+@[\w\.-]+\.[\w]+)/);
			if (match) {
				const email = match[1];
				console.log('Anti Spam: extracted email from account button:', email);
				return email;
			}
		}
		
		// Check Gmail's profile/account links
		const profileLinks = document.querySelectorAll('a[href*="/SignOutOptions"], a[href*="accounts.google.com"]');
		for (const link of profileLinks) {
			const parent = link.closest('[role="button"], div');
			if (parent) {
				const label = parent.getAttribute('aria-label') || parent.textContent || '';
				const match = label.match(/([\w\.-]+@[\w\.-]+\.[\w]+)/);
				if (match) {
					const email = match[1];
					console.log('Anti Spam: extracted email from profile link:', email);
					return email;
				}
			}
		}
		
		// Check for data email attributes in account areas
		const accountAreas = document.querySelectorAll('[data-email]');
		for (const area of accountAreas) {
			const email = area.getAttribute('data-email');
			if (email && email.includes('@')) {
				console.log('Anti Spam: extracted email from data-email attribute:', email);
				return email;
			}
		}
		
	} catch (e) {
		console.warn('Error extracting email:', e);
	}
	
	console.warn('Anti Spam: could not extract email from page');
	return null;
}

let lastSentHash = null;

function hashArray(arr) {
	try {
		return JSON.stringify(arr.sort()).toString();
	} catch (e) { return null; }
}

async function scanAndSend() {
	try {
		// Extract URLs from the Gmail DOM
		const urls = extractUrls();

		if (!urls || urls.length === 0) return;
		const h = hashArray(urls);
		if (!h || h === lastSentHash) return; // no change
		lastSentHash = h;

		// Extract current user's email address
		const email = extractEmailAddress();

		// Send data to background; server decides spam and tracks member
		chrome.runtime.sendMessage({ type: 'checkUrls', urls, email }, (response) => {
			// Response logged for debugging
			console.log('Anti Spam: server response for urls:', response);
		});
	} catch (e) {
		console.error('Anti Spam scanAndSend error:', e);
	}
}

// Initial scan
try {
	scanAndSend();
} catch (e) {
	console.error('Anti Spam initial scan error:', e);
}

// Observe DOM changes to detect new content
try {
	const observer = new MutationObserver(() => {
		// Debounce
		setTimeout(scanAndSend, 250);
	});
	observer.observe(document.body, { childList: true, subtree: true });
} catch (e) {
	console.error('Anti Spam MutationObserver setup error:', e);
}

// Listen for direct requests from the popup/background to return URLs immediately
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
	try {
		if (message && message.type === 'getForcedUrls') {
			// For popup fallback: return extracted URLs from the current page
			const urls = extractUrls();
			sendResponse({ ok: true, urls });
			return true;
		}
	} catch (e) {
		// ignore
	}
});
