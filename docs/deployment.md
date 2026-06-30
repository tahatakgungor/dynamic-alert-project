# Deployment Rehberi

## Hedef platformlar

- Raspberry Pi 4 / 5
- NVIDIA Jetson Nano / Orin
- Endustriyel mini PC (Ubuntu/Debian)

## Tavsiye edilen topoloji

1. Edge cihaz makina agina ethernet ile baglanir.
2. Cihaz bir veya daha fazla subnet'i tarar.
3. Yerel SQLite ile baslar, buyudugunde Postgres'e gecer.
4. Telegram bildirimleri internet erisimi varsa dogrudan gider.
5. Merkezi yonetim gerektiginde VPN veya ters tunca ile baglanilir.

## Kurulum

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 -m venv /opt/dynamic-alert/.venv
source /opt/dynamic-alert/.venv/bin/activate
pip install -e /opt/dynamic-alert/app
```

## Ortam degiskenleri

```bash
export DYNAMIC_ALERT_DATABASE_URL=sqlite:///./dynamic_alert.db
export DYNAMIC_ALERT_TELEGRAM_BOT_TOKEN=your-bot-token
export DYNAMIC_ALERT_TELEGRAM_CHAT_ID=your-chat-id
export DYNAMIC_ALERT_SCAN_SUBNETS=192.168.1.0/24,192.168.2.0/24
```

## Servis olarak calistirma

Ornek `systemd` uniti:

```ini
[Unit]
Description=Dynamic Alert Control Center
After=network-online.target
Wants=network-online.target

[Service]
User=root
WorkingDirectory=/opt/dynamic-alert/app
Environment=DYNAMIC_ALERT_DATABASE_URL=sqlite:///./dynamic_alert.db
ExecStart=/opt/dynamic-alert/.venv/bin/uvicorn dynamic_alert.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Sahaya cikmadan once

1. Tarama hizini sinirlayin.
2. Hangi subnetlerin taranacagini whitelist ile belirleyin.
3. Sadece read-only protokol adapterlerini aktif edin.
4. Telegram yerine once dry-run modunda bildirimleri log'a yazin.
5. Pilot tesiste protokol davranisini kaydedin.
