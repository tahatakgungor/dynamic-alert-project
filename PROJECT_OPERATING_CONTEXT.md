# Project Operating Context

Bu dosya projenin tek dosyalik operasyon hafizasidir.
Yeni bir sohbette once bu dosya okunmali, sonra calismaya devam edilmelidir.

## 1. Ana hedef

Dynamic Alert Project:

- edge cihazda calisacak
- ağa baglanir baglanmaz cihazlari kesfedecek
- bilinen protokollerle guvenli sekilde iletisime gececek
- ham veriyi anlamli telemetry'ye cevirecek
- semantic AI ile bilinmeyen alanlara hipotez uretecek
- alarm ve entegrasyon sistemiyle olayi aksiyona cevirecek

## 2. Kritik gerceklik

Asagidaki ifade kesin hedef degil, yon verici hedeftir:

- "ağdaki tum cihazlarla otomatik konus ve her veriyi eksiksiz anla"

Gercekci uygulama su katmanlarla olur:

1. discovery
2. protocol fingerprinting
3. safe read-only probing
4. passive observation
5. semantic inference
6. operator confirmation

## 3. Mimaride alinmis ana kararlar

- Dil: Python 3.11+
- API: FastAPI
- Config: Pydantic Settings
- ORM: SQLAlchemy 2.x
- Migration: Alembic
- DB baslangici: SQLite
- Buyume yolu: PostgreSQL + TimescaleDB / ClickHouse
- Bildirim: Telegram ile baslangic
- AI stratejisi: deterministic + heuristic + local small model + operator feedback
- Guvenlik: API key + RBAC + read-only protocol default

## 4. Bugune kadar yapilanlar

### Temel platform

- FastAPI uygulama iskeleti kuruldu
- dashboard ve temel API endpointleri eklendi
- workspace / site / network segment / integration modeli eklendi
- bootstrap verileri ve admin API key akisi eklendi

### Guvenlik ve operasyon

- API key tabanli auth eklendi
- `viewer / operator / admin` RBAC temeli eklendi
- `SECURITY.md` yazildi
- `.env.example`, `.gitignore`, `CI`, `LICENSE`, `CONTRIBUTING` eklendi
- Canli deploy `89.45.45.232:8011` uzerinde systemd ile yapildi

### Discovery ve protocol runtime

- plugin-first protocol registry kuruldu
- Modbus/TCP adapteri gercek `PyModbus` ile eklendi
- profile-based register reads eklendi
- generic modbus probe eklendi
- SNMP adapteri eklendi
- MQTT adapteri eklendi
- OPC UA adapteri eklendi
- passive observation ve flow cluster omurgasi baslatildi
- scapy tabanli live capture girisi eklendi
- unknown protocol candidate dataset katmani eklendi
- audit log temeli eklendi
- operator feedback ile semantic map persistence eklendi

### AI / semantic katman

- semantic hypothesis veri modeli eklendi
- local semantic intelligence service eklendi
- telemetry geldiginde semantic hypothesis uretme akisi eklendi
- AI strateji dokumani yazildi

### Dokumantasyon

- architecture
- deployment
- platform blueprint
- ui strategy
- roadmap
- ai strategy
- discovery strategy

## 5. Mevcut protokol destegi

- Modbus/TCP
- SNMP
- MQTT
- OPC UA
- raw TCP fallback
- D-Bus gateway heuristic

## 6. Simdi siradaki en mantikli isler

En oncelikli teknik sira:

1. live capture sertlestirme
2. unknown protocol candidate enrichment
3. webhook / email notifier
4. semantic map UI + operator workflow
5. audit log genisletme
6. background worker ayrimi
7. merkezi model/runtime entegrasyonu

## 7. Token optimizasyon kurallari

Her yeni sohbette ve her yeni gorevde bu kurallara uy:

1. Once bu dosyayi oku, tum repo taramasini gereksiz yere tekrar etme.
2. Kullanici istemedikce uzun teori tekrari yapma.
3. Mevcut mimari kararlarini yeniden uretmek yerine bu dosyadaki kararlar uzerinden ilerle.
4. Buyuk dosyalari butun olarak tekrar tekrar okumak yerine sadece ilgili bolumu ac.
5. Kod degisikligi yapmadan once hedef dosyalari dar kapsamli incele.
6. Yeni ozellikte once minimum calisan iskeleti kur, sonra genislet.
7. Web aramasi sadece degisebilir veya resmi dogrulama gereken konularda yap.
8. Final cevapta sadece sonuc, dogrulama ve siradaki en mantikli adimi ver.
9. Tekrar eden repo ozetleri yazma; gerekiyorsa bu dosyaya referans ver.
10. Bu dosyayi her anlamli iterasyonda guncelle.

## 8. Calisma kurallari

- Varsayilan protocol davranisi read-only olmali
- Endustriyel agda agresif ama guvenli davranilmali
- Bilinmeyen semantic alanlar AI + operator ile netlestirilmeli
- Projede "hazir modeli kullan, gereksiz yere sifirdan model egitme" ilkesi korunmali
- Edge cihazda kontrolsuz self-modifying model olmamali
- Surekli ogrenme once hypothesis memory ile ilerlemeli

## 9. Uretim riskleri

- bootstrap API key uretimde degistirilmeli
- tarama hizlari subnet ve bakim penceresine gore ayarlanmali
- proprietary protokoller icin passive observation daha oncelikli olmali
- bazi cihazlarda active probe bile riskli olabilir
- canli sirlar repoya yazilmamali; sadece sunucuda tutulmali

## 10. Yeni sohbette nasil devam edilir?

1. Bu dosyayi oku
2. `## 6. Simdi siradaki en mantikli isler` bolumune bak
3. Gerekirse sadece ilgili kod dosyalarini ac
4. Kaldigin yerden uygula

## 11. Son guncel durum

- Public GitHub repo hazir
- Son protokol genislemesi: SNMP + MQTT
- Son protokol genislemesi: OPC UA
- Son operasyon genislemesi: audit log
- Son ogrenme genislemesi: semantic map persistence
- Canli servis: `http://89.45.45.232:8011/`
- Canli servis birimi: `dynamic-alert.service`
- Canli klasor: `/opt/dynamic-alert`
- Mevcut odak: candidate enrichment, semantic map workflow ve canli guvenlik sertlestirme

## 12. Yeni sohbette kullanilacak kisa komutlar

Kullanici hatirlatma komutu:

- `DAC-LOAD`

Agent okuma komutu:

- `PROJECT_OPERATING_CONTEXT.md dosyasini oku, durumu ozetle ve kaldigin yerden devam et.`
