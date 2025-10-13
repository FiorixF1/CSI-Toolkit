
# DDR Overlays
Stream overlays for RotorHazard as a plugin. You can use these in OBS or any other streaming software with browser input. These are used and made by Dutch Drone Racing but totally free to use.

> [!IMPORTANT]
> This plugin is still a work in progress. The code should be cleaned and a few more overlays should be added. Feel free to help!

## Overlays
- Single Pilot Node
- Live Results
- Race Status Bar
- Qualifier Leaderboard
- Qualifier Leaderboard / 4 pages
- Brackets
- 'Last Heat' display
- 'Next Up' display
- Podium

## Installation
Download the latest release and put the **ddr_overlays** folder in the **plugins** folder of your RotorHazard installation. (Re-)Start your RotorHazard server.

On the settings page of your RotorHazard panel the section `DDR - OBS Overlays` shows up. Press the link, it will bring you to the page with links to the overlays. A friendly menu will let you choose the bracket type and the class used as data source for the content of the overlay: select the desired options then click on the link you want to display. The URL will be generated dynamically on a new browser page according to the selected options.

To setup country flags, pilot avatars and team logos refer to the **Important Information** below.

## Important Information

### Pilot Avatars
Pilot avatars are obtained from the `/rh-data/shared/avatars/` folder. The file name should be the pilot's callsign in lowercase where spaces has been replaced for underscores (_) and in the .webp file type. The file should be 595x814 pixels. If no avatar is found it will show the default avatar.

The page with links to overlays gives the possibility to visualize and upload the pilot avatars directly from the browser without the need to manually copy them into the SD card. Avatars can be uploaded individually for each pilot or in one shot through a zip archive.

### Country Flags
A country can be set as pilot attribute in the pilots tab (dropdown). When set it shows the flag icon before the pilot's callsign.

### Team Logo
Teams are stored in the text file `/static/data/teams.txt` and can be set as pilot attribute in the pilots tab (dropdown).

Team logos are obtained from the `/static/imgs/teams/` folder. The file name should be the team's name in lowercase where spaces have been replaced for underscores (_) and in the .png file type. If no team is found, it will show the default logo.

The page with links to overlays gives the possibility to visualize and upload the team logos directly from the browser without the need to manually copy them into the SD card. Currently logos can be uploaded only individually for each team.

### Brackets
These are the supported brackets, other will follow:
- 16 double-elimination (MultiGP, 4-up, 16-pilot)
- 16 double-elimination (FAI, 4-up, 16-pilot)
- 32 double-elimination (FAI, 4-up, 32-pilot)
- 8 double-elimination DDR

The advice is to load the whole page as 1 source in OBS and then make 2 scenes, one for the Winner Bracket and one for the Lower Bracket and crop the source accordingly. This way you can easily switch between the two.

## Screenshots

![Next Up](https://dutchdroneracing.com/wp-content/uploads/2024/07/nextup.jpg)

![Next Up](https://dutchdroneracing.com/wp-content/uploads/2024/07/nextup2.jpg)

![Nodes, Status Bar & Leaderboard](https://dutchdroneracing.com/wp-content/uploads/2024/07/nodes.jpg)

![Leaderboard](https://dutchdroneracing.com/wp-content/uploads/2024/07/leaderboard.jpg)

![Winner Bracket](https://dutchdroneracing.com/wp-content/uploads/2024/07/winner_bracket.jpg)

![Lower Bracket](https://dutchdroneracing.com/wp-content/uploads/2024/07/lower_bracket.jpg)

## Feedback

If you have any feedback, please create an issue on this repository.
