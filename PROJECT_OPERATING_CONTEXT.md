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
- live capture icin sniff exception fallback ve link-local/multicast filtreleme eklendi
- unknown protocol candidate dataset katmani eklendi
- unknown protocol enrichment icin port-spesifik ve payload-pattern heuristic'leri genisletildi
- audit log temeli eklendi
- Telegram notifier gercek HTTP `sendMessage` akisina gecirildi
- semantic tahmin sonucu ureten metric key'ler icin alert evaluation destegi eklendi
- D-Bus demo sicaklik -> semantic -> Telegram smoke test endpoint'i eklendi
- semantic hypothesis -> semantic map promote operator workflow'u eklendi
- alert.triggered audit kaydi ve dashboard'da alert/audit gorunurlugu eklendi
- unknown protocol candidate icin confirm / dismiss / escalate operator workflow'u eklendi
- scan / observe / capture / demo akislarinda in-process background job queue ve status endpoint'leri eklendi
- background job kayitlari veritabanina tasindi; job gecmisi restart sonrasi korunuyor
- control plane + edge node yonu icin edge node register / heartbeat / job claim / result raporlama iskeleti eklendi
- edge runtime API'lerini kullanan ilk `dynamic-alert-edge-agent` CLI eklendi
- edge job payload'lari scan subneti, capture interface/filter ve demo cihaz parametrelerini gercekten etkiler hale getirildi
- production ortaminda varsayilan bootstrap key reddi, edge payload limitleri ve status/job kind dogrulamalari eklendi
- control plane <-> edge agent tam roundtrip smoke testi ve saha smoke matrix dokumani eklendi
- edge job payload'inda `enabled_protocols` ve probe tuning alanlariyla protocol orchestration eklendi
- Modbus register yorumlamasi icin isimlendirilmis profile set katalogu ve panel secimi eklendi
- MQTT topic ve SNMP OID secimleri icin isimlendirilmis katalog omurgasi eklendi
- protocol catalog secimi ile raw override cakismalarini reddeden precedence guard eklendi
- named protocol catalog payload'lari icin edge scan roundtrip smoke testi eklendi
- katalog-secimli Modbus scan icin telemetry -> semantic -> alert roundtrip smoke testi eklendi
- edge endpoint rate limit, edge job finalize guard ve audit detail redaction sertlestirmeleri eklendi
- panelde calisabilir demo scenario lab eklendi
- panelde kullanici dostu edge orchestration formu ve ozet metrikler eklendi
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
- Son candidate enrichment genislemesi: S7 / EtherNet-IP / plaintext topic-value heuristic'leri
- Son alerting genislemesi: semantic metric üzerinden kural tetikleme + gercek Telegram notifier
- Son semantic workflow genislemesi: hipotezi panelden tek tikla kalici map'e promote etme
- Son operasyon genislemesi: panelde son alert event ve audit log gorunurlugu
- Son candidate workflow genislemesi: operator lock eden confirm / dismiss / escalate aksiyonlari
- Son runtime genislemesi: request path'ten ayri arka plan job calistirma ve job status takibi
- Son kalicilik genislemesi: `background_jobs` tablosu ve DB-backed worker status takibi
- Son mimari genisleme: merkezi panelden yonetilen edge node ve edge job temel modeli
- Son agent genislemesi: register / run-once / run modlari olan edge agent poller CLI
- Son executor genislemesi: edge job payload'u yerel agent execution parametrelerine baglandi
- Son sertlestirme genislemesi: bootstrap key enforcement, edge schema validation ve oldest-job claim duzeltmesi
- Son dogrulama genislemesi: register -> enqueue -> claim -> execute -> complete entegrasyon testi
- Son orchestration genislemesi: job bazli protocol secimi ve probe tuning
- Son protocol catalog genislemesi: named Modbus profile set secimi ve structured profile repository
- Son protocol catalog genislemesi: named MQTT topic set ve SNMP OID set secimi
- Son dogrulama genislemesi: catalog-secimli edge scan payload'inin roundtrip smoke testi
- Son dogrulama genislemesi: catalog-secimli Modbus scan telemetry/semantic/alert smoke testi
- Son sertlestirme genislemesi: edge endpoint throttle, duplicate completion guard ve audit redaction
- Son UI genislemesi: tek tikla senaryo calistiran scenario lab
- Son UI genislemesi: orchestration odakli daha anlasilir kontrol paneli
- Canli servis: `http://89.45.45.232:8011/`
- Canli servis birimi: `dynamic-alert.service`
- Canli klasor: `/opt/dynamic-alert`
- Mevcut odak: protocol task derinlestirme, saha smoke testleri ve kalan security hardening bosluklari

## 12. Yeni sohbette kullanilacak kisa komutlar

Kullanici hatirlatma komutu:

- `DAC-LOAD`

Agent okuma komutu:

- `PROJECT_OPERATING_CONTEXT.md dosyasini oku, durumu ozetle ve kaldigin yerden devam et.`
