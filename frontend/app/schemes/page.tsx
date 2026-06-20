"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { FileText, ChevronDown, ChevronUp } from "lucide-react";

type Benefit = {
  id: string; region: string; name: string; category: string; description: string;
  documents_required: string[]; application_steps: string[];
};

const CATEGORIES = [
  "all", "child_support", "healthcare_support", "unemployment",
  "housing_assistance", "food_assistance", "disability_support", "elderly_care",
];

export default function SchemeNavigatorPage() {
  const [region, setRegion] = useState("US");
  const [category, setCategory] = useState("all");
  const [schemes, setSchemes] = useState<Benefit[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiFetch(`/api/benefits/all?region=${region}`)
      .then((res) => res.json())
      .then((data) => setSchemes(data))
      .finally(() => setLoading(false));
  }, [region]);

  const filtered = category === "all" ? schemes : schemes.filter((s) => s.category === category);

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-100 bg-white px-8 py-4">
        <div className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-white text-sm">C</span>
          Scheme navigator
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-8 py-10">
        <h1 className="font-display text-2xl font-semibold text-ink">Browse every program</h1>
        <p className="mt-2 text-sm text-slate-600">
          All public benefit schemes available in your region, with documents and steps up front.
        </p>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <div className="flex gap-2">
            {["US", "IN", "BR"].map((r) => (
              <button
                key={r}
                onClick={() => setRegion(r)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium ${
                  region === r ? "bg-brand-600 text-white" : "border border-slate-100 bg-white text-ink"
                }`}
              >
                {r === "US" ? "USA" : r === "IN" ? "India" : "Brazil"}
              </button>
            ))}
          </div>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="rounded-full border border-slate-100 bg-white px-4 py-1.5 text-sm font-medium text-ink"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c === "all" ? "All categories" : c.replace("_", " ")}</option>
            ))}
          </select>
        </div>

        {loading ? (
          <p className="mt-10 text-sm text-slate-600">Loading schemes...</p>
        ) : (
          <div className="mt-6 space-y-3">
            {filtered.map((s) => {
              const isOpen = expanded === s.id;
              return (
                <div key={s.id} className="card">
                  <button
                    onClick={() => setExpanded(isOpen ? null : s.id)}
                    className="flex w-full items-center justify-between text-left"
                  >
                    <div>
                      <p className="font-semibold text-ink">{s.name}</p>
                      <p className="mt-1 text-sm text-slate-600">{s.description}</p>
                      <span className="mt-2 inline-block rounded-full bg-brand-50 px-3 py-0.5 text-xs font-medium text-brand-700">
                        {s.category.replace("_", " ")}
                      </span>
                    </div>
                    {isOpen ? <ChevronUp size={18} className="text-slate-600" /> : <ChevronDown size={18} className="text-slate-600" />}
                  </button>

                  {isOpen && (
                    <div className="mt-4 grid gap-6 border-t border-slate-100 pt-4 md:grid-cols-2">
                      <div>
                        <p className="flex items-center gap-2 text-sm font-semibold text-ink">
                          <FileText size={14} className="text-brand-600" /> Documents required
                        </p>
                        <ul className="mt-2 space-y-1.5">
                          {s.documents_required.map((d) => (
                            <li key={d} className="flex items-center gap-2 text-sm text-slate-700">
                              <span className="h-1.5 w-1.5 rounded-full bg-slate-400" /> {d}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-ink">Application steps</p>
                        <ol className="mt-2 space-y-1.5">
                          {s.application_steps.map((step, i) => (
                            <li key={i} className="flex gap-2 text-sm text-slate-700">
                              <span className="font-medium text-brand-600">{i + 1}.</span> {step}
                            </li>
                          ))}
                        </ol>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            {filtered.length === 0 && (
              <p className="text-sm text-slate-600">No schemes found for this filter.</p>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
