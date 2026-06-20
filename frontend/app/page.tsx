import Link from "next/link";
import { ArrowRight, MapPin, FileCheck2, Clock3, ShieldCheck, Sparkles } from "lucide-react";

const ROUTE_STOPS = [
  { label: "Tell us what's happening", icon: Sparkles, sub: "\u201cI lost my job\u201d" },
  { label: "Get matched to benefits", icon: FileCheck2, sub: "Ranked by eligibility" },
  { label: "Know your wait time", icon: Clock3, sub: "Before you leave home" },
  { label: "Arrive at the right office", icon: MapPin, sub: "At the right time" },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Nav */}
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2 text-lg font-semibold text-ink">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-white text-sm">C</span>
          CivicFlow AI
        </div>
        <nav className="hidden gap-8 text-sm font-medium text-slate-600 md:flex">
          <a href="#how-it-works" className="hover:text-ink">How it works</a>
          <a href="#impact" className="hover:text-ink">Impact</a>
          <a href="#demo" className="hover:text-ink">Live demo</a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm font-semibold text-ink hover:text-brand-600">Log in</Link>
          <Link href="/signup" className="btn-primary">Get started</Link>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pt-12 pb-20 md:pt-20">
        <div className="grid items-center gap-16 md:grid-cols-2">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-4 py-1.5 text-xs font-semibold text-brand-700">
              <ShieldCheck size={14} /> Available in India · USA · Brazil
            </span>
            <h1 className="mt-6 font-display text-5xl font-semibold leading-[1.05] tracking-tight text-ink md:text-6xl">
              Navigate public services with confidence
            </h1>
            <p className="mt-6 max-w-md text-lg leading-relaxed text-slate-600">
              AI-powered guidance for healthcare, benefits, and government services —
              so you know exactly which office to visit, when to go, and what to bring.
            </p>
            <div className="mt-8 flex items-center gap-4">
              <Link href="/signup" className="btn-primary">
                Start your journey <ArrowRight size={16} className="ml-2" />
              </Link>
              <a href="#demo" className="btn-secondary">See it in action</a>
            </div>
          </div>

          {/* Signature element: the service route line */}
          <div className="relative rounded-xl2 border border-slate-100 bg-slate-50/60 p-8">
            <p className="mb-6 text-xs font-semibold uppercase tracking-wide text-slate-600">
              Your route to support
            </p>
            <ol className="relative">
              {ROUTE_STOPS.map((stop, i) => {
                const Icon = stop.icon;
                const isLast = i === ROUTE_STOPS.length - 1;
                return (
                  <li key={stop.label} className="relative flex gap-4 pb-10 last:pb-0">
                    {!isLast && (
                      <span className="absolute left-[19px] top-10 h-[calc(100%-1rem)] w-px bg-gradient-to-b from-brand-400 to-brand-100" />
                    )}
                    <span className="z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-brand-600 shadow-card ring-1 ring-slate-100">
                      <Icon size={18} />
                    </span>
                    <div>
                      <p className="font-semibold text-ink">{stop.label}</p>
                      <p className="text-sm text-slate-600">{stop.sub}</p>
                    </div>
                  </li>
                );
              })}
            </ol>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="font-display text-3xl font-semibold text-ink">Five AI systems, one journey</h2>
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {[
            { title: "Life event detection", desc: "Tell us what's going on in plain language — we identify the right support category." },
            { title: "Benefit matching", desc: "Personalized eligibility scoring against real program rules for your region." },
            { title: "Queue forecasting", desc: "ML-predicted wait times and crowd levels before you leave the house." },
            { title: "Document readiness", desc: "OCR-powered checks confirm you have what you need before you go." },
            { title: "Journey optimizer", desc: "A step-by-step roadmap from situation to resolved, like turn-by-turn directions." },
            { title: "Live service map", desc: "See crowd levels at nearby hospitals, benefit centers, and offices in real time." },
          ].map((f) => (
            <div key={f.title} className="card">
              <p className="font-semibold text-ink">{f.title}</p>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Impact */}
      <section id="impact" className="mx-auto max-w-6xl px-6 py-20">
        <div className="grid gap-8 rounded-xl2 bg-ink px-10 py-16 text-white md:grid-cols-3">
          <div>
            <p className="font-display text-4xl font-semibold">3 regions</p>
            <p className="mt-2 text-sm text-slate-300">India, USA, and Brazil benefit programs mapped today.</p>
          </div>
          <div>
            <p className="font-display text-4xl font-semibold">81%</p>
            <p className="mt-2 text-sm text-slate-300">Crowd-level prediction accuracy from our forecasting model.</p>
          </div>
          <div>
            <p className="font-display text-4xl font-semibold">7 categories</p>
            <p className="mt-2 text-sm text-slate-300">Of life events automatically detected from natural language.</p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section id="demo" className="mx-auto max-w-6xl px-6 py-20 text-center">
        <h2 className="font-display text-3xl font-semibold text-ink">Ready to see your route?</h2>
        <p className="mt-4 text-slate-600">Create a free account and get matched in under a minute.</p>
        <Link href="/signup" className="btn-primary mt-8 inline-flex">
          Get started <ArrowRight size={16} className="ml-2" />
        </Link>
      </section>

      <footer className="border-t border-slate-100 px-6 py-10 text-center text-sm text-slate-600">
        © {new Date().getFullYear()} CivicFlow AI. Built for global public service access.
      </footer>
    </main>
  );
}
