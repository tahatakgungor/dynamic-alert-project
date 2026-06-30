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

Detaylar icin:

- [docs/platform_blueprint.md](/Users/tahatakgungor/dynamic_alert_project/docs/platform_blueprint.md)
- [docs/ui_strategy.md](/Users/tahatakgungor/dynamic_alert_project/docs/ui_strategy.md)
- [SECURITY.md](/Users/tahatakgungor/dynamic_alert_project/SECURITY.md)

## Kritik gerceklik

Agdaki tum makinelerin ozel veya proprietary protokollerini tek basina "otomatik cozmek" pratikte garanti edilemez. Bu ilk mimari su sirayi hedefler:

1. `Discovery`: cihaz, port, servis ve protokol siniflandirma
2. `Fingerprinting`: Modbus/TCP, raw TCP, D-Bus, HTTP, MQTT benzeri taninabilir yuzeyleri ayiklama
3. `Semantic Mapping`: bilinen register/payload tiplerini anlamli olcu birimlerine cevirme
4. `Heuristic Learning`: bilinmeyen akislari kural ve istatistikle aday metriklere donusturme
5. `Human-in-the-loop`: belirsiz veri haritalarini operator onayi ile kalici hale getirme

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
uvicorn dynamic_alert.main:app --reload
```

Sonra:

- Web arayuzu: `http://127.0.0.1:8000/`
- API dokumani: `http://127.0.0.1:8000/docs`

## Sonraki buyuk adimlar

1. Gercek Modbus/TCP tarama ve register okuma
2. Passive packet capture ile protocol fingerprinting
3. Telegram bot entegrasyonunun gercek token ile aktif edilmesi
4. Zaman serisi verisinin TimescaleDB / InfluxDB'ye alinmasi
5. Cihaz tarafinda systemd servisleri ve self-update mekanizmasi
