#!/bin/bash
set -e

PKGVER="0.1.0"
TAR_NAME="spotube-converter-$PKGVER.tar.gz"

echo "Creating source tarball..."
mkdir -p build_tmp/spotube-converter
cp -r spotube_converter pyproject.toml build_tmp/spotube-converter/
cd build_tmp
tar -czvf ../$TAR_NAME spotube-converter
cd ..
rm -rf build_tmp

echo "Building Arch package..."
makepkg -sf

echo ""
echo "Package built! You can install it using:"
echo "sudo pacman -U spotube-converter-$PKGVER-1-any.pkg.tar.zst"
