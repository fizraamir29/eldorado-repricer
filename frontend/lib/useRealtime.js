import { useEffect, useRef, useState, useCallback } from "react";

/**
 * Opens one WebSocket connection to the backend and re-connects automatically
 * if it drops (network blip, backend restart, etc). Exposes:
 *   - connected: boolean, shown as a small status dot in the header
 *   - lastEvent: the most recent { type, ... } message, so pages can react
 *     to "price_update" or "notification" events as they arrive live.
 */
export default function useRealtime() {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef = useRef(null);
  const retryDelay = useRef(1000);

  const connect = useCallback(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("token");
    if (!token) return;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const wsUrl = apiUrl.replace(/^http/, "ws") + `/ws?token=${encodeURIComponent(token)}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      retryDelay.current = 1000; // reset backoff after a successful connection
    };

    ws.onmessage = (event) => {
      try {
        setLastEvent(JSON.parse(event.data));
      } catch {
        // ignore malformed frames
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconnect with capped exponential backoff — handles brief network drops
      // and backend restarts without hammering the server.
      setTimeout(connect, retryDelay.current);
      retryDelay.current = Math.min(retryDelay.current * 2, 15000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  return { connected, lastEvent };
}
