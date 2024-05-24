{ lib
, pkgs
, python3
, ydb
}:

python3.pkgs.buildPythonPackage rec {
  pname = "ydb_sqlalchemy";
  version = "0.0.1b17";
  format = "setuptools";

  doCheck = false;

  src = pkgs.fetchPypi {
    inherit pname version;
    hash = "sha256-cI9Qcg09uonPHgB2mfoaPj3SjVt2+GJ70JdmrbJ6u7g=";
  };

  propagatedBuildInputs = with python3.pkgs; [
     sqlalchemy
     ydb
  ];

}
