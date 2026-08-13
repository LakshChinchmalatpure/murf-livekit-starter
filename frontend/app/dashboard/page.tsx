'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  RefreshCw,
  Phone,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  ShieldCheck,
  Calendar,
  AlertCircle
} from 'lucide-react';

interface CallRecord {
  call_id: string;
  caller_id: string;
  caller_name: string;
  call_type: string;
  status: string;
  start_time: string;
  end_time: string;
}

export default function DashboardPage() {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchCalls = async (showRefreshState = false) => {
    if (showRefreshState) setRefreshing(true);
    try {
      const res = await fetch(`/api/calls?t=${Date.now()}`, {
        cache: 'no-store'
      });
      if (!res.ok) {
        throw new Error('Failed to fetch call records');
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setCalls(data);
      } else {
        setCalls([]);
      }
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An error occurred while fetching calls.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, []);

  // Calculate statistics
  const totalCalls = calls.length;
  const successfulCalls = calls.filter(c => c.status === 'success').length;
  const failedCalls = calls.filter(c => c.status === 'failed').length;
  const successRate = totalCalls > 0 ? ((successfulCalls / totalCalls) * 100).toFixed(1) : '0.0';

  // Format relative/short start time
  const formatTime = (isoString: string) => {
    if (!isoString) return 'Unknown';
    try {
      const date = new Date(isoString);
      return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (e) {
      return isoString;
    }
  };

  // Format duration
  const formatDuration = (startIso: string, endIso: string) => {
    if (!startIso) return '--:--';
    if (!endIso) return 'Ongoing';
    try {
      const start = new Date(startIso).getTime();
      const end = new Date(endIso).getTime();
      const durationSeconds = Math.max(0, Math.round((end - start) / 1000));
      
      const mins = Math.floor(durationSeconds / 60);
      const secs = durationSeconds % 60;
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } catch (e) {
      return '--:--';
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans w-full max-w-7xl mx-auto px-4 md:px-8 py-6">
      
      {/* HEADER SECTION */}
      <header className="border-b border-border/60 pb-5 mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-2.5 rounded-xl border border-border hover:bg-muted/50 transition-all text-muted-foreground hover:text-foreground"
            title="Go back to Home"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Performance Dashboard
            </h1>
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
              Voice Agent Call Analytics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-center">
          <button
            onClick={() => fetchCalls(true)}
            disabled={refreshing || loading}
            className="bg-muted hover:bg-muted/80 text-foreground border border-border px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 cursor-pointer shadow-sm disabled:opacity-50 transition-all"
          >
            <RefreshCw className={`size-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh Stats
          </button>
        </div>
      </header>

      {/* ERROR MESSAGE CARD */}
      {error && (
        <div className="mb-6 p-4 rounded-xl border border-destructive/20 bg-destructive/10 text-destructive text-sm font-semibold flex items-center gap-2 max-w-xl">
          <AlertCircle className="size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* METRIC CARD PANEL */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        
        {/* TOTAL CALLS CARD */}
        <div className="p-6 rounded-2xl border border-border bg-card hover:border-primary/20 transition-all duration-300 shadow-sm relative overflow-hidden group">
          <div className="absolute right-3 top-3 bg-primary/10 p-2.5 rounded-xl border border-primary/20 text-primary">
            <Phone className="size-5" />
          </div>
          <span className="text-[10px] font-bold tracking-wider text-muted-foreground uppercase">
            Total Calls
          </span>
          <h2 className="text-3xl font-extrabold text-foreground mt-2 tracking-tight">
            {loading ? '...' : totalCalls}
          </h2>
          <p className="text-xs text-muted-foreground mt-2">
            Inbound & outbound sessions
          </p>
        </div>

        {/* SUCCESSFUL CALLS CARD */}
        <div className="p-6 rounded-2xl border border-border bg-card hover:border-emerald-500/20 transition-all duration-300 shadow-sm relative overflow-hidden group">
          <div className="absolute right-3 top-3 bg-emerald-500/10 p-2.5 rounded-xl border border-emerald-500/20 text-emerald-500">
            <CheckCircle2 className="size-5" />
          </div>
          <span className="text-[10px] font-bold tracking-wider text-muted-foreground uppercase">
            Successful Calls
          </span>
          <h2 className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-500 mt-2 tracking-tight">
            {loading ? '...' : successfulCalls}
          </h2>
          <p className="text-xs text-muted-foreground mt-2">
            Eligibility & documents checked
          </p>
        </div>

        {/* FAILED CALLS CARD */}
        <div className="p-6 rounded-2xl border border-border bg-card hover:border-rose-500/20 transition-all duration-300 shadow-sm relative overflow-hidden group">
          <div className="absolute right-3 top-3 bg-rose-500/10 p-2.5 rounded-xl border border-rose-500/20 text-rose-500">
            <XCircle className="size-5" />
          </div>
          <span className="text-[10px] font-bold tracking-wider text-muted-foreground uppercase">
            Failed Calls
          </span>
          <h2 className="text-3xl font-extrabold text-rose-500 mt-2 tracking-tight">
            {loading ? '...' : failedCalls}
          </h2>
          <p className="text-xs text-muted-foreground mt-2">
            Incomplete or hung up calls
          </p>
        </div>

        {/* SUCCESS RATE CARD */}
        <div className="p-6 rounded-2xl border border-border bg-card hover:border-amber-500/20 transition-all duration-300 shadow-sm relative overflow-hidden group">
          <div className="absolute right-3 top-3 bg-amber-500/10 p-2.5 rounded-xl border border-amber-500/20 text-amber-500">
            <TrendingUp className="size-5" />
          </div>
          <span className="text-[10px] font-bold tracking-wider text-muted-foreground uppercase">
            Success Rate
          </span>
          <h2 className="text-3xl font-extrabold text-foreground mt-2 tracking-tight">
            {loading ? '...' : `${successRate}%`}
          </h2>
          <div className="w-full bg-muted rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, parseFloat(successRate))}%` }}
            />
          </div>
        </div>

      </div>

      {/* REAL-TIME CALL LOGS TABLE */}
      <div className="border border-border/80 rounded-2xl bg-card shadow-md overflow-hidden flex flex-col">
        <div className="px-6 py-5 border-b border-border/40 bg-muted/30 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-base text-foreground tracking-tight">Call Records Logs</h3>
            <p className="text-xs text-muted-foreground">Real-time Browser & SIP voice sessions</p>
          </div>
          
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20">
            <ShieldCheck className="size-3.5" />
            Caller Data Protected
          </div>
        </div>

        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-12 text-center text-sm text-muted-foreground flex flex-col items-center gap-3">
              <RefreshCw className="size-8 animate-spin text-primary" />
              <span>Loading call data records...</span>
            </div>
          ) : calls.length === 0 ? (
            <div className="p-12 text-center text-sm text-muted-foreground flex flex-col items-center gap-2">
              <Phone className="size-8 text-muted-foreground/60 mb-2" />
              <p className="font-bold text-foreground">No calls recorded yet</p>
              <p className="text-xs">Start a voice session on the home page to begin tracking agent performance.</p>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-muted/40 border-b border-border/60 text-muted-foreground font-bold text-[10px] uppercase tracking-wider">
                  <th className="px-6 py-4">Call ID</th>
                  <th className="px-6 py-4">Caller</th>
                  <th className="px-6 py-4">Call Type</th>
                  <th className="px-6 py-4">Start Time</th>
                  <th className="px-6 py-4">Duration</th>
                  <th className="px-6 py-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/45">
                {calls.map((call) => {
                  const isSuccess = call.status === 'success';
                  const isOutbound = call.call_type === 'outbound';
                  return (
                    <tr key={call.call_id} className="hover:bg-muted/20 transition-colors">
                      <td className="px-6 py-4 font-mono text-muted-foreground font-medium select-all">
                        {call.call_id.substring(0, 14)}...
                      </td>
                      <td className="px-6 py-4 font-bold text-foreground flex items-center gap-2">
                        <div className="size-7 rounded-full bg-muted flex items-center justify-center text-[10px] font-semibold text-muted-foreground">
                          {call.caller_name.charAt(0).toUpperCase()}
                        </div>
                        {call.caller_name}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md font-semibold ${
                          isOutbound
                            ? 'bg-purple-500/10 text-purple-500 border border-purple-500/20'
                            : 'bg-indigo-500/10 text-indigo-500 border border-indigo-500/20'
                        }`}>
                          {isOutbound ? 'Outbound' : 'Inbound'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground font-medium">
                        <span className="flex items-center gap-1.5">
                          <Calendar className="size-3.5" />
                          {formatTime(call.start_time)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground font-medium">
                        <span className="flex items-center gap-1.5">
                          <Clock className="size-3.5" />
                          {formatDuration(call.start_time, call.end_time)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-bold ${
                          isSuccess
                            ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-500 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-500 border border-rose-500/20'
                        }`}>
                          <span className={`size-1.5 rounded-full ${isSuccess ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                          {isSuccess ? 'Success' : 'Failed'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <footer className="mt-auto pt-8 pb-4 text-center text-xs text-muted-foreground border-t border-border/40">
        <p>© 2026 Artha Saathi Admin Portal. All rights reserved.</p>
      </footer>

    </div>
  );
}
