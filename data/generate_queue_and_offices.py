import csv
import json
import os
import random
from datetime import date, timedelta

random.seed(7)

OFFICES = [
    # region, office_id, name, type, lat, lon, city
    ("IN","in_office_1","Mumbai Health & Welfare Centre","healthcare",19.0760,72.8777,"Mumbai"),
    ("IN","in_office_2","Andheri Benefit Centre","benefit_center",19.1197,72.8468,"Mumbai"),
    ("IN","in_office_3","Delhi Govt Service Office","government_office",28.6139,77.2090,"Delhi"),
    ("IN","in_office_4","Bengaluru Civic Hospital","healthcare",12.9716,77.5946,"Bengaluru"),
    ("US","us_office_1","Manhattan Community Health Center","healthcare",40.7831,-73.9712,"New York"),
    ("US","us_office_2","Brooklyn Benefits Office","benefit_center",40.6782,-73.9442,"New York"),
    ("US","us_office_3","LA County Social Services","government_office",34.0522,-118.2437,"Los Angeles"),
    ("US","us_office_4","Chicago Public Health Clinic","healthcare",41.8781,-87.6298,"Chicago"),
    ("BR","br_office_1","UBS Centro São Paulo","healthcare",-23.5505,-46.6333,"São Paulo"),
    ("BR","br_office_2","CRAS Zona Sul","benefit_center",-23.6105,-46.6433,"São Paulo"),
    ("BR","br_office_3","Rio Posto de Atendimento","government_office",-22.9068,-43.1729,"Rio de Janeiro"),
    ("BR","br_office_4","Brasília INSS Office","government_office",-15.7939,-47.8828,"Brasília"),
]

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "offices.json"), "w", encoding="utf-8") as f:
    json.dump([
        {"region":r,"office_id":oid,"name":n,"type":t,"lat":lat,"lon":lon,"city":city}
        for r,oid,n,t,lat,lon,city in OFFICES
    ], f, indent=2, ensure_ascii=False)

# ---- Queue history generation ----
HOLIDAYS_2025 = {"01-01","01-26","08-15","10-02","12-25","07-04","09-07","11-15"}  # mixed sample holidays

rows = []
start = date(2025, 1, 1)
days = 240  # ~8 months of history

for region, oid, name, otype, lat, lon, city in OFFICES:
    base_load = {"healthcare": 55, "benefit_center": 35, "government_office": 40}[otype]
    for d in range(days):
        cur_date = start + timedelta(days=d)
        dow = cur_date.weekday()  # 0=Mon
        is_holiday = cur_date.strftime("%m-%d") in HOLIDAYS_2025
        for hour in range(9, 17):  # office hours 9am-5pm
            weekend_factor = 0.5 if dow >= 5 else 1.0
            # lunchtime / early-morning peaks
            hour_factor = 1.3 if hour in (10, 11, 14, 15) else (0.7 if hour in (9, 16) else 1.0)
            holiday_factor = 1.6 if is_holiday else 1.0
            weather = random.choice(["clear","rain","extreme_heat","normal","storm"])
            weather_factor = {"clear":1.0,"normal":1.0,"rain":0.85,"extreme_heat":0.8,"storm":0.6}[weather]
            seasonal_factor = 1.0 + 0.15 * (1 if cur_date.month in (1,4,7,12) else 0)  # tax/season spikes

            visitors = max(0, int(base_load * weekend_factor * hour_factor * holiday_factor
                                    * weather_factor * seasonal_factor + random.gauss(0, 6)))
            wait_time = max(2, int(visitors * 0.9 + random.gauss(0, 5)))
            if visitors < 20:
                crowd = "low"
            elif visitors < 45:
                crowd = "moderate"
            else:
                crowd = "high"

            rows.append([
                region, oid, otype, cur_date.isoformat(), dow, hour,
                int(is_holiday), weather, round(seasonal_factor,2),
                visitors, wait_time, crowd
            ])

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "queue_history.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["region","office_id","office_type","date","day_of_week","hour",
                      "is_holiday","weather","seasonal_factor","num_visitors",
                      "actual_wait_time_minutes","crowd_level"])
    writer.writerows(rows)

print(f"Generated {len(rows)} queue history rows across {len(OFFICES)} offices.")
print(f"Generated {len(OFFICES)} office locations.")
