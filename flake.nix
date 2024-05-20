{
  description = "NixOS image for Yandex Cloud VM";

  inputs = {
    nixpkgs.follows = "khaser/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    khaser.url = "github:khaser/nix-vim-config";
  };

  outputs = { self, nixpkgs, khaser, flake-utils }:
    flake-utils.lib.eachDefaultSystem ( system:
    let
      pkgs = import nixpkgs { inherit system; };
      configured-vim = (khaser.lib.vim.override {
        extraPlugins = with pkgs.vimPlugins; [ ];
      });
      python3 = pkgs.python311;
    in
    {
      packages = {
        kdispatch-server =
          python3.pkgs.buildPythonPackage rec {
            pname = "kdispatch-server";
            version = "0.1.0";
            format = "setuptools";

            src = ./server;

            propagatedBuildInputs = with python3.pkgs; [
              setuptools
              requests
            ];

            doCheck = false;
          };

        proxy-node-img = import (nixpkgs + "/nixos/lib/make-disk-image.nix") {
          inherit pkgs;
          lib = pkgs.lib;
          config = self.packages.${system}.nixosConfigurations.default.config;
          diskSize = 8192;
          format = "qcow2";
          configFile = ./configuration.nix;
        };

        nixosConfigurations.default = nixpkgs.lib.nixosSystem {
          system = "x86_64-linux";
          modules = [
            ./configuration.nix
            (nixpkgs + "/nixos/modules/profiles/qemu-guest.nix")
            {
              systemd.services.kdispatch-server = {
                  wantedBy = [ "multi-user.target" ];
                  serviceConfig.ExecStart = "${self.packages.${system}.kdispatch-server}/bin/kdispatch-server --db_ip '10.0.0.1'";
              };
            }
          ];
        };

      };

      devShell =
        pkgs.mkShell {
          buildInputs = [
            configured-vim
            python3
          ];
        };
    });
}
