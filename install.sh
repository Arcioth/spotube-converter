#!/bin/bash
set -e

echo "Checking for pipx..."
if ! command -v pipx &> /dev/null; then
    echo "pipx is not installed. Installing pipx..."
    sudo pacman -S --needed python-pipx
    pipx ensurepath
fi

echo "Installing spotube-converter globally via pipx..."
pipx install . --force

echo ""
echo "Installation complete!"
echo "You can now use the CLI from anywhere by typing:"
echo "  spotube-converter auth"
echo "  spotube-converter migrate your_playlist.csv"
