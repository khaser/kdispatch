{ lib
, pkgs
, python3
}:

python3.pkgs.buildPythonPackage rec {
  pname = "ydb";
  version = "3.11.3";
  format = "setuptools";

  doCheck = false;

  src = pkgs.fetchPypi {
    inherit pname version;
    hash = "sha256-pPdS0nNLHuwvuLYXIRcWUoCyXIOFc6am4JZLqntMIjU=";
  };

  propagatedBuildInputs = with python3.pkgs; [
    grpcio
    packaging
    protobuf
    aiohttp
  ];

}
