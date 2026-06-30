# AI Strategy

## Neden AI gerekiyor?

Bu projede AI'nin ana gorevi sohbet etmek degil, su alanlarda guc carpani olmak:

- bilinmeyen telemetry alanlarina anlam onermek
- register / payload yapilarini siniflandirmak
- cihaz davranisini ozetlemek
- operatore anlamli aciklama sunmak
- daha once gorulmemis makineler icin semantic hipotezler uretmek

## Temel ilke

Hazir modelleri kullaniriz, gereksiz yere sifirdan model egitmeyiz.

## Onerilen AI katmanlari

### Katman 1 - Deterministic Edge Intelligence

- heuristics
- protocol-specific decoders
- unit normalization
- confidence scoring

Bu katman internet olmadan da calisir.

### Katman 2 - Small Local Model

Yerelde calisabilecek kucuk model:

- semantic mapping
- unknown field explanation
- protocol guess refinement

Runtime secenekleri:

- Ollama
- ONNX Runtime
- llama.cpp

### Katman 3 - Central Training / Evaluation

Surekli ogrenirken dogrudan sahada kontrolsuz agirlik guncellemek yerine:

- saha verisini anonimlestir
- merkezi degerlendirme yap
- iyi cikan semantic mappingleri edge'e geri dagit

Bu daha guvenli ve denetlenebilir bir surekli iyilestirme modelidir.

## "Devamli kendini egitme" nasil gercekci uygulanir?

Dogru yaklasim:

- online memory
- hypothesis store
- confidence update
- operator feedback loop
- merkezi model refresh

Yanlis yaklasim:

- edge cihazda rastgele kendi agirliklarini surekli degistiren kontrolsuz model

## AI'nin karar tipleri

1. `Deterministic`
   Esik, kural ve protocol decoder sonucudur.
2. `Heuristic`
   Deger araligi, cihaz tipi ve anahtar isimlerinden cikarim yapar.
3. `Model-assisted`
   Hazir kucuk model semantic yorum ve aciklama onerir.
4. `Human-confirmed`
   Operator onayi ile kalici semantic map olur.

## Hedeflenen sonraki AI ozellikleri

- register map discovery assistant
- packet clustering
- anomaly explanation
- maintenance prediction
- automatic protocol playbook suggestion
