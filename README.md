# Dynamic Alert Project

Endustriyel makineleri ag uzerinden kesfeden, protokollerini siniflandiran, veriyi anlamli olaylara donusturen ve ilk asamada Telegram ile bildirim ureten bir edge-gozlem platformu.

## Vizyon

Bu proje iki cekirdek parcadan olusur:

1. `Edge Agent`
   Agdaki cihazlari bulur, protokol parmak izi cikarir, veri toplar ve normalize eder.
2. `Control Center`
   Web arayuzu, alarm kurallari, cihaz gozlemi, bildirim yonetimi ve API katmani.

## Bu ilk surum ne sagliyor?

- FastAPI tabanli bir kontrol merkezi
- SQLite tabanli temel veri modeli
- Cihaz, protocol fingerprint ve telemetry kayitlari
- Dinamik alarm kurali motoru
- Telegram bildirimi icin genisletilebilir notifier katmani
- Protocol adapter mimarisi (`modbus`, `dbus`, `tcp`)
- Ornek ag kesfi ve veri toplama akisi
- Raspberry Pi / Jetson dostu deploy dokumani
- GitHub CI ve repo guvenlik/dokumantasyon iskeleti

## Modern teknoloji yonu

Temel secimler:

- `FastAPI`
- `Pydantic v2`
- `pydantic-settings`
- `SQLAlchemy 2.x`
- `Jinja2` tabanli ilk panel

Hedeflenen buyume yolu:

- `PostgreSQL + Alembic`
- `Redis`
- `NATS veya Redpanda`
- `OpenTelemetry`
- `React/Next.js` tabanli operasyon konsolu
- `PyModbus` tabanli read-only endustriyel veri toplama
- `pysnmp` ve `paho-mqtt` tabanli cok protokollu kesif

Detaylar icin:

- [docs/platform_blueprint.md](/Users/tahatakgungor/dynamic_alert_project/docs/platform_blueprint.md)
- [docs/ui_strategy.md](/Users/tahatakgungor/dynamic_alert_project/docs/ui_strategy.md)
- [docs/ai_strategy.md](/Users/tahatakgungor/dynamic_alert_project/docs/ai_strategy.md)
- [docs/discovery_strategy.md](/Users/tahatakgungor/dynamic_alert_project/docs/discovery_strategy.md)
- [SECURITY.md](/Users/tahatakgungor/dynamic_alert_project/SECURITY.md)

## Kritik gerceklik

Agdaki tum makinelerin ozel veya proprietary protokollerini tek basina "otomatik cozmek" pratikte garanti edilemez. Bu ilk mimari su sirayi hedefler:

1. `Discovery`: cihaz, port, servis ve protokol siniflandirma
2. `Fingerprinting`: Modbus/TCP, SNMP, MQTT, raw TCP, D-Bus, HTTP benzeri taninabilir yuzeyleri ayiklama
3. `Register/Profile Reads`: bilinen cihazlar icin dogrudan register okuma
4. `Semantic Mapping`: bilinen register/payload tiplerini anlamli olcu birimlerine cevirme
5. `Heuristic Learning`: bilinmeyen akislari kural ve istatistikle aday metriklere donusturme
6. `Model-assisted Semantics`: hazir kucuk modellerle semantic yorum guclendirme
7. `Human-in-the-loop`: belirsiz veri haritalarini operator onayi ile kalici hale getirme

## Hedef mimari

Detaylar icin:

- [docs/architecture.md](/Users/tahatakgungor/dynamic_alert_project/docs/architecture.md)
- [docs/deployment.md](/Users/tahatakgungor/dynamic_alert_project/docs/deployment.md)
- [docs/platform_blueprint.md](/Users/tahatakgungor/dynamic_alert_project/docs/platform_blueprint.md)

## Hizli baslangic

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn dynamic_alert.main:app --reload
```

Sonra:

- Web arayuzu: `http://127.0.0.1:8000/`
- API dokumani: `http://127.0.0.1:8000/docs`

Not:

