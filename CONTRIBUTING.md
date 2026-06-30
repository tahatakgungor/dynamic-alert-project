# Contributing

## Gelistirme akisi

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

## Kurallar

- Yeni protocol adapterleri cekirdek kodu bozmadan eklenmelidir.
- Varsayilan davranis read-only olmalidir.
- Gizli bilgi kod icine gomulmemelidir.
- Her yeni servis icin en az bir test eklenmelidir.
- Mimari kararlari `docs/` altinda kayda gecirilmelidir.
