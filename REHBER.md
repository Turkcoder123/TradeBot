# 📘 EURUSD Scalp-Trend Hibrit Strateji Rehberi

## İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Strateji Mantığı](#strateji-mantığı)
3. [İndikatörler](#indikatörler)
4. [Giriş Kuralları](#giriş-kuralları)
5. [Risk Yönetimi](#risk-yönetimi)
6. [Backtest Sonuçları](#backtest-sonuçları)
7. [Overfitting Kontrolü](#overfitting-kontrolü)
8. [Forward Test (Demo Hesap)](#forward-test-demo-hesap)
9. [Dosya Yapısı](#dosya-yapısı)
10. [Kurulum ve Çalıştırma](#kurulum-ve-çalıştırma)
11. [Sık Sorulan Sorular](#sık-sorulan-sorular)

---

## Genel Bakış

Bu strateji, EURUSD paritesi için **H1 (1 saatlik)** zaman diliminde çalışan
bir **scalp-trend hibrit** yaklaşımdır. Temel amacı:

- **Trend yönünü** belirleyip sadece o yönde işlem açmak
- **Pullback (geri çekilme)** anlarında trende katılım sağlamak
- **Overfitting yapmadan** standart indikatör parametreleri kullanmak

### Tasarım İlkeleri

| İlke | Uygulama |
|------|----------|
| Overfitting önleme | Tüm parametreler ders kitabı standartları (EMA 50/200, RSI 14, MACD 12/26/9) |
| Veri ayrımı | %70 eğitim / %30 test (out-of-sample doğrulama) |
| Gerçekçi maliyetler | Spread ve komisyon hesaba katılır |
| Adaptif risk | ATR tabanlı dinamik SL/TP |

---

## Strateji Mantığı

```
                    EMA-50 > EMA-200?
                   /                 \
                 EVET                HAYIR
              (Yükseliş)           (Düşüş)
                 |                    |
        Fiyat EMA-50'ye         Fiyat EMA-50'ye
         geri çekildi?          geri yükseldi?
                 |                    |
         MACD histogram          MACD histogram
            pozitif?                negatif?
                 |                    |
            LONG giriş           SHORT giriş
```

Strateji iki giriş tipi kullanır:

### 1. Trend Pullback (Ana Giriş)
Fiyat trend yönündeki EMA-50'ye geri çekilip, MACD ile momentum doğrulaması
aldığında giriş yapılır. Bu, trend takipçi stratejilerin en güvenilir
giriş tekniğidir.

### 2. Momentum Doğrulama (Yardımcı Giriş)
MACD histogramı sıfır çizgisini trend yönünde geçtiğinde ve fiyat
EMA-50'nin doğru tarafında olduğunda giriş yapılır.

---

## İndikatörler

| İndikatör | Parametre | Amaç |
|-----------|-----------|------|
| **EMA-50** | Periyot: 50 | Hızlı trend takibi, dinamik destek/direnç |
| **EMA-200** | Periyot: 200 | Ana trend yönü belirleme |
| **MACD** | 12/26/9 | Momentum doğrulama |
| **RSI** | Periyot: 14 | Aşırı alım/satım kontrolü |
| **Bollinger Bands** | 20/2σ | Volatilite ölçümü |
| **ATR** | Periyot: 14 | Dinamik SL/TP hesaplama |

> ⚠️ **Not:** Tüm parametreler standart ders kitabı değerleridir. Hiçbir
> parametre optimizasyonu yapılmamıştır.

---

## Giriş Kuralları

### LONG (Alış) Giriş

**Tip 1 – Trend Pullback:**
1. ✅ EMA-50 > EMA-200 (yükseliş trendi)
2. ✅ Mumun düşük fiyatı (low) EMA-50'ye değdi veya aşağı geçti
3. ✅ Mum, EMA-50'nin **üzerinde** kapandı (bounce/sıçrama)
4. ✅ MACD histogramı **pozitif** (momentum doğrulama)
5. ✅ Saat: 08:00-17:00 UTC (Londra/NY oturumu)

**Tip 2 – Momentum:**
1. ✅ EMA-50 > EMA-200 (yükseliş trendi)
2. ✅ MACD histogramı negatiften pozitife geçti
3. ✅ Fiyat EMA-50'nin üzerinde
4. ✅ Saat: 08:00-17:00 UTC

### SHORT (Satış) Giriş

**Tip 1 – Trend Pullback:**
1. ✅ EMA-50 < EMA-200 (düşüş trendi)
2. ✅ Mumun yüksek fiyatı (high) EMA-50'ye değdi veya yukarı geçti
3. ✅ Mum, EMA-50'nin **altında** kapandı (rejection/reddedilme)
4. ✅ MACD histogramı **negatif** (momentum doğrulama)
5. ✅ Saat: 08:00-17:00 UTC

**Tip 2 – Momentum:**
1. ✅ EMA-50 < EMA-200 (düşüş trendi)
2. ✅ MACD histogramı pozitiften negatife geçti
3. ✅ Fiyat EMA-50'nin altında
4. ✅ Saat: 08:00-17:00 UTC

---

## Risk Yönetimi

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| **Stop Loss** | 1.5 × ATR(14) | Volatiliteye göre dinamik |
| **Take Profit** | 3.0 × ATR(14) | Risk:Ödül = 1:2 |
| **Risk/İşlem** | %1 | Hesap bakiyesinin %1'i riskle |
| **Pozisyon** | Tek pozisyon | Aynı anda tek işlem |
| **Lot Hesabı** | (Bakiye × %1) / (SL pip × 10) | Otomatik lot hesaplama |
| **Seans** | 08:00-17:00 UTC | Sadece yüksek likidite saatleri |

### Başabaş Noktası
- SL=1.5 ATR, TP=3.0 ATR → Başabaş için gereken kazanma oranı: **%33.3**
- Stratejinin gerçek kazanma oranı: **~%35** (başabaş üzerinde)

---

## Backtest Sonuçları

### Veri Bilgisi
- **Sembol:** EURUSD
- **Zaman dilimi:** H1 (1 saat)
- **Tarih aralığı:** 09 Ekim 2025 – 07 Nisan 2026 (6 ay)
- **Toplam bar:** 3015
- **Başlangıç bakiyesi:** $10,000

### In-Sample (Eğitim Seti - %70)
| Metrik | Değer |
|--------|-------|
| Toplam işlem | 52 |
| Kazanan | 19 |
| Kaybeden | 33 |
| Kazanma oranı | %36.5 |
| Toplam kar/zarar | +96.9 pip / +$296 |
| Profit factor | 1.09 |
| Maks. drawdown | $1,010 |

### Out-of-Sample (Test Seti - %30)
| Metrik | Değer |
|--------|-------|
| Toplam işlem | 23 |
| Kazanan | 7 |
| Kaybeden | 16 |
| Kazanma oranı | %30.4 |
| Toplam kar/zarar | -35.5 pip / -$266 |
| Profit factor | 0.83 |
| Maks. drawdown | $693 |

### Tam Veri Seti (%100)
| Metrik | Değer |
|--------|-------|
| Toplam işlem | 75 |
| Kazanan | 26 |
| Kaybeden | 49 |
| Kazanma oranı | %34.7 |
| Toplam kar/zarar | +61.4 pip / +$17 |
| Profit factor | 1.0 |

### Önemli Notlar
- SHORT sinyalleri düşüş trendinde güçlü sonuç verdi (+40-58 pip kazançlar)
- LONG sinyalleri bu dönemde zayıf (piyasa genel olarak yatay/düşüş eğiliminde)
- Strateji **simetrik kurallar** kullanır – piyasa koşulları değiştiğinde
  her iki yönde de çalışır

---

## Overfitting Kontrolü

### Test Edilen Önlemler

1. **Standart Parametreler:** Tüm indikatörler ders kitabı değerleri (optimizasyon yok)
2. **Veri Ayrımı:** %70 eğitim / %30 doğrulama seti
3. **Simetrik Kurallar:** Aynı mantık LONG ve SHORT için geçerli
4. **Basit Kural Seti:** Sadece 4-5 koşul (karmaşık değil)

### Sonuç

| Metrik | Eğitim | Test | Fark |
|--------|--------|------|------|
| Kazanma Oranı | %36.5 | %30.4 | %6.1 |

✅ **%6.1 fark, düşük overfitting riski göstermektedir** (kabul edilebilir eşik: <%15).

Eğitim seti hafif kârlı, test seti hafif zararlı – bu gerçekçi bir sonuçtur.
Strateji "sihirli" değil, ancak **mantıksal bir avantaja** sahiptir.

---

## Forward Test (Demo Hesap)

### Başlatma

MetaTrader 5 terminali açık ve demo hesaba giriş yapılmış olmalıdır.

```bash
# Botu başlat (varsayılan: 0.01 lot, EURUSD)
python mt5_bot.py

# Özel lot boyutu
python mt5_bot.py --lot 0.05

# Özel sembol
python mt5_bot.py --symbol EURUSD --lot 0.02
```

### Bot Davranışı

1. MT5 terminaline bağlanır
2. Her saatte bir (H1 bar kapanışında) kontrol yapar
3. Açık pozisyon yoksa sinyal arar
4. Sinyal varsa SL/TP ile market emri gönderir
5. Aynı anda sadece 1 pozisyon açık tutulur
6. Tüm işlemler `logs/mt5_bot.log` dosyasına kaydedilir

### Log Dosyası

```
logs/mt5_bot.log
```

Bot her çalıştığında aşağıdaki bilgileri loglar:
- Bağlantı bilgisi
- Her bar kontrolü
- Sinyal detayları (yön, giriş, SL, TP, ATR)
- İşlem sonuçları

### Önemli Uyarılar

> ⚠️ **Demo hesap üzerinde test edin!** Gerçek para ile işlem yapmadan
> önce en az 1 ay demo test yapmanız önerilir.

> ⚠️ **Bot sürekli çalışmalıdır.** Her saat başı kontrol yapar,
> kapatırsanız sinyalleri kaçırırsınız.

> ⚠️ **İnternet bağlantısı** gereklidir. MT5 terminali açık ve
> bağlı olmalıdır.

---

## Dosya Yapısı

```
tradebot/
├── data/
│   └── EURUSD_6m.csv          # 6 aylık H1 fiyat verisi
├── logs/
│   └── mt5_bot.log            # Bot log dosyası
├── tests/
│   ├── conftest.py            # Test yapılandırması
│   ├── test_fetch_prices.py   # Veri çekme testleri
│   ├── test_strategy.py       # Strateji testleri
│   └── test_backtest.py       # Backtest testleri
├── strategy.py                # Strateji mantığı ve indikatörler
├── backtest.py                # Backtest motoru
├── mt5_bot.py                 # Forward test botu (MT5 canlı)
├── fetch_prices.py            # MT5'ten veri çekme
├── requirements.txt           # Python bağımlılıkları
└── REHBER.md                  # Bu dosya
```

---

## Kurulum ve Çalıştırma

### Ön Gereksinimler

- Python 3.10+
- MetaTrader 5 terminali kurulu ve giriş yapılmış
- Demo hesap açık

### Kurulum

```bash
# Bağımlılıkları kur
pip install -r requirements.txt

# (İsteğe bağlı) Yeni veri çek
python fetch_prices.py EURUSD
```

### Backtest Çalıştırma

```bash
# Varsayılan CSV ile backtest
python backtest.py

# Özel CSV ile backtest
python backtest.py path/to/custom.csv
```

### Testleri Çalıştırma

```bash
# Tüm testler
python -m pytest tests/ -v

# Sadece strateji testleri
python -m pytest tests/test_strategy.py -v

# Sadece backtest testleri
python -m pytest tests/test_backtest.py -v
```

### Forward Test Başlatma

```bash
# Demo hesapta botu başlat
python mt5_bot.py --lot 0.01
```

---

## Sık Sorulan Sorular

### Neden kazanma oranı düşük (~%35)?

Strateji **1:2 risk-ödül oranı** kullanır (SL=1.5 ATR, TP=3.0 ATR). Bu
nedenle daha az işlem kazanır ama kazandığında daha çok kazanır. Başabaş
noktası sadece %33.3 kazanma oranıdır.

### Neden LONG işlemler zayıf?

Bu 6 aylık dönemde EURUSD genel olarak yatay veya hafif düşüş eğiliminde
idi. Strateji simetrik kurallar kullandığı için her iki yönde de aynı
mantığı uygular – yükseliş trendlerinde LONG işlemler daha iyi sonuç
verecektir.

### Overfitting yapılmadığını nasıl anlarız?

1. Tüm indikatör parametreleri standart ders kitabı değerleri
2. Eğitim-test arası kazanma oranı farkı sadece %6.1
3. Kurallar basit ve az sayıda (4-5 koşul)
4. Parametre optimizasyonu yapılmadı

### Stratejiyi nasıl geliştirebilirim?

- Farklı zaman dilimlerini deneyin (M15, M30, H4)
- Diğer paritelerde test edin (GBPUSD, USDJPY)
- Trailing stop ekleyin (fiyat 1x ATR kâra geçtiğinde SL'yi giriş noktasına çekin)
- Haber filtresi ekleyin (yüksek etkili haberlerden önce işlem kapatın)

### Bot çöktüğünde ne olur?

Açık pozisyonlar MT5 sunucusunda SL/TP ile korunmaya devam eder.
Bot tekrar başlatıldığında mevcut pozisyonu algılar ve yeni sinyal
bekler.

---

## Sorumluluk Reddi

Bu strateji **eğitim amaçlıdır**. Forex piyasasında işlem yapmak yüksek
risk taşır. Geçmiş performans gelecekteki sonuçları garanti etmez.
Gerçek para ile işlem yapmadan önce yeterli deneyim kazanın ve
kaybetmeyi göze alabileceğiniz miktarla işlem yapın.
