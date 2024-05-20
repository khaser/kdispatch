# Only this configuration file will be put into image,
# so it will be better to write all configuration here.
# It allows rebuild configuration by vm itself
{ pkgs, ... }:
let
  db_ip = "10.0.0.1";
in
{
  fileSystems."/" = {
    device = "/dev/disk/by-label/nixos";
    fsType = "ext4";
    autoResize = true;
  };

  boot.growPartition = true;
  boot.kernelParams = [ "console=ttyS0" ];
  boot.loader.grub.device = "/dev/vda";
  boot.loader.timeout = 0;

  environment.systemPackages = with pkgs; [
    vim
    git
    tmux
  ];

  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
  };

  users.groups.anon = {};
  users.users = {
    anon = {
      description = "No-login user, used by default on ssh login for port-forwarding";
      password = "";
      isSystemUser = true;
      group = "anon";
    };
  };

  networking.firewall.enable = false;

  services = {
    cloud-init = {
      enable = true;
    };
    openssh = {
      enable = true;
      listenAddresses = [ { addr = "0.0.0.0"; port = 22; } ];
      settings = {
        GatewayPorts = "yes";
      };
      extraConfig = ''
        PermitEmptyPasswords yes
      '';
    };
  };

  system.stateVersion = "23.11";
}
