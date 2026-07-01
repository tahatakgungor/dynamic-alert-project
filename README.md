# Dynamic Alert Project

Dynamic Alert Project, endustriyel veya operasyonel aglarda calisan cihazlari kesfetmek, guvenli read-only protokollerle veri toplamak, ham veriyi semantic olarak anlamlandirmak ve sonucu alarm/entegrasyon akisina cevirmek icin tasarlanmis `edge-first` bir kontrol duzlemi ve edge agent platformudur.

Bugunku mimari artik tek makinede demo eden bir API iskeletinden cikti. Sistem su modele evrildi:

1. `Control Plane`
   Web arayuzu, API, alarm kurallari, semantic workflow, audit ve edge node/job yonetimi.
2. `Edge Agent`
   Fabrikanin veya sahadaki yerel agin icinde calisir; merkezi panelden is claim eder, tarama/capture/protokol gorevlerini yerelde yurutur ve sonucu geri raporlar.

## Su an ne calisiyor?

- FastAPI tabanli control plane
- SQLite + SQLAlchemy + Alembic veri modeli
- API key tabanli auth ve temel `viewer / operator / admin` RBAC
- Protocol adapter mimarisi
- `Modbus/TCP`, `SNMP`, `MQTT`, `OPC UA`, `raw TCP`, `D-Bus gateway heuristic`
- Passive observation, flow cluster ve unknown protocol candidate katmani
- Semantic hypothesis, semantic map ve operator onay akisi
- Semantic metric uzerinden alarm tetikleme
- Telegram notifier
- Background job queue + DB-backed job history
- Edge node register / heartbeat / job queue / claim / completion akisi
- `dynamic-alert-edge-agent` CLI
- Edge job payload ile protocol orchestration
- Web panelde edge orchestration formu, audit, alarm, candidate ve semantic workflow gorunurlugu
- Gercekci smoke test matrix ve control plane <-> edge agent roundtrip testi

## Kritik gerceklik

Bu proje, “agdaki her cihazi otomatik olarak eksiksiz anlar” varsayimi uzerine kurulu degildir.

Gercekci calisma modeli su sira ile ilerler:

1. `Discovery`
2. `Protocol fingerprinting`
3. `Safe read-only probing`
4. `Passive observation`
5. `Semantic inference`
6. `Operator confirmation`

Yani hedef sihirli reverse engineering degil; kontrollu gozetim, semantic yardim ve insan-onayli ogrenmedir.

## Mimarinin bugunku ozeti

### Control Plane

- Site, workspace, integration, edge node ve edge job yonetimi
- Alarm kurallari ve alert event kayitlari
- Semantic hypothesis ve semantic map workflow'u
- Audit log ve operasyon gorunurlugu
- Edge agent'lara is dagitimi

### Edge Agent

- Control plane'e register olur
- `heartbeat` ile canlilik bildirir
- Kendi node'una atanmis edge job'lari claim eder
- Payload'a gore scan/capture/demo gorevlerini yerelde calistirir
- Sonucu geri raporlar

### Veri katmanlari

- `TelemetryRecord`
- `ProtocolFingerprint`
- `TrafficObservation`
- `FlowCluster`
- `UnknownProtocolCandidate`
- `SemanticHypothesis`
- `SemanticMap`
- `AlertEvent`
- `AuditLog`
- `BackgroundJobRecord`
- `EdgeNode`
- `EdgeJob`

## Teknoloji secimleri

- `Python 3.11+`
- `FastAPI`
- `Pydantic v2`
- `pydantic-settings`
- `SQLAlchemy 2.x`
- `Alembic`
- `Jinja2`
- `PyModbus`
- `pysnmp`
- `paho-mqtt`
- `asyncua`
- `scapy`

## Hizli baslangic

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn dynamic_alert.main:app --reload
```

Sonra:

- Panel: `http://127.0.0.1:8000/`
- API dokumani: `http://127.0.0.1:8000/docs`

## Onemli calisma notlari

- Yonetimsel endpointler `X-API-Key` ister.
- Varsayilan bootstrap key yalnizca development icindir.
- Uygulama production benzeri ortamda `change-me-before-production` ile baslatilmaz.
- Telegram token varsa notifier gercek `sendMessage` cagrisi yapar; yoksa `dry-run` modundadir.
- `scan`, `passive-observe`, `live-capture` ve demo akislar background job olarak kosar.
- Background job kayitlari veritabaninda tutulur.
- Edge job kayitlari de veritabaninda tutulur.
- Live capture icin `scapy` ve uygun interface/izin gerekir.
- Protocol davranisi varsayilan olarak read-only tutulmalidir.

## Edge Agent kullanim akisi

### 1. Edge node register et

```bash
dynamic-alert-edge-agent register \
  --control-plane-url http://127.0.0.1:8000 \
  --admin-api-key change-me-before-production \
  --name factory-edge-01 \
  --site-code HQ-PLANT
```

Bu komut bir `node_key` dondurur.

### 2. Edge agent'i tek tur calistir

```bash
dynamic-alert-edge-agent run-once \
  --control-plane-url http://127.0.0.1:8000 \
  --edge-key EDGE_NODE_KEY
```

### 3. Surekli poll eden ajan

```bash
dynamic-alert-edge-agent run \
  --control-plane-url http://127.0.0.1:8000 \
  --edge-key EDGE_NODE_KEY
```

## Edge job payload ornekleri

### Scan

```json
{
  "scan_subnets": ["10.20.30.0/24"],
  "enabled_protocols": ["modbus_tcp", "snmp", "mqtt"],
  "modbus_profile_set": "generic_plc",
  "mqtt_topic_set": "telemetry_focus",
  "snmp_oid_set": "standard_mib2",
  "modbus_generic_probe_count": 8,
  "mqtt_probe_max_messages": 5,
  "opcua_max_nodes": 16
}
```

