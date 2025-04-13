{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    temporal-cli
    temporal
    poetry
    overmind
  ];
}
