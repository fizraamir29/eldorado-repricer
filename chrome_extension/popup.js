document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('backend_url');
    const tokenInput = document.getElementById('auth_token');
    const saveBtn = document.getElementById('save_btn');
    const statusDiv = document.getElementById('status');
    const bgStatus = document.getElementById('bg_status');

    // Load saved settings
    chrome.storage.local.get(['backendUrl', 'authToken', 'lastError', 'isRunning'], (result) => {
        if (result.backendUrl) urlInput.value = result.backendUrl;
        if (result.authToken) tokenInput.value = result.authToken;
        
        if (result.isRunning) {
            bgStatus.textContent = "Running & Polling...";
            bgStatus.style.color = "green";
        } else {
            bgStatus.textContent = "Stopped / Waiting";
        }
        
        if (result.lastError) {
            statusDiv.textContent = result.lastError;
            statusDiv.className = 'error';
        }
    });

    saveBtn.addEventListener('click', () => {
        const backendUrl = urlInput.value.trim().replace(/\/$/, ""); // remove trailing slash
        const authToken = tokenInput.value.trim();

        if (!backendUrl || !authToken) {
            statusDiv.textContent = 'Please fill both fields.';
            statusDiv.className = 'error';
            return;
        }

        chrome.storage.local.set({ backendUrl, authToken }, () => {
            statusDiv.textContent = 'Saved successfully! Extension will start polling.';
            statusDiv.className = 'success';
            
            // Tell background script to restart polling
            chrome.runtime.sendMessage({ action: "settings_updated" });
        });
    });
});
