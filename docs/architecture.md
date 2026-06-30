# Mimari Taslak

## Problem tanimi

Amac, sadece elektrik ve ethernet baglantisi ile sahaya bir edge cihaz koyup:

- agdaki makineleri bulmak,
- iletisim protokollerini tanimak,
- akan veriyi normalize etmek,
- anlamli olaylar uretmek,
- bildirimi Telegram ve daha sonra diger kanallardan iletmek,
- tum sistemi web arayuzunden yonetmektir.

## Neden edge-first?

Endustriyel aglarda gecikme, guvenlik ve saha izolasyonu onemlidir. Bu nedenle:

- ilk tarama edge cihazda yapilmali,
- veri yerelde islenmeli,
- yalnizca gerekli olaylar ve ozetler disari cikmalidir.

## Sistem bilesenleri

### 1. Device Discovery

Sorumluluklar:

- ARP / ICMP / TCP port scan
- Bilinen portlardan protokol adaylari cikarimi
- MAC vendor ve hostname toplama
- Cihaz sinifi tahmini

Ornek ipuclari:

- `502/tcp` -> Modbus/TCP adayi
- `80`, `443` -> HTTP tabanli cihaz
- `1883` -> MQTT
- `22` -> Linux tabanli gateway
- `111`, `135`, `139`, `445` -> OS / servis ipuclari

### 2. Protocol Fingerprinting

Bu katman "kesin semantic anlama" degil, once "hangi dilden konusuyor?" sorusunu cozer.

Strateji:

- active probe
- banner inspection
- protocol handshake denemeleri
- packet shape analizi
- retry / timeout istatistigi

### 3. Telemetry Normalization

Ham veri su standarda cekilir:

- `metric_key`
- `value`
- `unit`
- `quality`
- `source_protocol`
- `source_address`
- `observed_at`

Ornek:

- Ham: `register 40012 = 713`
- Normalize: `temperature_c = 71.3`

### 4. Rule Engine

Kurallar:

- esik bazli
- degisim hizi bazli
- sessizlik / heartbeat kaybi
- kombinasyon kurallari

Ornek:

- `temperature_c > 70`
- `pressure_bar < 2`
- `no telemetry for 120 seconds`

### 5. Notification Layer

Ilk kanal:

- Telegram

Sonraki kanallar:

- E-posta
- SMS
- Webhook
- Mobil push

### 6. Control Center

Web tarafinda yonetilecekler:

- cihaz listesi
- son telemetry akisi
- alarm kurallari
- bildirim kanallari
- protokol esleme durumu
- bilinmeyen veri alanlari icin operator karar ekrani

## Fazlara ayrilmis teknik yol haritasi

### Faz 0 - Temel platform

- API
- web panel
- SQLite
- simulasyon verisi
- temel alarm motoru

### Faz 1 - Gercek saha discovery

- subnet tarama
- port fingerprint
- cihaz envanteri

### Faz 2 - Bilinen protokoller

- Modbus/TCP
- OPC UA
- MQTT
- HTTP tabanli cihaz API'leri

### Faz 3 - Bilinmeyen akislari anlama

- packet capture
- pattern extraction
- value clustering
- yari-otomatik semantic mapping

### Faz 4 - Endustriyel sertlestirme

- offline queue
- TLS / sertifika
- cihaz kimliklendirme
- merkezi guncelleme
- watchdog ve self-healing

## Riskler ve gercekci sinirlar

Su kisim mutlaka bilincli planlanmali:

- Proprietary protokoller bazen reverse engineering gerektirir.
- Sadece aktif probe ile her cihaz anlamlandirilamaz.
- Bazi makinelerde okuma denemesi bile riskli olabilir.
- Bazi endustriyel segmentlerde tarama hizi dikkatli sinirlanmalidir.

Bu nedenle sistemin ana vaadi:

"Bilinen protokolleri otomatik tanimlamak ve bilinmeyen veri akislari icin hizli bir operator-destekli anlamlandirma sunmak"

olmalidir.
