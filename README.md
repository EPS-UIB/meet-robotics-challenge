# MEET Robotics Challenge 2027 — models de fabricació

Models per imprimir en 3D i tallar amb làser les peces del taulell del [MEET Robotics Challenge](https://blocs.uib.cat/eps/meet-robotics-challenge/), organitzat per l'Escola Politècnica Superior de la Universitat de les Illes Balears.

Les regles, les mides del taulell i la posició de cada element són a la guia per als participants. Aquest repositori només conté els fitxers per fabricar les peces. L'organització fabrica les de la competició; els centres en poden fer còpies per entrenar.

> **Esborrany.** Cap peça no s'ha fabricat ni assajat encara. Les mides poden canviar després dels assaigs de l'organització.

## Què cal per a un taulell complet

| Element | Quantitat | Fabricació | Carpeta |
|---|---:|---|---|
| Bobina | 7 (2 vermelles, 2 blaves, 2 lila, 1 verda) | Impressió 3D | [`bobina/`](bobina/) |
| Plataforma de les zones vermella i blava | 2 | Tall làser, contraplacat de 3 mm | [`plataforma/`](plataforma/) |
| Receptacle de la zona lila | 1 | La mateixa plataforma, sense les dues capes amb forats | [`plataforma/`](plataforma/) |
| Barrera de la zona lila | 1 | Peça mòbil impresa en 3D; base, muntants i paret tallats amb làser; 3 cargols M4 | [`barrera/`](barrera/) |

Cada carpeta té un `LLEGEIX-ME.md` amb els fitxers, les instruccions de fabricació i el muntatge.

## Fitxers

- **STL i STEP:** peces per imprimir en 3D.
- **SVG a escala 1:1:** làmines de tall làser. Ja incorporen una compensació de tall (kerf) de 0,15 mm. Abans de tallar, proveu el gruix real del contraplacat amb `plataforma/calibratge_encaixos_1a1.svg`.
- **PNG:** imatges de muntatge.
- **Python:** generadors paramètrics dels models. No cal executar-los per fabricar les peces; serveixen per ajustar mides. Alguns necessiten [FreeCAD](https://www.freecad.org/) per generar el STEP.

## Bobines

PLA mat, 0,2 mm d'altura de capa, 4 perímetres, 8 capes superiors i inferiors, 30 % de farciment giroide, dreta i sense suports. La marca i la referència del filament de cada color es publicaran a la guia, perquè les bobines d'entrenament siguin iguals que les de la competició.

## Llicència

[Creative Commons Reconeixement 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.ca). Podeu fer servir, copiar i modificar aquests models per a qualsevol finalitat, citant-ne la font: *MEET Robotics Challenge, Escola Politècnica Superior, Universitat de les Illes Balears*.

## Contacte

at.eps@uib.es
