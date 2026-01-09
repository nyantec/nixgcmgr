{ lib, python3Packages, nix-gitignore }:
let
  # Find gitignore files recursively in parent directory stopping with .git
  findGitIgnores = path:
    let
      parent = builtins.dirOf path;
      gitIgnore = path + "/.gitignore";
      isGitRoot = builtins.pathExists (path + "/.git");
      hasGitIgnore = builtins.pathExists gitIgnore;
      gitIgnores = if hasGitIgnore then [ gitIgnore ] else [ ];
    in
    lib.optionals (builtins.pathExists path && builtins.toString path != "/" && ! isGitRoot) (findGitIgnores parent) ++ gitIgnores;

  /*
    Provides a source filtering mechanism that:

    - Filters gitignore's
    - Filters pycache/pyc files
    - Uses cleanSourceFilter to filter out .git/.hg, .o/.so, editor backup files & nix result symlinks

    Shamelessly stolen from poetry2nix.
  */
  cleanPythonSources = { src }:
  let
    gitIgnores = findGitIgnores src;
    pycacheFilter = name: type:
      (type == "directory" && ! lib.strings.hasInfix "__pycache__" name)
      || (type == "regular" && ! lib.strings.hasSuffix ".pyc" name)
    ;
  in
  lib.cleanSourceWith {
    filter = lib.cleanSourceFilter;
    src = lib.cleanSourceWith {
      filter = nix-gitignore.gitignoreFilterPure pycacheFilter gitIgnores src;
      inherit src;
    };
  };
in
python3Packages.buildPythonApplication {
  name = "nixgcmgr";
  version = "0.1.0";
  pyproject = true;

  src = cleanPythonSources {
    src = ./.;
  };

  build-system = with python3Packages; [ setuptools ];

  # There are no tests for now
  doCheck = false;

  meta = with lib; {
    mainProgram = "nixgcmgr";
    homepage = "https://github.com/nyantec/nixgcmgr";
    description = "A tool to manage Nix GC root symlinks";
    maintainers = with maintainers; [
      vikanezrimaya
    ];
    license = licenses.miros;
    platforms = platforms.linux;
  };
}
