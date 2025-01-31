
    _        _    ____ _                _ _     ____        
   / \      / \  / ___(_)_ __ ___ _   _(_) |_  |  _ \ _   _ 
  / _ \    / _ \| |   | | '__/ __| | | | | __| | |_) | | | |
 / ___ \  / ___ \ |___| | | | (__| |_| | | |_  |  __/| |_| |
/_/   \_\/_/   \_\____|_|_|  \___|\__,_|_|\__| |_|    \__, |
                                                      |___/ 
                                            

Draw electronic circuits with ASCII characters.
                                                                        
                                                                        
         .---------------------o--------------o---o +1.5V               
         |                     |              |                         
         |                     |              |                         
        .-.         ||100n     |             .-.                        
        | |    .----||----.    |             | |                        
       100k    |    ||    |    |             | |1k                      
        '-'    |    ___   |  |<              '-'                        
         |     o---|___|--o--|                |                         
         |     |    1k       |\               |                         
         |   |/                |              |                         
         o---|                 |              |                         
    L    |   |>                |              |                         
    E    |     |               |              |                         
    D    |     |    \]         |     \]       |                         
         '-----)----|]---------o-----|]-------o                         
    B          |    /]+        |     /]+      |                         
    l          |    10µ       .-.    100µ     |                         
    i          |              | |             |                         
    n          |              | |47Ω          V ->                      
    k          |              '-'             -                         
    e          |               |              |                         
    r          '---------------o--------------o---o GND                 
                                                                        

This is a pythonized version of (Borland Delphi) AACircuit (by Andreas Weber).
A kind of reverse engineered version, where the idea and GUI layout are taken from the original.

For the ASCII representation, use copy or "Save ASCII". Use a monospaced font in your document, news- or mailclient!

Component library: User components are read from optional file components/user_component_x.json (x=1..5)
Every symbol has to be created for all four directions (N/E/S/W).


Usage
=====
Download the zip-file, unzip, go to the AACircuit directory and run: python aacircuit.py


Dependencies
============
Python3
xerox
platformdirs
pypubsub
bresenham
Gtk+ 3


Windows
============
use pacman if prefer to list full architecture
package explicitly (e.g. i686, x86_64 on msys2)

pacboy -S gtk3 python-pywin32 python-gobject
pip install xerox platformdirs pypubsub bresenham

Original: https://github.com/Andy1978/AACircuit
