# Barrera d'accés a la zona lila

Disseny vigent: barrera tipus pàrquing, sense corda ni pedal. Un robot empeny una pala que sobresurt, la barrera puja, i dos topalls limiten el gir entre 0° i 80°. En deixar d'empènyer, es tanca pel seu propi pes. Sota el braç hi ha un faldó que deixa 35 mm lliures sobre el taulell, perquè una bobina tombada (50 mm) no pugui passar per sota de la barrera tancada. Prototip sense fabricar: mides i masses pendents d'assaig.

La barrera és independent del receptacle. El receptacle es col·loca a la cantonada del fons i de la dreta del taulell, i la barrera al seu costat esquerre, amb la base tocant el receptacle i el fons.

| Fitxer | Contingut |
|---|---|
| `barrera_peca_mobil.stl`, `barrera_peca_mobil.step` | Peça mòbil impresa en 3D, d'una sola peça: braç amb faldó, pala i superfície de contacte |
| `barrera_lamina_1a1.svg` | Làmina de tall de 420 × 297 mm en contraplacat de 3 mm: base, dos muntants i paret |
| `generate_barrera.py` | Generador paramètric, amb el càlcul del moment de tancament i les comprovacions del faldó |

La làmina ja incorpora un kerf de 0,15 mm. També calen un cargol M4 per a l'eix, dos cargols M4 per als topalls, volanderes i cola. El receptacle és la plataforma de `../plataforma`, sense les dues capes amb forats.

Executa'l amb `python3 generate_barrera.py` (làmina) o amb `PYTHONIOENCODING=utf-8 FreeCADCmd "$PWD/generate_barrera.py"` (làmina i peça mòbil). FreeCAD falla si el camí té accents: en aquest cas, copia el generador a una carpeta sense accents i executa'l allà. Les imatges es generen amb `render_muntatge.py`, que necessita numpy i matplotlib.

## Impressió de la peça mòbil

PLA, 0,2 mm de capa, 2 perímetres i 30 % de farciment, amb la cara plana sobre el llit. La massa estimada és de 36 g, i la força horitzontal màxima per obrir-la, d'uns 0,7 N; cal pesar el prototip i comprovar que un robot l'obre.

## Muntatge

1. Encola els dos muntants, l'un sobre l'altre, amb els forats alineats.
2. Encaixa la llengüeta de la paret a la ranura dels muntants, i les llengüetes inferiors a la base.
3. Munta la peça mòbil a l'eix, amb la superfície de contacte cap a la banda contrària dels muntants, amb volanderes i sense collar-la, i col·loca els dos topalls.
4. Col·loca el receptacle a la cantonada i la barrera al seu costat, amb la base tocant el receptacle i el fons.