`modbus_profile_set`, `configs/modbus_profiles.json` icindeki isimlendirilmis profil kataloglarindan birini secmek icin kullanilir. `modbus_profiles_path` hala desteklenir, ancak bu alan artik yalnizca farkli bir profil dosyasi enjekte etmek isteyen ileri seviye kullanimlar icin dusunulmelidir.
`mqtt_topic_set` ve `snmp_oid_set` de benzer sekilde named catalog secimi yapar. Ham `mqtt_probe_topics` ve `snmp_oid_*` override alanlari korunur, ancak artik ileri seviye elle override senaryolari icin dusunulmelidir.

### Live capture

```json
{
  "packet_capture_interface": "eth1",
  "packet_capture_timeout_seconds": 10,
  "packet_capture_max_packets": 200,
  "packet_capture_bpf_filter": "tcp port 502",
  "enabled_protocols": ["raw_tcp", "modbus_tcp"]
}
```

### Passive observe

```json
{
  "samples": [
    {
      "source_ip": "10.0.0.10",
      "source_port": 40001,
      "destination_ip": "10.0.0.20",
      "destination_port": 502,
      "transport": "tcp",
      "payload_sample": "010300000002"
    }
  ]
}
```

### D-Bus demo

```json
{
  "site_code": "HQ-PLANT",
  "ip_address": "192.168.10.50",
  "hostname": "edge-temp-gw",
  "vendor": "Linux Edge Gateway",
  "open_ports": [22, 80],
  "enabled_protocols": ["dbus_gateway"]
}
```

## Web arayuzu

Panel artik yalnizca ham listeleyen bir dashboard degil:

- ozet metrikler gosterir
- edge node ve edge job durumunu gosterir
- edge orchestration formu ile JSON yazmadan edge job olusturur
- semantic hypothesis -> semantic map promote akisina izin verir
- unknown candidate icin `confirm / dismiss / escalate` aksiyonlari sunar
- alarm olaylarini ve audit log'lari gorunur kilir

Bu yuzden urunun kullanimi icin asgari is akisi su sekilde dusunulmelidir:

1. Site ve edge node kur
2. Edge agent'i register et
3. Panelden edge job olustur
4. Agent claim edip calistirsin
5. Sonuclari panelde semantic/alarm/audit olarak incele

## Telegram demo akisi

`.env` icine asgari olarak:

```bash
DYNAMIC_ALERT_TELEGRAM_BOT_TOKEN=123456:example
DYNAMIC_ALERT_TELEGRAM_CHAT_ID=123456789
```

Ardindan:

```bash
curl -X POST http://127.0.0.1:8000/api/demo/dbus-temperature-alert \
  -H 'X-API-Key: change-me-before-production'
```

Bu zinciri test eder:

1. D-Bus demo telemetry
2. Semantic yorum
3. `temperature_c` uzerinden alarm tetigi
4. Telegram veya dry-run bildirimi

## Dogrulama ve smoke test

Gercekci saha dogrulama senaryolari:

- [docs/smoke_test_matrix.md](/Users/tahatakgungor/dynamic_alert_project/docs/smoke_test_matrix.md)

Bu matrix su alanlari kapsar:

- control plane baslangici
- edge node register
- heartbeat
- edge job queue
- claim -> execute -> complete zinciri
- D-Bus semantic alarm zinciri
- passive observe / live capture
- operator workflow
- audit / forensics
- production sertlestirme

## Guvenlik

Guvenlik notlari:

- [SECURITY.md](/Users/tahatakgungor/dynamic_alert_project/SECURITY.md)

Ozel dikkat edilmesi gerekenler:

- Varsayilan bootstrap key production'da kullanilmaz
- Edge payload boyutu ve tipi sinirlanmistir
- Edge status ve job kind whitelist ile dogrulanir
- Protocol adapterleri read-only varsayimi ile tasarlanmistir
- Secrets repoya yazilmamalidir

## Testler

Tam test calistirma:

```bash
pytest -q
```

Syntax/bytecode dogrulamasi:

```bash
python3 -m compileall src
```

## Dokumantasyon

- [docs/architecture.md](/Users/tahatakgungor/dynamic_alert_project/docs/architecture.md)
- [docs/deployment.md](/Users/tahatakgungor/dynamic_alert_project/docs/deployment.md)
- [docs/platform_blueprint.md](/Users/tahatakgungor/dynamic_alert_project/docs/platform_blueprint.md)
- [docs/discovery_strategy.md](/Users/tahatakgungor/dynamic_alert_project/docs/discovery_strategy.md)
- [docs/ai_strategy.md](/Users/tahatakgungor/dynamic_alert_project/docs/ai_strategy.md)
- [docs/ui_strategy.md](/Users/tahatakgungor/dynamic_alert_project/docs/ui_strategy.md)
- [docs/smoke_test_matrix.md](/Users/tahatakgungor/dynamic_alert_project/docs/smoke_test_matrix.md)

## Mevcut sinirlar

Proje artik anlamli bir control plane + edge agent omurgasina sahip, ama bazi alanlar hala derinlestirilmeli:

- Bazi protocol adapterlari hala demo/heuristic agirlikli
- Gercek saha task orchestration daha ayrintili hale gelmeli
- Daha zengin agent retry/backoff/persistence stratejileri gerekebilir
- UI su an kullanisli ama tam operasyon konsolu seviyesinde degil

## Bir sonraki mantikli gelisim

- Protocol task derinlestirme
  Modbus profile set secimi, SNMP OID setleri, MQTT topic stratejileri, OPC UA node strategy
- Kalan security hardening bosluklari
- Daha ileri saha smoke testleri
