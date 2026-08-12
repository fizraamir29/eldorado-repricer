import { useEffect, useState } from "react";
import { Zap, ZapOff, Plus, Trash2, Clock, ShieldCheck, MessageSquare, Save, CheckCircle2, ArrowRight, RefreshCw } from "lucide-react";
import Layout from "../components/Layout";

import api from "../lib/api";
import useRealtime from "../lib/useRealtime";
import { useTheme } from "../lib/useTheme";

const REASON_STYLE = {
  undercut: { label: "Undercut applied ($0.01 step)", className: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" },
  clamped_to_min: { label: "Held at minimum floor", className: "text-amber-400 bg-amber-500/10 border-amber-500/30" },
  clamped_to_max: { label: "Held at maximum ceiling", className: "text-amber-400 bg-amber-500/10 border-amber-500/30" },
  no_change: { label: "Already lowest market price", className: "text-slate-400 bg-slate-800 border-slate-700" },
  no_competitors: { label: "No competitor offers found", className: "text-slate-400 bg-slate-800 border-slate-700" },
  offer_missing: { label: "Offer Missing on Eldorado", className: "text-rose-400 bg-rose-500/10 border-rose-500/30" },
};

export default function ListingsPage() {
  const [listings, setListings] = useState([]);
  const [rules, setRules] = useState({});
  const [loading, setLoading] = useState(true);
  const [isSyncingEldorado, setIsSyncingEldorado] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [flash, setFlash] = useState({});
  const [savedSuccess, setSavedSuccess] = useState({});
  const { lastEvent } = useRealtime();
  const { accentObj } = useTheme();

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (lastEvent?.type === "price_update") {
      setListings((prev) =>
        prev.map((l) =>
          l.id === lastEvent.listing_id
            ? { ...l, current_price: lastEvent.new_price, last_checked_at: lastEvent.checked_at }
            : l
        )
      );
      setFlash((prev) => ({ ...prev, [lastEvent.listing_id]: lastEvent.reason }));
      setTimeout(() => {
        setFlash((prev) => {
          const next = { ...prev };
          delete next[lastEvent.listing_id];
          return next;
        });
      }, 4000);
    }
  }, [lastEvent]);

  async function load() {
    setLoading(true);
    try {
      // We no longer auto-sync on load. Client must explicitly click "Sync from Eldorado".

      const { data } = await api.get("/listings");
      setListings(data);

      const ruleEntries = await Promise.all(
        data.map(async (l) => {
          const r = await api.get(`/listings/${l.id}/rule`);
          return [l.id, r.data];
        })
      );
      setRules(Object.fromEntries(ruleEntries));
    } catch (e) {
      // Intercepted on 401
    } finally {
      setLoading(false);
    }
  }

  async function syncFromEldorado() {
    setIsSyncingEldorado(true);
    try {
      const { data } = await api.post("/listings/sync-eldorado");
      alert(`Successfully synced ${data.synced_count} new listings!`);
      await load(); // Reload listings to show the new ones
    } catch (e) {
      alert(e.response?.data?.detail || "Failed to sync from Eldorado");
    } finally {
      setIsSyncingEldorado(false);
    }
  }

  async function saveRule(listingId, updated) {
    try {
      const { data } = await api.put(`/listings/${listingId}/rule`, updated);
      setRules((prev) => ({ ...prev, [listingId]: data }));
      setSavedSuccess((prev) => ({ ...prev, [listingId]: true }));
      setTimeout(() => {
        setSavedSuccess((prev) => ({ ...prev, [listingId]: false }));
      }, 3000);
    } catch (e) {
      const detail = e.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail[0]?.msg : detail;
      alert(msg || "Failed to update rule settings");
    }
  }

  async function removeListing(listingId) {
    if (!confirm("Are you sure you want to stop tracking this listing?")) return;
    await api.delete(`/listings/${listingId}`);
    setListings((prev) => prev.filter((l) => l.id !== listingId));
  }

  async function addListing(payload) {
    try {
      const { data } = await api.post("/listings", payload);
      setListings((prev) => [...prev, data]);
      const r = await api.get(`/listings/${data.id}/rule`);
      setRules((prev) => ({ ...prev, [data.id]: r.data }));
      setShowAddForm(false);
    } catch (e) {
      const detail = e.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail[0]?.msg : detail;
      alert(msg || "Failed to add listing");
    }
  }

  async function syncListing(listingId) {
    try {
      const { data } = await api.post(`/listings/${listingId}/sync`);
      setListings((prev) =>
        prev.map((l) =>
          l.id === listingId
            ? { ...l, current_price: data.current_price, last_checked_at: data.last_checked_at, status: data.status === "synced" ? "active" : data.status }
            : l
        )
      );
    } catch (e) {
      const detail = e.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail[0]?.msg : detail;
      alert(msg || "Failed to sync listing");
    }
  }

  async function relinkListing(listingId, newOfferId) {
    try {
      const { data } = await api.put(`/listings/${listingId}/relink`, { marketplace_listing_id: newOfferId });
      setListings((prev) => prev.map((l) => (l.id === listingId ? data : l)));
    } catch (e) {
      const detail = e.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail[0]?.msg : detail;
      alert(msg || "Failed to relink listing");
    }
  }

  const activeAutomationCount = Object.values(rules).filter((r) => r.enabled).length;

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20 text-slate-400 text-sm gap-2">
          <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          Loading tracked listings…
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      {/* Overview Stat Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-[#131B2A] border border-slate-800 rounded-2xl p-5 shadow-glass flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">TOTAL TRACKED LISTINGS</p>
            <p className="text-2xl font-bold text-white mt-1 font-heading">{listings.length}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <ShieldCheck size={20} />
          </div>
        </div>

        <div className="bg-[#131B2A] border border-slate-800 rounded-2xl p-5 shadow-glass flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">ACTIVE BOT AUTOMATION</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1 font-heading">
              {activeAutomationCount} / {listings.length}
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400">
            <Zap size={20} />
          </div>
        </div>

        <div className="bg-[#131B2A] border border-slate-800 rounded-2xl p-5 shadow-glass flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400">AUTO-GREETING RESPONDER</p>
            <p className="text-2xl font-bold text-indigo-400 mt-1 font-heading">Active</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <MessageSquare size={20} />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-white font-heading">Tracked Marketplace Items</h2>
        <div className="flex gap-3">
          <button
            onClick={syncFromEldorado}
            disabled={isSyncingEldorado}
            className={`flex items-center gap-2 bg-[#1E293B] hover:bg-[#334155] border border-slate-700 text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-all disabled:opacity-50`}
          >
            <RefreshCw size={18} className={isSyncingEldorado ? "animate-spin text-emerald-400" : "text-slate-400"} /> 
            {isSyncingEldorado ? "Syncing..." : "Sync from Eldorado"}
          </button>
          <button
            onClick={() => setShowAddForm((v) => !v)}
            className={`flex items-center gap-2 bg-gradient-to-r ${accentObj.primary} text-white text-sm font-semibold px-4 py-2.5 rounded-xl ${accentObj.shadow} transition-all`}
          >
            <Plus size={18} /> Add New Listing
          </button>
        </div>
      </div>

      {showAddForm && <AddListingForm onSubmit={addListing} onCancel={() => setShowAddForm(false)} />}

      {listings.length === 0 && !showAddForm && (
        <div className="bg-[#131B2A] rounded-2xl border border-dashed border-slate-800 p-12 text-center text-slate-400 text-sm">
          <Zap size={32} className="mx-auto mb-3 text-slate-600" />
          No listings being tracked yet. Click <strong className="text-white font-medium">Add New Listing</strong> to start automated $0.01 repricing.
        </div>
      )}

      <div className="grid gap-6">
        {listings.map((listing) => (
          <ListingCard
            key={listing.id}
            listing={listing}
            rule={rules[listing.id]}
            flashReason={flash[listing.id]}
            isSaved={savedSuccess[listing.id]}
            onSave={(updated) => saveRule(listing.id, updated)}
            onRemove={() => removeListing(listing.id)}
            onSync={() => syncListing(listing.id)}
            onRelink={(newOfferId) => relinkListing(listing.id, newOfferId)}
          />
        ))}
      </div>
    </Layout>
  );

}

function AddListingForm({ onSubmit, onCancel }) {
  const [form, setForm] = useState({ marketplace_listing_id: "", game_name: "", title: "", current_price: "" });

  return (
    <div className="bg-[#131B2A] rounded-2xl shadow-glass p-6 mb-6 border border-slate-800">
      <h3 className="text-base font-semibold text-white mb-4 font-heading">Add Eldorado Listing to Track</h3>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-5">
        <div>
          <label className="text-xs text-slate-400 block mb-1.5 font-medium">Eldorado Listing ID</label>
          <input
            placeholder="e.g. offer-98214"
            value={form.marketplace_listing_id}
            onChange={(e) => setForm({ ...form, marketplace_listing_id: e.target.value })}
            className="w-full px-3 py-2 bg-[#0F172A] border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500 transition"
          />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1.5 font-medium">Game Name</label>
          <input
            placeholder="e.g. World of Warcraft"
            value={form.game_name}
            onChange={(e) => setForm({ ...form, game_name: e.target.value })}
            className="w-full px-3 py-2 bg-[#0F172A] border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500 transition"
          />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1.5 font-medium">Item / Currency Title</label>
          <input
            placeholder="e.g. 1000k Gold Coins"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="w-full px-3 py-2 bg-[#0F172A] border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500 transition"
          />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1.5 font-medium">Current Listing Price ($)</label>
          <input
            type="number"
            step="0.01"
            placeholder="12.50"
            value={form.current_price}
            onChange={(e) => setForm({ ...form, current_price: e.target.value })}
            className="w-full px-3 py-2 bg-[#0F172A] border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500 transition"
          />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={() => onSubmit({ ...form, current_price: parseFloat(form.current_price) })}
          className="bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition shadow-glow-emerald"
        >
          Confirm & Add Listing
        </button>
        <button onClick={onCancel} className="text-sm font-medium px-4 py-2.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition">
          Cancel
        </button>
      </div>
    </div>
  );
}

function ListingCard({ listing, rule, flashReason, isSaved, onSave, onRemove, onSync }) {
  const [form, setForm] = useState(rule);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => setForm(rule), [rule]);
  if (!form) return null;

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSync() {
    setSyncing(true);
    try {
      await onSync();
    } finally {
      setSyncing(false);
    }
  }

  const flash = flashReason ? REASON_STYLE[flashReason] : null;

  // Calculate percentage indicator for floor/ceiling visual range gauge
  const minP = Number(form.min_price) || 0.01;
  const maxP = Number(form.max_price) || 100.0;
  const curP = Number(listing.current_price) || minP;
  const percent = Math.min(100, Math.max(0, ((curP - minP) / (maxP - minP || 1)) * 100));

  const isMissing = listing.status === "missing";

  return (
    <div
      className={`bg-[#131B2A] rounded-2xl p-6 border transition-all shadow-glass ${
        flash ? "border-emerald-500/50 shadow-glow-emerald" : "border-slate-800"
      } ${isMissing ? "border-rose-500/50" : ""}`}
    >
      {isMissing && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 p-4 rounded-xl mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ZapOff size={20} />
            <div>
              <p className="font-bold text-sm">Offer Missing / Not Live on Eldorado</p>
              <p className="text-xs opacity-80 mt-0.5">This offer could not be found. Repricing is paused until you re-link it to a valid active offer.</p>
            </div>
          </div>
          <button 
            onClick={() => {
              const newId = prompt("Enter the new active Offer ID from Eldorado:");
              if (newId) onRelink(newId.trim());
            }}
            className="bg-rose-500/20 hover:bg-rose-500/30 px-4 py-2 rounded-lg text-xs font-bold transition"
          >
            Re-link Offer
          </button>
        </div>
      )}

      {/* Header Info Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-bold text-white font-heading">{listing.title}</h3>
            {flash && (
              <span className={`text-xs px-3 py-1 rounded-full font-medium border ${flash.className}`}>
                {flash.label}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
            <span className="bg-slate-800 text-slate-300 px-2.5 py-0.5 rounded-md font-medium">{listing.game_name}</span>
            <span>ID: <code className="text-slate-300">{listing.marketplace_listing_id}</code></span>
            {listing.last_checked_at && (
              <span className="flex items-center gap-1 text-slate-400">
                <Clock size={12} /> Last synced {new Date(listing.last_checked_at).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Current Live Price</p>
            <p className="text-2xl font-extrabold text-emerald-400 font-heading">${Number(listing.current_price).toFixed(2)}</p>
          </div>

          <div className="flex items-center gap-3 pl-4 border-l border-slate-800">
            <button
              onClick={handleSync}
              disabled={syncing}
              className="flex items-center gap-1.5 px-3 py-2 bg-[#0F172A] hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-200 rounded-xl transition disabled:opacity-50"
              title="Force Immediate Repricing Sync"
            >
              <RefreshCw size={14} className={`text-teal-400 ${syncing ? "animate-spin" : ""}`} />
              {syncing ? "Syncing..." : "Sync Now"}
            </button>

            <button
              onClick={() => update("enabled", !form.enabled)}
              className="flex items-center gap-2.5 text-sm font-medium text-slate-200 bg-[#0F172A] hover:bg-slate-800 px-3.5 py-2 rounded-xl border border-slate-700 transition"
              title="Toggle Bot Active/Paused"
            >
              <span className={`w-2.5 h-2.5 rounded-full ${form.enabled ? "bg-emerald-500 shadow-glow-emerald" : "bg-slate-500"}`}></span>
              <span className={form.enabled ? "text-emerald-400 font-semibold" : "text-slate-400"}>
                {form.enabled ? "Bot Active" : "Bot Paused"}
              </span>
            </button>

            <button onClick={onRemove} className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition" title="Remove Listing">
              <Trash2 size={18} />
            </button>
          </div>
        </div>
      </div>


      {/* Visual Price Range Gauge */}
      <div className="mb-6 bg-[#0F172A] p-4 rounded-xl border border-slate-800/80">
        <div className="flex justify-between text-xs font-semibold mb-2">
          <span className="text-amber-400">Min Floor: ${Number(form.min_price).toFixed(2)}</span>
          <span className="text-emerald-400 flex items-center gap-1 font-bold">
            Live Position: ${Number(listing.current_price).toFixed(2)}
          </span>
          <span className="text-teal-400">Max Ceiling: ${Number(form.max_price).toFixed(2)}</span>
        </div>
        <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden relative">
          <div
            className="bg-gradient-to-r from-amber-400 via-emerald-400 to-teal-400 h-full rounded-full transition-all duration-500"
            style={{ width: `${percent}%` }}
          ></div>
        </div>
      </div>

      {/* Repricing Rule Settings */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        <Field label="Minimum Price Floor ($)" value={form.min_price} onChange={(v) => update("min_price", v)} hint="Never drop below this price" />
        <Field label="Maximum Price Ceiling ($)" value={form.max_price} onChange={(v) => update("max_price", v)} hint="Never exceed this price" />
        <Field label="Undercut Step ($)" value={form.undercut_step} onChange={(v) => update("undercut_step", v)} hint="Exact undercut amount ($0.01)" />
        <Field label="Check Interval (minutes)" value={form.check_interval_minutes} onChange={(v) => update("check_interval_minutes", v)} step="1" hint="Frequency of market scan" />
      </div>

      {/* Auto Greeting Responder Template Config */}
      <div className="bg-[#0F172A] p-4 rounded-xl border border-slate-800/80 mb-5">
        <div className="flex items-center justify-between mb-3">
          <label className="flex items-center gap-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider">
            <MessageSquare size={14} /> Automated Buyer Welcome Message
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={form.auto_greeting_enabled ?? true}
              onChange={(e) => update("auto_greeting_enabled", e.target.checked)}
              className="accent-indigo-500 w-3.5 h-3.5 rounded"
            />
            <span>Enable Auto-Greeting</span>
          </label>
        </div>
        <input
          type="text"
          value={form.auto_greeting_message || ""}
          onChange={(e) => update("auto_greeting_message", e.target.value)}
          placeholder="Enter custom welcoming message for new buyers..."
          className="w-full px-3 py-2 bg-[#131B2A] border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
        />
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-between">
        {isSaved ? (
          <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-semibold">
            <CheckCircle2 size={16} /> Automation rules updated successfully!
          </span>
        ) : (
          <span className="text-xs text-slate-500">Changes will apply immediately on the next background loop</span>
        )}

        <button
          onClick={() => onSave(form)}
          className="flex items-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-sm font-semibold px-5 py-2.5 rounded-xl shadow-glow-emerald transition-all"
        >
          <Save size={16} /> Save Configuration
        </button>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, step = "0.01", hint }) {
  return (
    <div>
      <label className="text-xs text-slate-400 block mb-1 font-medium">{label}</label>
      <input
        type="number"
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full px-3 py-2 bg-[#0F172A] border border-slate-700 rounded-xl text-sm text-white font-medium focus:outline-none focus:border-emerald-500 transition"
      />
      {hint && <span className="text-[10px] text-slate-500 mt-1 block">{hint}</span>}
    </div>
  );
}
