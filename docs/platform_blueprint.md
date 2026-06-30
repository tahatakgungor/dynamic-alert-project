# Platform Blueprint

## Hedef

Bu proje yalnizca bir "alarm uygulamasi" degil, zamanla asagidaki yeteneklere genisleyebilecek bir endustriyel observability platformu olmalidir:

- cihaz kesfi
- protocol fingerprinting
- telemetry normalization
- semantic mapping
- alert orchestration
- entegrasyon merkezi
- coklu saha / coklu musteri yonetimi

## Modern teknoloji hedefi

### Edge katmani

- Python 3.11+
- FastAPI tabanli local control plane
- uvicorn / uvloop
- systemd veya container runtime
- ileride Rust tabanli packet capture modulu opsiyonu

### Control plane

- FastAPI
- Pydantic v2 + pydantic-settings
- SQLAlchemy 2.x
- Alembic
- OpenTelemetry

### Veri katmani

Faz 0:

- SQLite

Faz 1-2:

- PostgreSQL
- Redis

Faz 3+:

- TimescaleDB veya ClickHouse
- Object storage for packet captures

### Asenkron olay omurgasi

Buyume fazinda:

- NATS veya Redpanda/Kafka

Bu secim su sebeple onemli:

- telemetry ingestion ile alert evaluation ayrisir
- replay ve backpressure yonetimi kolaylasir
- baska sistemlere entegrasyon sadeleşir

## Temel mimari prensipleri

1. `Plugin-first protocol layer`
   Yeni protokoller cekirdek degismeden adapter olarak eklenmeli.
2. `Event-driven core`
   Zamanla scan, telemetry, alert ve notification akislari event bazli ayrismali.
3. `Control plane / data plane ayrimi`
   UI/API ile sahadaki veri toplama ayni sorumlulukta olmamali.
4. `Secure by default`
   Tarama, kimlik, secret ve entegrasyonlar en bastan guvenli tasarlanmali.
5. `Offline-first edge`
   Internet olmasa da saha cihazlari calismaya devam etmeli.

## Onerilen servis sinirlari

### 1. Edge Discovery Service

- subnet tarama
- cihaz envanteri
- port fingerprint
- network policy enforcement

### 2. Protocol Runtime

- adapter registry
- active probe
- passive capture
- semantic decoder

### 3. Normalization Pipeline

- ham veri -> canonical metric
- unit conversion
- quality score
- source metadata

### 4. Rule and Policy Engine

- threshold rules
- correlation rules
- silence detection
- maintenance windows

### 5. Notification Orchestrator

- Telegram
- webhook
- e-mail
- ticketing systems

### 6. Integration Gateway

- REST API
- webhook outbound
- MQTT publish
- ERP/MES/SCADA connectors

## Coklu ortam ve entegrasyon stratejisi

Arayuz ve API su yapida dusunulmeli:

- `workspace`
- `site`
- `network segment`
- `device`
- `integration`

Boylece ayni platform:

- tek tesis
- cok tesis
- farkli musteri
- farkli sektor

senaryolarina evrilebilir.

## Kisa vadeli yol

1. Moduler protocol registry
2. Migration altyapisi
3. Auth/RBAC
4. Audit log
5. Async task queue
6. Integration management UI
