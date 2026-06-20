"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Upload, FileCheck2, AlertCircle, CheckCircle2 } from "lucide-react";

type Benefit = { id: string; name: string; documents_required: string[] };
type ScanResult = { document_type: string; detected: boolean; confidence: number; missing_fields: string[] };

export default function DocumentsPage() {
  const [region, setRegion] = useState("US");
  const [benefits, setBenefits] = useState<Benefit[]>([]);
  const [selectedBenefitId, setSelectedBenefitId] = useState("");
  const [submittedDocs, setSubmittedDocs] = useState<string[]>([]);
  const [checklist, setChecklist] = useState<any>(null);
  const [scanning, setScanning] = useState(false);
  const [lastScan, setLastScan] = useState<ScanResult | null>(null);

  useEffect(() => {
    apiFetch(`/api/benefits/all?region=${region}`)
      .then((res) => res.json())
      .then((data) => {
        setBenefits(data);
        setSelectedBenefitId(data[0]?.id || "");
      });
  }, [region]);

  useEffect(() => {
    if (!selectedBenefitId) return;
    const qs = submittedDocs.length ? `?submitted=${encodeURIComponent(submittedDocs.join(","))}` : "";
    apiFetch(`/api/documents/checklist/${selectedBenefitId}${qs}`)
      .then((res) => res.json())
      .then(setChecklist);
  }, [selectedBenefitId, submittedDocs]);

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setScanning(true);
    setLastScan(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await apiFetch("/api/documents/scan", { method: "POST", body: formData });
      const result: ScanResult = await res.json();
      setLastScan(result);
      if (result.detected && !submittedDocs.includes(result.document_type)) {
        setSubmittedDocs([...submittedDocs, result.document_type]);
      }
    } finally {
      setScanning(false);
      e.target.value = "";
    }
  }

  const selectedBenefit = benefits.find((b) => b.id === selectedBenefitId);

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-100 bg-white px-8 py-4">
        <div className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-white text-sm">C</span>
          Document readiness
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-8 py-10">
        <h1 className="font-display text-2xl font-semibold text-ink">Check your documents before you go</h1>
        <p className="mt-2 text-sm text-slate-600">
          Scan documents and we'll match them against what's required — so you don't get turned away at the office.
        </p>

        <div className="mt-6 flex gap-3">
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

        <div className="mt-6 card">
          <label className="text-sm font-medium text-ink">Which program are you applying for?</label>
          <select
            value={selectedBenefitId}
            onChange={(e) => { setSelectedBenefitId(e.target.value); setSubmittedDocs([]); setLastScan(null); }}
            className="mt-2 w-full rounded-lg border border-slate-100 px-4 py-2.5 text-sm"
          >
            {benefits.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <div className="card">
            <p className="flex items-center gap-2 font-semibold text-ink">
              <Upload size={16} className="text-brand-600" /> Scan a document
            </p>
            <p className="mt-1 text-sm text-slate-600">Upload a photo of your document — OCR detects the type automatically.</p>
            <label className="mt-4 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center hover:border-brand-400">
              <Upload size={24} className="text-slate-400" />
              <span className="mt-2 text-sm font-medium text-ink">{scanning ? "Scanning..." : "Click to upload"}</span>
              <span className="text-xs text-slate-500">PNG or JPEG</span>
              <input type="file" accept="image/png,image/jpeg" onChange={handleFileUpload} className="hidden" disabled={scanning} />
            </label>

            {lastScan && (
              <div className={`mt-4 flex items-start gap-2 rounded-lg p-3 text-sm ${lastScan.detected ? "bg-green-50 text-green-800" : "bg-amber-50 text-amber-800"}`}>
                {lastScan.detected ? <CheckCircle2 size={16} className="mt-0.5 shrink-0" /> : <AlertCircle size={16} className="mt-0.5 shrink-0" />}
                <span>
                  {lastScan.detected
                    ? `Detected: ${lastScan.document_type} (${Math.round(lastScan.confidence * 100)}% confidence)`
                    : "Couldn't confidently identify this document. Try a clearer photo."}
                </span>
              </div>
            )}
          </div>

          <div className="card">
            <p className="flex items-center gap-2 font-semibold text-ink">
              <FileCheck2 size={16} className="text-brand-600" /> Readiness checklist
            </p>
            {checklist && (
              <>
                <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-brand-500" style={{ width: `${checklist.readiness_percent}%` }} />
                </div>
                <p className="mt-1 text-xs text-slate-600">{checklist.readiness_percent}% ready</p>

                <ul className="mt-4 space-y-2">
                  {checklist.required_documents.map((doc: string) => {
                    const have = checklist.submitted_documents.includes(doc);
                    return (
                      <li key={doc} className="flex items-center gap-2 text-sm">
                        {have ? (
                          <CheckCircle2 size={15} className="text-green-600" />
                        ) : (
                          <span className="h-3.5 w-3.5 rounded-full border-2 border-slate-300" />
                        )}
                        <span className={have ? "text-ink" : "text-slate-600"}>{doc}</span>
                      </li>
                    );
                  })}
                </ul>
              </>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