- Yonetimsel endpointler `X-API-Key` ister.
- Varsayilan bootstrap anahtari sadece gelistirme icindir, uretimde degistirilmelidir.
- Uretimde uygulama varsayilan `change-me-before-production` bootstrap key ile baslatilmaz.
- Modbus register profilleri [configs/modbus_profiles.json](/Users/tahatakgungor/dynamic_alert_project/configs/modbus_profiles.json) icinden yonetilir.
- Profil eslesmezse sistem generic read-only probe ile ham register verisi toplamayi dener.
- MQTT probe `DYNAMIC_ALERT_MQTT_PROBE_TOPICS` ile, SNMP probe ise community ve timeout ayarlariyla yonetilir.
- Passive observation, unknown traffic akisini cluster'a cevirip ileride protocol reverse engineering icin hafiza olusturur.
- Live capture icin `scapy` kullanilir; cihazda capture izni ve dogru network interface gerekir.
- Unknown traffic akislari candidate dataset olarak saklanir; bu katman operator onayi ve ileri AI icin temel olur.
- OPC UA icin generic numeric node okuma girisi vardir; cihaz yapisina gore ileride profile/browse stratejisi gelistirilecektir.
- Operator semantic map tanimlayabilir; sistem sonraki telemetry akislarinda bu map'i heuristic'in onune koyar.
- Telegram token tanimliysa notifier gercek `sendMessage` istegi gonderir; token yoksa `dry-run` davranisi devam eder.
- Alarm kurallari semantic tahmin sonucu uretilecek anahtarlar icin de tetiklenebilir; ornegin ham `dbus_sensor_temperature_raw` akisi `temperature_c` olarak anlamlandirilip kurali tetikleyebilir.
- `scan`, `passive-observe`, `live-capture` ve demo akislari artik arka plan job'u olarak kuyruga alinir; durum `/api/jobs` ve `/api/jobs/{job_id}` ile izlenir.
- Arka plan job kayitlari veritabaninda da tutulur; servis yeniden baslasa bile job gecmisi panel ve API uzerinden gorulebilir.
- Yeni yon: merkezi control plane + edge node modeli. Edge node kaydi, heartbeat, job queue, claim ve result raporlama icin ilk API iskeleti eklendi.
- [docs/smoke_test_matrix.md](/Users/tahatakgungor/dynamic_alert_project/docs/smoke_test_matrix.md) gercekci saha dogrulama senaryolarini listeler.

## Edge Agent Ilk Kullanim

Merkezi panelde bir edge node kaydet:

```bash
dynamic-alert-edge-agent register \
  --control-plane-url http://127.0.0.1:8000 \
  --admin-api-key change-me-before-production \
  --name factory-edge-01 \
  --site-code HQ-PLANT
```

Bu komut bir `node_key` dondurur. Sonra edge cihazda tek tur calistir:

```bash
dynamic-alert-edge-agent run-once \
  --control-plane-url http://127.0.0.1:8000 \
  --edge-key EDGE_NODE_KEY
```

Surekli poll eden agent icin:

```bash
dynamic-alert-edge-agent run \
  --control-plane-url http://127.0.0.1:8000 \
  --edge-key EDGE_NODE_KEY
```

Edge job payload ile hedefli isler gonderilebilir. Ornekler:

- `scan` icin: `{"scan_subnets": ["10.20.30.0/24"]}`
- `live-capture` icin:
  `{"packet_capture_interface":"eth1","packet_capture_timeout_seconds":10,"packet_capture_max_packets":200,"packet_capture_bpf_filter":"tcp port 502"}`
- `passive-observe` icin custom sample listesi:
  `{"samples":[{"source_ip":"10.0.0.10","source_port":40001,"destination_ip":"10.0.0.20","destination_port":502,"transport":"tcp","payload_sample":"010300000002"}]}`
- `dbus-demo` icin:
  `{"site_code":"HQ-PLANT","ip_address":"192.168.10.50","hostname":"edge-temp-gw","vendor":"Linux Edge Gateway","open_ports":[22,80]}`

Ek olarak `enabled_protocols` ile scan veya demo job'larinda hangi adapter'larin aktif olacagi secilebilir:

- `{"enabled_protocols":["modbus_tcp","snmp","mqtt"]}`

Panel tarafinda artik bir `Edge Orchestration` formu vardir; edge node secimi, protocol toggle'lari ve temel probe tuning alanlariyla JSON yazmadan job olusturulabilir.

## Telegram ve demo smoke test

`.env` icine asgari olarak sunlari koy:

```bash
DYNAMIC_ALERT_TELEGRAM_BOT_TOKEN=123456:example
DYNAMIC_ALERT_TELEGRAM_CHAT_ID=123456789
```

Sonra operator API key ile ornek D-Bus sicaklik akisini tetikle:

```bash
curl -X POST http://127.0.0.1:8000/api/demo/dbus-temperature-alert \
  -H 'X-API-Key: change-me-before-production'
```

Bu demo su zinciri calistirir:

1. `dbus_gateway` olarak ornek bir Linux edge cihazini ingest eder.
2. `dbus_sensor_temperature_raw` telemetry'si uretir.
3. Semantic katman bunu `temperature_c` olarak yorumlar.
4. `temperature_c >= 70` kuralini tetikler.
5. Telegram token varsa gercek mesaj gonderir; yoksa uygulama `dry-run` log'u yazar.

## Sonraki buyuk adimlar

1. Gercek Modbus/TCP tarama ve register okuma
2. Passive packet capture ile protocol fingerprinting
3. Telegram bot entegrasyonunun gercek token ile aktif edilmesi
4. Zaman serisi verisinin TimescaleDB / InfluxDB'ye alinmasi
5. Cihaz tarafinda systemd servisleri ve self-update mekanizmasi
6. Yerel model runtime ile semantic mapping yardimcisi
7. OPC UA adapteri
8. Passive packet capture ve protocol clustering
