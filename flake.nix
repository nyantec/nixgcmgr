{
  description = "A tool to manage Nix GC root symlinks";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs, flake-utils }: {
    overlay = final: prev: {
      nixgcmgr = final.callPackage ./default.nix {};
    };
  } // (flake-utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs {
      inherit system; overlays = [ self.overlay ];
    };
  in {
    packages = {
      nixgcmgr = pkgs.nixgcmgr;
      default = self.packages.${system}.nixgcmgr;
    };

    devShells.default = pkgs.mkShell {
      inputsFrom = [ self.packages.${system}.default ];
      nativeBuildInputs = with pkgs; [ mypy ];
      PIP_DISABLE_PIP_VERSION_CHECK = "true";
    };
  }));
}
