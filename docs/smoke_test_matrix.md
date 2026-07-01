# Smoke Test Matrix

Bu dokuman yeni ozellik eklemek icin degil, sistemin amacina ne kadar yaklastigini gercekci senaryolarla sinamak icin kullanilir.

## 1. Control Plane Baslangici

- Senaryo: Uygulama temiz veritabani ile baslar.
- Beklenen:
  - bootstrap verileri olusur
  - `HQ-PLANT` site kaydi gelir
  - bootstrap admin API key kaydi olusur
  - varsayilan alarm kurali yuklenir
- Risk:
  - production ortaminda varsayilan bootstrap key ile kalkmamali

## 2. Edge Node Register

- Senaryo: Fabrikadaki edge node merkezi panele kaydolur.
- Beklenen:
  - edge node kaydi olusur
  - tekil `node_key` uretilir
  - `site_code` gecersizse istek reddedilir
- Risk:
  - yetkisiz kullanicinin node register etmesi

## 3. Edge Heartbeat

- Senaryo: Edge agent periyodik heartbeat yollar.
- Beklenen:
  - `last_seen_at` guncellenir
  - status `online/degraded/offline` gibi whitelist degerlerden biri olur
- Risk:
  - serbest string status ile veri kirlenmesi

## 4. Edge Job Queue

- Senaryo: Operator edge node icin scan veya capture isi kuyruga alir.
- Beklenen:
  - yalniz whitelist `job_kind` kabul edilir
  - payload boyutu ve sekli sinirli olur
  - gecersiz `edge_node_id` reddedilir
- Risk:
  - keyfi job kind veya asiri buyuk payload ile istismar

## 5. Claim -> Execute -> Complete

- Senaryo: Edge agent bir isi claim eder, yerelde calistirir, sonucu geri raporlar.
- Beklenen:
  - en eski queued job claim edilir
  - job `queued -> running -> completed/failed` gecisleri gorulur
  - sonuc DB ve API uzerinden gorunur
- Risk:
  - race condition, cift claim, sessiz failure

## 6. D-Bus Sicaklik Demo

- Senaryo: `dbus-demo` edge job'u claim edilip yerelde calisir.
- Beklenen:
  - telemetry olusur
  - semantic hypothesis olusur
  - kural tetiklenirse alert event yazilir
  - Telegram notifier varsa mesaj gider, yoksa dry-run iz gorulur
- Risk:
  - semantic->alert zincirinin kopmasi

## 7. Passive Observe / Live Capture

- Senaryo: Edge agent custom packet sample veya live capture ile veri toplar.
- Beklenen:
  - observation ve flow cluster olusur
  - unknown candidate enrichment calisir
  - multicast/link-local filtreleri korunur
- Risk:
  - kontrolsuz capture parametresi, fazla paket, anlamsiz gürültü

## 8. Operator Workflow

- Senaryo: Operator semantic hypothesis veya unknown candidate uzerinde aksiyon alir.
- Beklenen:
  - semantic hypothesis -> semantic map promote calisir
  - unknown candidate `confirm/dismiss/escalate` aksiyonlari kalici olur
  - audit log kaydi olusur
- Risk:
  - operator karari sonraki refresh tarafindan ezilmemeli

## 9. Audit ve Forensics

- Senaryo: Alarm, edge job ve operator aksiyonlari sonradan incelenir.
- Beklenen:
  - audit log izleri eksiksiz gorulur
  - alert event teslim durumu kayitlidir
  - background job gecmisi restart sonrasi korunur
- Risk:
  - sessiz hata, kayip olay, hesap verilebilirlik eksigi

## 10. Uretim Sertlestirme Kontrolu

- Senaryo: Production benzeri ortamda uygulama ayağa kalkar.
- Beklenen:
  - varsayilan bootstrap key ile baslamaz
  - edge payload dogrulama ve status whitelist'leri aktif kalir
  - hassas tokenlar repoda bulunmaz
- Risk:
  - yanlis konfig ile guvensiz deployment
