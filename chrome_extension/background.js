let pollInterval = null;

async function checkUpdates() {
    chrome.storage.local.get(['backendUrl', 'authToken'], async (settings) => {
        if (!settings.backendUrl || !settings.authToken) return;

        try {
            chrome.storage.local.set({ isRunning: true, lastError: null });
            
            const response = await fetch(`${settings.backendUrl}/api/extension/pending-updates`, {
                headers: {
                    'Authorization': `Bearer ${settings.authToken}`
                }
            });

            if (!response.ok) {
                if (response.status === 401) throw new Error("Invalid Auth Token");
                throw new Error(`Server returned ${response.status}`);
            }

            const updates = await response.json();
            
            if (updates && updates.length > 0) {
                // Find an active Eldorado tab to delegate the request to (bypasses Cloudflare)
                const tabs = await chrome.tabs.query({ url: "*://*.eldorado.gg/*" });
                if (tabs.length === 0) {
                    chrome.storage.local.set({ lastError: "Error: No Eldorado tab open. Please keep at least one eldorado.gg tab open." });
                    return;
                }

                const targetTab = tabs[0];
                
                for (const update of updates) {
                    console.log(`Sending update request to tab for listing ${update.marketplace_listing_id} to price ${update.pending_target_price}`);
                    
                    // Tell the content script to execute the price change
                    chrome.tabs.sendMessage(targetTab.id, {
                        action: "EXECUTE_PRICE_UPDATE",
                        listingId: update.marketplace_listing_id,
                        newPrice: update.pending_target_price
                    }, async (result) => {
                        if (chrome.runtime.lastError) {
                            console.error(chrome.runtime.lastError);
                            return;
                        }

                        if (result && result.success) {
                            // Tell backend it was successful
                            await fetch(`${settings.backendUrl}/api/extension/update-success`, {
                                method: 'POST',
                                headers: {
                                    'Authorization': `Bearer ${settings.authToken}`,
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ listing_id: update.id })
                            });
                            console.log(`Backend notified of success for ${update.id}`);
                        } else {
                            console.error(`Tab failed to update price: ${result?.error}`);
                        }
                    });
                }
            }

        } catch (error) {
            console.error("Polling error:", error);
            chrome.storage.local.set({ isRunning: false, lastError: `Polling Error: ${error.message}` });
        }
    });
}

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    // Poll every 5 seconds
    pollInterval = setInterval(checkUpdates, 5000);
    checkUpdates(); // Run immediately
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "settings_updated") {
        startPolling();
    }
});

// Start on load if settings exist
startPolling();
