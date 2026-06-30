# Discovery Strategy

## En zor hedef

Edge cihazin ağa baglanir baglanmaz tum cihazlari bulmasi, uygun sekilde iletisime gecmesi ve anlamli veri cikarmasi.

Bu hedef icin katmanli strateji gerekir.

## 1. Safe Discovery

- ARP scan
- ICMP reachability
- TCP SYN port sampling
- MAC vendor lookup
- hostname collection

## 2. Protocol Probing

Bilinen protokoller icin hafif handshake:

- Modbus/TCP
- HTTP
- MQTT
- OPC UA
- BACnet
- SNMP

## 3. Passive Observation

Ag musaitse:

- packet capture
- flow clustering
- request/response pattern extraction
- unknown payload sample retention

Bu, proprietary protokolleri anlamada aktif probing'den daha yararlidir.

## 4. Semantic Extraction

- bilinen decoder
- heuristic AI
- local small model
- operator confirmation

## 5. Safety Guardrails

- rate limiting
- read-only mode
- subnet allow-list
- protocol deny-list
- maintenance window awareness

## Sonuc

Hedef "tum cihazlarla konusmak" olmali, ama bunu:

- agi bozmayacak sekilde,
- cihazlara zarar vermeden,
- operatorun guvenini kaybetmeden

yapmak asildir.
