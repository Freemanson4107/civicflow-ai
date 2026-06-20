"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { apiFetch } from "@/lib/api";

const MapContainer = dynamic(() => import("react-leaflet").then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then((m) => m.TileLayer), { ssr: false });
const CircleMarker = dynamic(() => import("react-leaflet").then((m) => m.CircleMarker), { ssr: false });
const Popup = dynamic(() => import("react-leaflet").then((m) => m.Popup), { ssr: false });

type Office = { office_id: string; name: string; type: string; lat: number; lon: number; city: string; region: string };

const CROWD_COLORS: Record<string, string> = {
  low: "#16A34A",
  moderate: "#D97706",
  high: "#DC2626",
};

const REGION_CENTER: Record<string, [number, number]> = {
  US: [39.8283, -98.5795],
  IN: [22.3511, 78.6677],
  BR: [-14.235, -51.9253],
};

export default function ServiceMap({ region }: { region: "US" | "IN" | "BR" }) {
  const [offices, setOffices] = useState<Office[]>([]);
  const [crowdByOffice, setCrowdByOffice] = useState<Record<string, string>>({});

  useEffect(() => {
    apiFetch(`/api/offices?region=${region}`).then(async (res) => {
      const data: Office[] = await res.json();
      setOffices(data);

      const today = new Date().toISOString().slice(0, 10);
      const hour = new Date().getHours();
      const results: Record<string, string> = {};
      await Promise.all(
        data.map(async (o) => {
          const res2 = await apiFetch("/api/queue/predict", {
            method: "POST",
            body: JSON.stringify({ office_id: o.office_id, date: today, hour, weather: "normal" }),
          });
          if (res2.ok) {
            const pred = await res2.json();
            results[o.office_id] = pred.crowd_level;
          }
        })
      );
      setCrowdByOffice(results);
    });
  }, [region]);

  return (
    <div className="h-[420px] w-full overflow-hidden rounded-xl2">
      <MapContainer center={REGION_CENTER[region]} zoom={4} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {offices.map((o) => (
          <CircleMarker
            key={o.office_id}
            center={[o.lat, o.lon]}
            radius={10}
            pathOptions={{
              color: CROWD_COLORS[crowdByOffice[o.office_id] || "moderate"],
              fillColor: CROWD_COLORS[crowdByOffice[o.office_id] || "moderate"],
              fillOpacity: 0.6,
            }}
          >
            <Popup>
              <strong>{o.name}</strong>
              <br />
              {o.city} — {o.type.replace("_", " ")}
              <br />
              Crowd level: {crowdByOffice[o.office_id] || "loading..."}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
