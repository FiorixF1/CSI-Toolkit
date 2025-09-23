# RotorHazard Class Rank Brackets
"Brackets" class ranking plugin for RotorHazard

This plugin has been designed to be used along with single and double elimination brackets.

It supports:
* MultiGP format with Chace the Ace and Iron Man rule (16 pilots, double elimination)
* FAI brackets according to F9U rules (16/32/64 pilots, both single and double elimination)
* CSI Drone Racing format (16 pilots, double elimination)
* Unofficial 8 pilots double elimintion brackets by DDR, both MultiGP-like and FAI-like


## Installation

Install through the "Community Plugins" area within RotorHazard. Alternately, copy the `class_rank_brackets` directory from inside `custom_plugins` into the plugins directory of your RotorHazard data directory.


## Usage

After creating a class, select "Brackets" for the class ranking method. Using the settings button, enter the bracket type, choose the class used in qualification stage and set whether to use or not the Chace the Ace format and the Iron Man rule. If these options are enabled, visual feedback is provided to the race director when running the last heat.

Note: once selected the general bracket type (MultiGP, FAI, CSI Drone Racing) the plugin identifies automatically the specific format (number of pilots, single or double elimination) from the number of heats in the class. For this reason the class must have a number of heats compatible with an existing bracket format, otherwise it won't be able to generate the ranking. This requirement is satisfied if the heats are generated through the built-in generators.
