'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  ShieldAlert, 
  User, 
  Clock, 
  AlertCircle, 
  ArrowLeft, 
  CheckCircle2, 
  Play, 
  RefreshCw, 
  Languages, 
  MessageSquare,
  Sparkles,
  PhoneCall,
  Mail,
  AlertTriangle
} from 'lucide-react';

interface Escalation {
  reference_id: string;
  name: string;
  what_happened: string;
  checked: string;
  urgency: string;
  language: string;
  follow_up: string;
  status: string;
  created_at: string;
}

export default function EscalationsDashboard() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'All' | 'Open' | 'In Progress' | 'Resolved'>('All');
  const [refreshing, setRefreshing] = useState(false);

  const fetchEscalations = async (showRefreshState = false) => {
    if (showRefreshState) setRefreshing(true);
    try {
      const res = await fetch(`/api/escalations?t=${Date.now()}`, {
        cache: 'no-store'
      });
      if (!res.ok) {
        throw new Error('Failed to fetch escalations');
      }
      const data = await res.ok ? await res.json() : [];
      if (Array.isArray(data)) {
        setEscalations(data);
      } else {
        setEscalations([]);
      }
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An error occurred while fetching tickets.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const updateStatus = async (referenceId: string, newStatus: string) => {
    try {
      const res = await fetch('/api/escalations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ referenceId, status: newStatus }),
      });
      if (!res.ok) {
        throw new Error('Failed to update status');
      }
      // Optimistically update status local state
      setEscalations(prev => 
        prev.map(item => 
          item.reference_id === referenceId ? { ...item, status: newStatus } : item
        )
      );
    } catch (err: any) {
      alert(err.message || 'Failed to update ticket status.');
    }
  };

  useEffect(() => {
    fetchEscalations();
  }, []);

  const filteredTickets = escalations.filter(ticket => {
    if (filter === 'All') return true;
    return ticket.status.toLowerCase() === filter.toLowerCase();
  });

  // Calculate statistics
  const totalCount = escalations.length;
  const openCount = escalations.filter(t => t.status === 'Open').length;
  const inProgressCount = escalations.filter(t => t.status === 'In Progress').length;
  const resolvedCount = escalations.filter(t => t.status === 'Resolved').length;

  const getUrgencyBadge = (urgency: string) => {
    const u = urgency.toLowerCase();
    if (u === 'high') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-500 border border-rose-500/20">
          <span className="size-1.5 rounded-full bg-rose-500 animate-pulse" />
          High
        </span>
      );
    }
    if (u === 'medium') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20">
          <span className="size-1.5 rounded-full bg-amber-500" />
          Medium
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-sky-500/10 text-sky-500 border border-sky-500/20">
        <span className="size-1.5 rounded-full bg-sky-500" />
        Low
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    if (s === 'open') {
      return (
        <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold tracking-wider uppercase bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
          Open
        </span>
      );
    }
    if (s === 'in progress') {
      return (
        <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold tracking-wider uppercase bg-amber-500/10 text-amber-500 border border-amber-500/20">
          In Progress
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold tracking-wider uppercase bg-muted text-muted-foreground border border-border">
        Resolved
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans w-full max-w-7xl mx-auto px-4 md:px-8 py-6">
      
      {/* HEADER */}
      <header className="border-b border-border/60 pb-5 mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <Link 
            href="/"
            className="flex items-center justify-center p-2 rounded-xl bg-card border border-border hover:border-primary/40 text-muted-foreground hover:text-foreground transition-all cursor-pointer shadow-xs"
          >
            <ArrowLeft className="size-5" />
          </Link>
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 p-2.5 rounded-xl border border-primary/20 shadow-sm">
              <ShieldAlert className="size-6 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
                Escalations & Handoffs
              </h1>
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                Financial Services Human-Help Desk
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start md:self-center">
          <button
            onClick={() => fetchEscalations(true)}
            disabled={refreshing || loading}
            className="flex items-center gap-2 bg-card hover:bg-muted border border-border px-4 py-2 rounded-xl text-xs font-semibold text-foreground transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`size-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </header>

      {/* STATS OVERVIEW CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block mb-1">
            Total Tickets
          </span>
          <span className="text-2xl font-black tracking-tight text-foreground">
            {totalCount}
          </span>
        </div>
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider block mb-1">
            Open
          </span>
          <span className="text-2xl font-black tracking-tight text-emerald-500">
            {openCount}
          </span>
        </div>
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-[10px] font-bold text-amber-500 uppercase tracking-wider block mb-1">
            In Progress
          </span>
          <span className="text-2xl font-black tracking-tight text-amber-500">
            {inProgressCount}
          </span>
        </div>
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block mb-1">
            Resolved
          </span>
          <span className="text-2xl font-black tracking-tight text-muted-foreground">
            {resolvedCount}
          </span>
        </div>
      </div>

      {/* FILTERS */}
      <div className="flex gap-2 border-b border-border/50 pb-4 mb-6 text-xs font-semibold overflow-x-auto">
        {(['All', 'Open', 'In Progress', 'Resolved'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-4 py-2 rounded-lg transition-all cursor-pointer shrink-0 ${
              filter === tab
                ? 'bg-primary text-primary-foreground shadow-xs'
                : 'text-muted-foreground hover:bg-card hover:text-foreground border border-transparent'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* ERROR STATE */}
      {error && (
        <div className="mb-6 p-4 rounded-xl border border-destructive/20 bg-destructive/5 text-destructive text-sm flex items-start gap-3">
          <AlertCircle className="size-5 shrink-0" />
          <div>
            <h4 className="font-bold">Database Access Error</h4>
            <p className="text-xs text-destructive/90 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* MAIN LIST */}
      <div className="flex-1">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
            <RefreshCw className="size-8 animate-spin text-primary" />
            <p className="text-xs font-medium">Loading escalation records...</p>
          </div>
        ) : filteredTickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 border border-dashed border-border rounded-2xl bg-card/20 text-center px-4">
            <Sparkles className="size-10 text-muted-foreground/60 mb-3" />
            <h3 className="font-bold text-base text-foreground mb-1">No Tickets Found</h3>
            <p className="text-xs text-muted-foreground max-w-xs">
              No escalations matching status &ldquo;{filter}&rdquo; were found in the database.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredTickets.map((ticket) => (
              <div 
                key={ticket.reference_id}
                className="border border-border/80 rounded-2xl bg-card shadow-sm hover:shadow-md transition-all overflow-hidden flex flex-col group hover:border-primary/20"
              >
                {/* Card Header */}
                <div className="px-5 py-4 border-b border-border/40 bg-muted/20 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-sm text-primary tracking-tight">
                      {ticket.reference_id}
                    </span>
                    {getStatusBadge(ticket.status)}
                  </div>
                  <div>
                    {getUrgencyBadge(ticket.urgency)}
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-5 flex-1 space-y-4">
                  
                  {/* Who Needs Help */}
                  <div className="flex items-center gap-2.5">
                    <div className="size-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-xs font-bold">
                      <User className="size-4" />
                    </div>
                    <div>
                      <h4 className="font-bold text-sm text-foreground">{ticket.name}</h4>
                      <p className="text-[10px] text-muted-foreground flex items-center gap-1 mt-0.5">
                        <Clock className="size-3" />
                        {new Date(ticket.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {/* Summary of What Happened */}
                  <div className="bg-muted/30 p-3.5 rounded-xl border border-border/40 space-y-2">
                    <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-wider block">
                      Summary of Issue
                    </span>
                    <p className="text-xs text-foreground leading-relaxed font-medium">
                      {ticket.what_happened}
                    </p>
                  </div>

                  {/* What Was Checked */}
                  {ticket.checked && (
                    <div className="space-y-1.5">
                      <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-wider block">
                        Checked by Agent
                      </span>
                      <p className="text-xs text-muted-foreground leading-relaxed pl-1 font-medium border-l border-border">
                        {ticket.checked}
                      </p>
                    </div>
                  )}

                  {/* Follow-up Details */}
                  <div className="grid grid-cols-2 gap-3 pt-2 text-xs border-t border-border/30">
                    <div className="flex items-center gap-1.5 font-medium text-muted-foreground">
                      <Languages className="size-3.5 text-primary/80" />
                      <span>{ticket.language}</span>
                    </div>
                    <div className="flex items-center gap-1.5 font-medium text-muted-foreground justify-end">
                      {ticket.follow_up.toLowerCase() === 'call' ? (
                        <PhoneCall className="size-3.5 text-primary/80" />
                      ) : (
                        <Mail className="size-3.5 text-primary/80" />
                      )}
                      <span>{ticket.follow_up}</span>
                    </div>
                  </div>

                </div>

                {/* Card Actions Footer */}
                <div className="px-5 py-3 border-t border-border/40 bg-muted/10 flex items-center gap-2 justify-end">
                  {ticket.status === 'Open' && (
                    <>
                      <button
                        onClick={() => updateStatus(ticket.reference_id, 'In Progress')}
                        className="flex items-center gap-1 bg-primary/10 hover:bg-primary/20 border border-primary/25 px-3 py-1.5 rounded-lg text-[10px] font-bold text-primary transition-all cursor-pointer uppercase tracking-wider"
                      >
                        <Play className="size-3" />
                        In Progress
                      </button>
                      <button
                        onClick={() => updateStatus(ticket.reference_id, 'Resolved')}
                        className="flex items-center gap-1 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/25 px-3 py-1.5 rounded-lg text-[10px] font-bold text-emerald-500 transition-all cursor-pointer uppercase tracking-wider"
                      >
                        <CheckCircle2 className="size-3" />
                        Resolve
                      </button>
                    </>
                  )}
                  {ticket.status === 'In Progress' && (
                    <button
                      onClick={() => updateStatus(ticket.reference_id, 'Resolved')}
                      className="flex items-center gap-1 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/25 px-3 py-1.5 rounded-lg text-[10px] font-bold text-emerald-500 transition-all cursor-pointer uppercase tracking-wider"
                    >
                      <CheckCircle2 className="size-3" />
                      Resolve
                    </button>
                  )}
                  {ticket.status === 'Resolved' && (
                    <button
                      onClick={() => updateStatus(ticket.reference_id, 'Open')}
                      className="flex items-center gap-1 bg-card hover:bg-muted border border-border px-3 py-1.5 rounded-lg text-[10px] font-bold text-muted-foreground hover:text-foreground transition-all cursor-pointer uppercase tracking-wider"
                    >
                      Reopen
                    </button>
                  )}
                </div>

              </div>
            ))}
          </div>
        )}
      </div>

      {/* FOOTER */}
      <footer className="border-t border-border/50 pt-6 mt-12 flex flex-col md:flex-row items-center justify-between text-xs text-muted-foreground gap-4">
        <p>© 2026 Artha Saathi Help-Desk. All rights reserved.</p>
        <span className="font-semibold text-primary/80">Secured Financial Service Handoff System</span>
      </footer>
    </div>
  );
}
