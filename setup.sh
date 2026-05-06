#!/bin/bash
echo "Setting up virtual environment..."
python -m venv .venv
source .venv/bin/activate

echo "Installing requirements..."
pip install ytmusicapi pandas

echo ""
echo "Setup complete! To proceed, you need to authenticate with YouTube Music."
echo "Please run the following commands:"
echo ""
echo "  source .venv/bin/activate"
echo "  ytmusicapi oauth"
echo ""
echo "Follow the instructions in the terminal to log in."
echo "Once authenticated (oauth.json is created), you can run the migration script:"
echo ""
echo "  python migrate.py your_spotify_playlist.csv"
echo ""