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
- Modbus register profilleri [configs/modbus_profiles.json](/Users/tahatakgungor/dynamic_alert_project/configs/modbus_profiles.json) icinden yonetilir.
- Profil eslesmezse sistem generic read-only probe ile ham register verisi toplamayi dener.
- MQTT probe `DYNAMIC_ALERT_MQTT_PROBE_TOPICS` ile, SNMP probe ise community ve timeout ayarlariyla yonetilir.
- Passive observation, unknown traffic akisini cluster'a cevirip ileride protocol reverse engineering icin hafiza olusturur.
- Live capture icin `scapy` kullanilir; cihazda capture izni ve dogru network interface gerekir.

## Sonraki buyuk adimlar

1. Gercek Modbus/TCP tarama ve register okuma
2. Passive packet capture ile protocol fingerprinting
3. Telegram bot entegrasyonunun gercek token ile aktif edilmesi
4. Zaman serisi verisinin TimescaleDB / InfluxDB'ye alinmasi
5. Cihaz tarafinda systemd servisleri ve self-update mekanizmasi
6. Yerel model runtime ile semantic mapping yardimcisi
7. OPC UA adapteri
8. Passive packet capture ve protocol clustering
