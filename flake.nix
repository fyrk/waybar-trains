{
  description = "display information from a train's WiFi network on your Waybar";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = (pkgs.python312.withPackages (ps: with ps; [
          requests
          pyroute2
        ]));
      in
      {
        packages = {
          default = pkgs.writeShellApplication {
            name = "waybar-trains";
            runtimeInputs = [ python ];
            text = ''
              PYTHONPATH="${./.}" "${python}/bin/python" -m waybar-trains "$@"
            '';
          };
        };

        devShells.default = pkgs.mkShell {
          packages = [ python ];
        };
      });
}
