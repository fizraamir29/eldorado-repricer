chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "EXECUTE_PRICE_UPDATE") {
        console.log(`Repricer Bridge: Received request to update ${request.listingId} to ${request.newPrice}`);
        
        // Try to find a Bearer token from localStorage (common in modern SPAs)
        let token = "";
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            const val = localStorage.getItem(key);
            if (val && (val.includes("eyJ") || key.toLowerCase().includes("token"))) {
                // heuristic to find JWT token if it exists
                if (val.startsWith("eyJ")) token = val;
                else if (val.includes('"eyJ')) {
                    try {
                        const parsed = JSON.parse(val);
                        if (parsed.token) token = parsed.token;
                        else if (parsed.accessToken) token = parsed.accessToken;
                    } catch(e) {}
                }
            }
        }
        
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*'
        };
        
        // If we found a token in local storage, use it just in case
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        fetch(`https://www.eldorado.gg/api/v1/currency-management/me/offers/${request.listingId}/change-price`, {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify({ amount: request.newPrice }),
            credentials: 'omit' // if it requires token, or 'include' if it relies on cookies
        }).then(response => {
            if (response.status === 401 || response.status === 403) {
                // If it failed without cookies, try WITH cookies
                return fetch(`https://www.eldorado.gg/api/v1/currency-management/me/offers/${request.listingId}/change-price`, {
                    method: 'PUT',
                    headers: headers,
                    body: JSON.stringify({ amount: request.newPrice }),
                    credentials: 'include'
                });
            }
            return response;
        }).then(async (response) => {
            if (response.ok) {
                console.log(`Repricer Bridge: Successfully updated ${request.listingId}`);
                sendResponse({ success: true });
            } else {
                const text = await response.text();
                console.error(`Repricer Bridge: Failed. Status: ${response.status}. Body: ${text}`);
                sendResponse({ success: false, error: `Status ${response.status}: ${text}` });
            }
        }).catch(err => {
            console.error("Repricer Bridge: Fetch error", err);
            sendResponse({ success: false, error: err.message });
        });

        // Return true to indicate we will call sendResponse asynchronously
        return true; 
    }
});
