# UI Strategy

## Arayuz vizyonu

Arayuz yalnizca bir dashboard degil, genisleyebilir bir operasyon konsolu olmalidir.

## Bilgi mimarisi

Ana navigasyon:

- Overview
- Devices
- Protocols
- Telemetry
- Rules
- Alerts
- Integrations
- Deployments
- Settings

## Tasarim ilkeleri

1. Coklu saha yonetimine uygun olmasi
2. Yeni entegrasyon modullerine yer acmasi
3. Teknik olmayan operatorlerin de temel aksiyonlari alabilmesi
4. Guvenlik, audit ve rol sinirlarinin UI'da gorunur olmasi

## Bilesen mimarisi

- shell layout
- command palette
- entity detail side panels
- live event stream
- protocol mapping wizard
- integration setup wizard

## Neden bu onemli?

Bugun tek edge cihaz icin baslayan proje yarin:

- merkezi NOC paneline,
- saha bazli operasyon ekranina,
- entegrasyon marketine

donusebilir.
