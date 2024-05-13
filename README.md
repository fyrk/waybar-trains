# waybar-trains

This is a module for [Waybar](https://github.com/Alexays/Waybar) that displays the status of the train you are currently in, using the train's API available from its WiFi network.

It was inspired by https://github.com/e1mo/waybar-iceportal and https://github.com/liclac/ambient.

These operators are currently supported:

| Operator Portal                                                                  | WiFi name        | Description                                                                                                |
| -------------------------------------------------------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------- |
| [Iceportal](https://iceportal.de)                                                | `WIFIonICE`      | German long-distance trains ICE and IC by Deutsche Bahn                                                    |
| [Zugportal](https://zugportal.de)                                                | `WIFI@DB`        | German regional trains by Deutsche Bahn                                                                    |
| [ODEG](https://www.odeg.de) ([Portal](https://wasabi.hotspot-local.unwired.at/)) | `ODEG Free WiFi` | Some regional trains in German states Berlin/Brandenburg, Mecklenburg-Vorpommern, Saxony and Saxony-Anhalt |

## Screenshot

<img src="docs/images/demo.png" alt='Screenshot of the module, it says "ICE 1601 – Berlin-Spandau – 12:08 – 12:10"' width=450>

Times include the displayed delay.

## Configuration example

After cloning the repository and installing the required Python modules (`pip install -r requirements.txt`), run waybar-trains as a Python module using `python -m waybar-trains`.

Example Waybar module configuration:

```json
"custom/trains": {
    "exec": "cd ~/path/to/waybar-trains && python -m waybar-trains",
    "return-type": "json",
    "interval": 15
}
```

### Using Home Manager

A Nix Flake is available for use with NixOS and/or Home Manager. First, add waybar-trains as an input:

```nix
{
  inputs = {
    waybar-trains.url = "git+https://codeberg.org/fyrk/waybar-trains.git";
  };
}
```

Then, add a custom module, for example:

```nix
{
  "custom/trains" = {
    "exec" = "${inputs.waybar-trains.packages.${system}.default}/bin/waybar-trains";
    "return-type" = "json";
    "interval" = 15;
  };
}
```

## CSS style

A CSS style that sets the background, text, and border colors could look like this:

```css
#custom-trains {
  border: 2px solid;
}
#custom-trains sup {
  margin-left: 10px;
}
#custom-trains.provider-iceportal {
  background: #f0f3f5;
  color: #282d37;
  border-color: #ec0016;
}
#custom-trains.provider-zugportal {
  background: #0e0e0c;
  color: #f0f3f5;
  border-color: #ec0016;
}
#custom-trains.provider-odeg {
  background: #ffffff;
  border-color: #007073;
}
```
