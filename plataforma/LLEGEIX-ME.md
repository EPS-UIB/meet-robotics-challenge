# Plataforma de les zones vermella i blava

Plataforma de 200 × 100 mm a 100 mm d'altura, amb dos allotjaments per a bobines. Té el costat davanter obert, cap al centre del taulell, i no té base: una bobina pot entrar a sota empenyent-la. Prototip sense tallar: mides pendents d'assaig.

Cada zona necessita un joc complet de les dues làmines, de 420 × 230 mm i en contraplacat nominal de 3 mm.

| Fitxer | Contingut |
|---|---|
| `zona_lamina1_plaques_1a1.svg` | Placa massissa i dues capes amb forats |
| `zona_lamina2_parets_1a1.svg` | Posterior i dos laterals |
| `generate_zona.py` | Generador paramètric amb comprovacions |
| `plataforma_muntada.png`, `plataforma_peces_separades.png` | Imatges de la plataforma muntada i de les peces separades i numerades |
| `render_plataforma.py`, `render_peces_separades.py` | Generen les imatges; necessiten numpy i matplotlib |

Els SVG ja incorporen un kerf de 0,15 mm: no s'ha d'afegir cap compensació a la màquina.

Abans de tallar, prova el gruix real amb `calibratge_encaixos_1a1.svg`. Si cal, canvia `thickness`, `kerf` o `fit_clearance` al generador i executa'l amb `python3 generate_zona.py`.

El receptacle de la zona lila és la mateixa plataforma sense les dues capes amb forats: només es munten la placa massissa i les parets.

## Muntatge

Números de l'esquema `plataforma_peces_separades.png`: 1 posterior, 2 laterals, 3 placa massissa, 4 capes amb forats.

1. Encaixa les llengüetes dels laterals (2) a les ranures del posterior (1).
2. Col·loca la placa massissa (3) sobre les llengüetes superiors.
3. Encola les dues capes amb forats (4) sobre la placa massissa, amb les vores enrasades.
