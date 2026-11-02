# Peces 3D

Model de les peces del MEET Robotics Challenge. Prototip sense imprimir: dimensions pendents d'assaig.

Totes les peces són la mateixa bobina i només canvia el color.

| Fitxer | Contingut |
|---|---|
| `bobina.stl`, `bobina.step` | Bobina simètrica: extrems Ø 50 mm, cintura Ø 34 mm, 80 mm d'altura |
| `generate_peces.py` | Generador paramètric |

Per canviar una mida, edita el perfil del generador i executa'l amb `python3 generate_peces.py` (STL) o amb `FreeCADCmd generate_peces.py` (STL i STEP).

La massa que mostra el generador és una estimació. Els colors i els paràmetres d'impressió són a la guia per als participants.
