# Advanced International Trade – Mandatory Assignment

**Topic:** Did China's informal sanctions after the 2010 Nobel Peace Prize to Liu Xiaobo
reduce Norwegian exports to China, did trade recover after the December 2016
normalisation, and was trade re-routed via neighbouring countries?

Approach: ex-post structural gravity (PPML with exporter-year, importer-year and pair
fixed effects, international-border × year controls), following Yotov et al. (2016), ch. 1.
All code is Python.

## Structure

```
norway_china_nobel.py   main analysis: figure, PPML regression, event study
data/                   raw data (NOT in git – see below)
output/                 figures and tables produced by the script
```

## Data

| Dataset | Source | Used for | In repo? |
|---|---|---|---|
| CEPII TradeProd, TPe V202606 | cepii.fr → Data → TradeProd | Bilateral + domestic manufacturing trade, 9 industries, 1966–2022 | No (850 MB) |
| CEPII Gravity V202211 | cepii.fr → Data → Gravity | Optional controls (distance, RTAs) | No |

Download `TPe_V202606.zip`, unzip, and put `TPe_V202606.dta` in `data/`.

**Important limitation:** TradeProd covers manufacturing only (ISIC rev. 3, divisions
15–36). Fresh and chilled salmon (HS 0302) is classified as fishing (ISIC 05) and is
therefore *not* in the Food industry. Only processed fish (e.g. frozen fillets, ISIC 1512)
is included. The sanctions mainly targeted fresh salmon, so the Food-sector estimate is
best read as the effect on *other / processed* food exports. Product-level data (CEPII
BACI or UN Comtrade, HS 0302/0303/0304) is needed to estimate the salmon effect directly.

## Run

```bash
pip install pyfixest pandas matplotlib pyarrow
python norway_china_nobel.py data/TPe_V202606.dta
```

## References

- Yotov, Piermartini, Monteiro & Larch (2016), *An Advanced Guide to Trade Policy
  Analysis: The Structural Gravity Model*, WTO/UNCTAD.
- Mayer, Santoni & Vicard (2023), *The CEPII Trade and Production Database*, CEPII WP 2023-01.
- Kolstad, I. *Too big to fault? Effects of the 2010 Nobel Peace Prize on Norwegian
  exports to China and foreign policy*, CMI Working Paper WP 2016:03.

## First results (Food, 2000–2022, 98 countries with domestic flows)

| | PPML coef. | SE | Effect |
|---|---|---|---|
| Norway→China, freeze 2011–16 | −0.451*** | 0.094 | −36% |
| Norway→China, after 2017 | −0.436*** | 0.143 | −35% |
| Norway→Vietnam, freeze | −0.342*** | 0.071 | −29% |
| Norway→Hong Kong, freeze | 0.197* | 0.100 | +22% |

Event study (`output/fig2_event_study.png`): the effect grows from −0.30 in 2011 to
−0.85 in 2016 and only partly recovers after 2017. Caveats: negative coefficients
already in 2007–08 (2009 was an unusually high year, so the reference year matters),
and the effect does not disappear after normalisation.
