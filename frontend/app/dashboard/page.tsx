"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, logout } from "@/lib/api";
import { Sparkles, FileCheck2, MapPin, LogOut, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import ServiceMap from "@/components/ServiceMap";

type LifeEventResult = { category: string; confidence: number };
type Benefit = {
  id: string; name: string; category: string; description: string;
  priority_score: number; documents_required: string[];
  application_steps: string[]; priority_rank: number;
};
type RoadmapStep = { step: number; title: string; detail: string | string[] };
type QueueForecast = {
  predicted_wait_minutes: number; crowd_level: string;
  service_efficiency_score: number; date: string; weekday: string; hour: number;
};
type Roadmap = {
  benefit: { id: string; name: string; category: string };
  recommended_office: { name: string; city: string } | null;
  queue_forecast: QueueForecast | null;
  life_event_signal: { category: string; confidence: number; matches_benefit_category: boolean } | null;
  roadmap: RoadmapStep[];
};

export default function DashboardPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [situationText, setSituationText] = useState("");
  const [detecting, setDetecting] = useState(false);
  const [lifeEvent, setLifeEvent] = useState<LifeEventResult | null>(null);
  const [benefits, setBenefits] = useState<Benefit[]>([]);
  const [selectedBenefit, setSelectedBenefit] = useState<Benefit | null>(null);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [roadmapLoading, setRoadmapLoading] = useState(false);

  useEffect(() => {
    apiFetch("/api/profile/me").then(async (res) => {
      if (res.status === 401) {
        router.push("/login");
        return;
      }
      setProfile(await res.json());
    });
  }, [router]);

  async function detectLifeEvent() {
    if (!situationText.trim()) return;
    setDetecting(true);
    try {
      const res = await apiFetch("/api/life-event/detect", {
        method: "POST",
        body: JSON.stringify({ text: situationText }),
      });
      const data = await res.json();
      setLifeEvent(data.top_prediction);
      await fetchBenefits(data.top_prediction.category);
    } finally {
      setDetecting(false);
    }
  }

  async function fetchBenefits(categoryHint?: string) {
    const qs = categoryHint ? `?category_hint=${encodeURIComponent(categoryHint)}` : "";
    const res = await apiFetch(`/api/benefits/match${qs}`);
    if (res.ok) setBenefits(await res.json());
  }

  async function selectBenefit(benefit: Benefit) {
    setSelectedBenefit(benefit);
    setRoadmap(null);
    setRoadmapLoading(true);
    try {
      const params = new URLSearchParams({ region: profile?.region || "US" });
      if (lifeEvent) {
        params.set("life_event_category", lifeEvent.category);
        params.set("life_event_confidence", String(lifeEvent.confidence));
      }
      const res = await apiFetch(`/api/journey/roadmap/${benefit.id}?${params.toString()}`);
      if (res.ok) setRoadmap(await res.json());
    } finally {
      setRoadmapLoading(false);
    }
  }

  async function handleLogout() {
    await logout();
    router.push("/");
  }

  if (!profile) {
    return <div className="flex min-h-screen items-center justify-center text-slate-600">Loading...</div>;
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="flex items-center justify-between border-b border-slate-100 bg-white px-8 py-4">
        <div className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-white text-sm">C</span>
          CivicFlow AI
        </div>
        <div className="flex items-center gap-4">
          <Link href="/schemes" className="text-sm font-medium text-slate-600 hover:text-ink">Scheme navigator</Link>
          <Link href="/documents" className="text-sm font-medium text-slate-600 hover:text-ink">Documents</Link>
          <span className="text-sm text-slate-600">{profile.full_name || profile.email} · {profile.region}</span>
          <button onClick={handleLogout} className="flex items-center gap-1 text-sm font-medium text-slate-600 hover:text-ink">
            <LogOut size={14} /> Log out
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-8 py-10">
        {/* Life event detection */}
        <section className="card">
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
            <Sparkles size={18} className="text-brand-600" /> What's going on?
          </h2>
          <p className="mt-1 text-sm text-slate-600">Describe your situation in your own words.</p>
          <div className="mt-4 flex gap-3">
            <input
              value={situationText}
              onChange={(e) => setSituationText(e.target.value)}
              placeholder="e.g. I recently had a baby and need childcare help"
              className="flex-1 rounded-lg border border-slate-100 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none"
              onKeyDown={(e) => e.key === "Enter" && detectLifeEvent()}
            />
            <button onClick={detectLifeEvent} disabled={detecting} className="btn-primary">
              {detecting ? "Analyzing..." : "Analyze"}
            </button>
          </div>
          {lifeEvent && (
            <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-brand-50 px-4 py-2 text-sm font-medium text-brand-700">
              <CheckCircle2 size={16} />
              Detected: {lifeEvent.category.replace("_", " ")} ({Math.round(lifeEvent.confidence * 100)}% confidence)
            </div>
          )}
        </section>

        {/* Benefit matches */}
        {benefits.length > 0 && (
          <section className="mt-8">
            <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
              <FileCheck2 size={18} className="text-brand-600" /> Recommended services
            </h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {benefits.slice(0, 6).map((b) => (
                <button
                  key={b.id}
                  onClick={() => selectBenefit(b)}
                  className={`card text-left transition hover:border-brand-400 ${selectedBenefit?.id === b.id ? "border-brand-500 ring-1 ring-brand-200" : ""}`}
                >
                  <div className="flex items-center justify-between">
                    <p className="font-semibold text-ink">{b.name}</p>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                      #{b.priority_rank}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{b.description}</p>
                  <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-brand-500"
                      style={{ width: `${Math.round(b.priority_score * 100)}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-slate-600">
                    Priority score {Math.round(b.priority_score * 100)}/100 — you already qualify; this ranks how strongly
                  </p>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Live service map */}
        <section className="mt-8 card">
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
            <MapPin size={18} className="text-brand-600" /> Live service map — {profile.region}
          </h2>
          <p className="mt-1 text-sm text-slate-600">Green = low crowd · Amber = moderate · Red = high</p>
          <div className="mt-4">
            <ServiceMap region={profile.region} />
          </div>
        </section>

        {/* Selected benefit detail: roadmap + documents */}
        {selectedBenefit && (
          <section className="mt-8 grid gap-6 md:grid-cols-2">
            <div className="card">
              <h3 className="flex items-center gap-2 font-display font-semibold text-ink">
                <MapPin size={16} className="text-brand-600" /> Your action plan
              </h3>
              {roadmapLoading && (
                <p className="mt-4 text-sm text-slate-500">Building your roadmap…</p>
              )}
              {!roadmapLoading && roadmap && (
                <>
                  <ol className="mt-4 space-y-3">
                    {roadmap.roadmap.map((s) => (
                      <li key={s.step} className="flex gap-3 text-sm">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700">
                          {s.step}
                        </span>
                        <span className="text-slate-700">
                          <span className="font-medium">{s.title}</span>
                          {typeof s.detail === "string" && s.detail && (
                            <span className="block text-slate-500">{s.detail}</span>
                          )}
                          {Array.isArray(s.detail) && s.detail.length > 0 && (
                            <span className="block text-slate-500">{s.detail.join(", ")}</span>
                          )}
                        </span>
                      </li>
                    ))}
                  </ol>
                  {roadmap.queue_forecast && (
                    <p className="mt-4 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                      Queue model forecast for {roadmap.recommended_office?.name}: predicted wait{" "}
                      {roadmap.queue_forecast.predicted_wait_minutes} min, crowd level{" "}
                      {roadmap.queue_forecast.crowd_level} on {roadmap.queue_forecast.weekday}{" "}
                      {roadmap.queue_forecast.date} at {roadmap.queue_forecast.hour}:00.
                    </p>
                  )}
                </>
              )}
              {!roadmapLoading && !roadmap && (
                <ol className="mt-4 space-y-3">
                  {selectedBenefit.application_steps.map((step, i) => (
                    <li key={i} className="flex gap-3 text-sm">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700">
                        {i + 1}
                      </span>
                      <span className="text-slate-700">{step}</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>

            <div className="card">
              <h3 className="flex items-center gap-2 font-display font-semibold text-ink">
                <FileCheck2 size={16} className="text-brand-600" /> Documents needed
              </h3>
              <ul className="mt-4 space-y-2">
                {selectedBenefit.documents_required.map((doc) => (
                  <li key={doc} className="flex items-center gap-2 text-sm text-slate-700">
                    <span className="h-1.5 w-1.5 rounded-full bg-slate-400" /> {doc}
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {!lifeEvent && (
          <p className="mt-10 text-center text-sm text-slate-600">
            Describe your situation above to get personalized recommendations.
          </p>
        )}
      </div>
    </main>
  );
}
