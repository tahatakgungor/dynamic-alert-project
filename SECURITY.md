# Security Policy

## Guvenlik ilkeleri

Bu proje endustriyel aglar icin tasarlandigi icin varsayilan yaklasim:

- minimum yetki
- read-only protocol davranisi
- kapali-varsayilan konfigrasyon
- guvenli varsayilanlar
- gozlemlenebilirlik ve denetlenebilirlik

## Tehdit modeli

Korunmasi gereken ana alanlar:

- edge cihaz kimligi
- makine telemetrisi
- alarm kurallari
- entegrasyon sirleri
- operator oturumlari

Ana riskler:

- yetkisiz ag tarama veya yatay hareket
- sahte telemetry enjeksiyonu
- notifier token sizmasi
- panel uzerinden yetkisiz kural degisikligi
- supply-chain bagimlilik riski

## Uretim icin zorunlu kontroller

1. Telegram ve diger entegrasyon sirlarini sadece ortam degiskeni veya secret manager ile yonetin.
2. UI ve API icin RBAC ekleyin.
3. CORS allow-list kullanin.
4. Edge cihazlari VPN veya sifir-guven yaklasimi ile merkezi sisteme baglayin.
5. Tum protocol adapterlerini default olarak read-only baslatin.
6. Paket bagimliliklarini duzenli tarayin.
7. Audit log tutun.
8. Metrik ve olaylar icin imzali veya dogrulanabilir event zinciri planlayin.

## Guvenlik acigi bildirimi

Guvenlik acigi bulursaniz public issue yerine private kanal kullanin. GitHub Security Advisory veya dogrudan sorumlu ekip ile paylasim tercih edilmelidir.
