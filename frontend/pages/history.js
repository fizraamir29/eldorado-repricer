import { useEffect, useState } from "react";
import { TrendingDown, TrendingUp, Minus, AlertCircle, History, Clock, Filter, Download, Printer } from "lucide-react";
import Layout from "../components/Layout";
import api from "../lib/api";
import useRealtime from "../lib/useRealtime";
import { useTheme } from "../lib/useTheme";

const REASON_LABEL = {
  undercut: "Undercut Applied ($0.01 step)",
  clamped_to_min: "Held at Minimum Floor",
  clamped_to_max: "Held at Maximum Ceiling",
  no_change: "Already Lowest Market Price",
  no_competitors: "No Competitor Offers Found",
  error: "API Execution Error",
};

const REASON_BADGE = {
  undercut: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  clamped_to_min: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  clamped_to_max: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  no_change: "bg-slate-800 text-slate-400 border-slate-700",
  no_competitors: "bg-slate-800 text-slate-400 border-slate-700",
  error: "bg-rose-500/10 text-rose-400 border-rose-500/30",
};

function ReasonIcon({ reason, success }) {
  if (!success) return <AlertCircle size={14} className="text-rose-400" />;
  if (reason === "undercut") return <TrendingDown size={14} className="text-emerald-400" />;
  if (reason === "clamped_to_min" || reason === "clamped_to_max") return <TrendingUp size={14} className="text-amber-400" />;
  return <Minus size={14} className="text-slate-400" />;
}

export default function HistoryPage() {
  const [listings, setListings] = useState([]);
  const [selected, setSelected] = useState("");
  const [rows, setRows] = useState([]);
  const { lastEvent } = useRealtime();
  const { accentObj } = useTheme();

  useEffect(() => {
    api.get("/listings").then(({ data }) => {
      setListings(data);
      if (data.length) setSelected(data[0].id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (selected) {
      api.get(`/listings/${selected}/history`).then(({ data }) => setRows(data)).catch(() => {});
    }
  }, [selected]);

  useEffect(() => {
    if (lastEvent?.type === "price_update" && lastEvent.listing_id === selected) {
      setRows((prev) => [
        {
          id: `live-${Date.now()}`,
          old_price: prev[0]?.new_price ?? null,
          new_price: lastEvent.new_price,
          lowest_competitor_price: lastEvent.lowest_competitor_price ?? null,
          reason: lastEvent.reason,
          success: true,
          created_at: lastEvent.checked_at,
        },
        ...prev,
      ]);
    }
  }, [lastEvent, selected]);

  function exportCSV() {
    if (!rows.length) return alert("No history data to export");
    const headers = ["Timestamp", "Previous Price", "New Price", "Lowest Competitor", "Reason", "Status"];
    const csvRows = rows.map((r) => [
      new Date(r.created_at).toLocaleString(),
      r.old_price != null ? `$${Number(r.old_price).toFixed(2)}` : "-",
      `$${Number(r.new_price).toFixed(2)}`,
      r.lowest_competitor_price != null ? `$${Number(r.lowest_competitor_price).toFixed(2)}` : "-",
      REASON_LABEL[r.reason] || r.reason,
      r.success ? "Success" : "Failed",
    ]);

    const content = [headers.join(","), ...csvRows.map((e) => e.map(cell => `"${cell}"`).join(","))].join("\n");
    const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `price_history_report_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function exportPDF() {
    window.print();
  }

  const selectedListingObj = listings.find((l) => l.id === selected);

  return (
    <Layout>
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <Filter size={18} className={accentObj.text} />
          <label className="text-sm font-medium text-slate-300">Select Item:</label>
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="px-4 py-2.5 bg-[#131B2A] border border-slate-800 rounded-xl text-sm font-semibold text-white focus:outline-none focus:border-amber-500 transition shadow-glass"
          >
            {listings.map((l) => (
              <option key={l.id} value={l.id}>
                {l.title} ({l.game_name})
              </option>
            ))}
          </select>
        </div>

        {/* PDF & CSV Export Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={exportCSV}
            className="flex items-center gap-2 bg-[#131B2A] hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold px-3.5 py-2.5 rounded-xl transition"
          >
            <Download size={15} className={accentObj.text} /> Export CSV Audit Log
          </button>
          <button
            onClick={exportPDF}
            className={`flex items-center gap-2 bg-gradient-to-r ${accentObj.primary} text-white text-xs font-semibold px-4 py-2.5 rounded-xl ${accentObj.shadow} transition`}
          >
            <Printer size={15} /> Printable PDF Report
          </button>
        </div>
      </div>

      {selectedListingObj && (
        <div className="bg-[#131B2A] border border-slate-800 rounded-xl p-4 mb-6 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white font-heading">{selectedListingObj.title}</h3>
            <p className="text-xs text-slate-400">Game: {selectedListingObj.game_name} | ID: {selectedListingObj.marketplace_listing_id}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-400 font-medium">CURRENT LIVE PRICE</p>
            <p className={`text-xl font-extrabold ${accentObj.text} font-heading`}>
              ${Number(selectedListingObj.current_price).toFixed(2)}
            </p>
          </div>
        </div>
      )}

      <div className="bg-[#131B2A] rounded-2xl border border-slate-800 shadow-glass overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-[#0F172A] text-slate-300 font-semibold border-b border-slate-800">
            <tr>
              <th className="px-5 py-3.5">Timestamp</th>
              <th className="px-5 py-3.5">Previous Price</th>
              <th className="px-5 py-3.5">New Repriced Value</th>
              <th className="px-5 py-3.5">Lowest Competitor</th>
              <th className="px-5 py-3.5">Repricing Decision</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {rows.map((r) => (
              <tr key={r.id} className="hover:bg-slate-800/30 transition">
                <td className="px-5 py-3.5 text-xs text-slate-400 font-mono">
                  {new Date(r.created_at).toLocaleString()}
                </td>
                <td className="px-5 py-3.5 font-medium">
                  {r.old_price != null ? `$${Number(r.old_price).toFixed(2)}` : "-"}
                </td>
                <td className="px-5 py-3.5 font-bold text-white">
                  ${Number(r.new_price).toFixed(2)}
                </td>
                <td className="px-5 py-3.5 text-slate-400">
                  {r.lowest_competitor_price != null ? `$${Number(r.lowest_competitor_price).toFixed(2)}` : "-"}
                </td>
                <td className="px-5 py-3.5">
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${REASON_BADGE[r.reason] || "bg-slate-800 text-slate-400 border-slate-700"}`}>
                    <ReasonIcon reason={r.reason} success={r.success} />
                    {REASON_LABEL[r.reason] || r.reason}
                  </span>
                </td>
              </tr>
            ))}

            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center py-10 text-slate-400 text-xs">
                  No price history recorded for this item yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
