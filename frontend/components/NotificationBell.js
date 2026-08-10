import { useEffect, useRef, useState } from "react";
import { Bell, AlertTriangle, Info, XCircle } from "lucide-react";
import api from "../lib/api";

const LEVEL_ICON = {
  info: <Info size={16} className="text-brand-600 shrink-0 mt-0.5" />,
  warning: <AlertTriangle size={16} className="text-amber-500 shrink-0 mt-0.5" />,
  error: <XCircle size={16} className="text-red-500 shrink-0 mt-0.5" />,
};

export default function NotificationBell({ liveEvent }) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const boxRef = useRef(null);

  async function load() {
    try {
      const [list, count] = await Promise.all([
        api.get("/notifications"),
        api.get("/notifications/unread-count"),
      ]);
      setItems(list.data);
      setUnread(count.data.count);
    } catch (e) {
      // Gracefully handled by api response interceptor if 401
    }
  }

  useEffect(() => {
    load();
  }, []);

  // Live push: when the scheduler creates a new notification, it arrives here
  // instantly over the WebSocket instead of waiting for the next page load.
  useEffect(() => {
    if (liveEvent?.type === "notification") {
      setItems((prev) => [
        {
          id: liveEvent.id,
          level: liveEvent.level,
          title: liveEvent.title,
          message: liveEvent.message,
          listing_id: liveEvent.listing_id,
          created_at: liveEvent.created_at,
          read: false,
        },
        ...prev,
      ]);
      setUnread((prev) => prev + 1);
    }
  }, [liveEvent]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function markAllRead() {
    await api.post("/notifications/mark-all-read");
    setItems((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnread(0);
  }

  return (
    <div className="relative" ref={boxRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative p-2 rounded-md hover:bg-brand-50 transition"
        aria-label="Notifications"
      >
        <Bell size={20} className="text-brand-800" />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] leading-none rounded-full min-w-[16px] h-4 flex items-center justify-center px-1">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-100 z-20 max-h-96 overflow-y-auto">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <span className="font-medium text-sm text-brand-800">Notifications</span>
            {unread > 0 && (
              <button onClick={markAllRead} className="text-xs text-brand-600 hover:underline">
                Mark all read
              </button>
            )}
          </div>

          {items.length === 0 && (
            <p className="text-sm text-gray-400 px-4 py-6 text-center">No notifications yet.</p>
          )}

          {items.map((n) => (
            <div
              key={n.id}
              className={`px-4 py-3 border-b border-gray-50 flex gap-2 ${n.read ? "opacity-60" : "bg-brand-50/40"}`}
            >
              {LEVEL_ICON[n.level] || LEVEL_ICON.info}
              <div>
                <p className="text-sm font-medium text-gray-800">{n.title}</p>
                <p className="text-xs text-gray-500 mt-0.5">{n.message}</p>
                <p className="text-[11px] text-gray-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
