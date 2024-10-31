# Radio-Gholam

A gholam for playing media URLs and some TV/Radio stations in Discord voice channels.

## Some features:

- Playback of direct links to media files and streams
- Built-in playlist (loop, shuffle, export, import, ...)
- Supports optional http proxies to access media links in certain regions.

## Get Started

1. Clone the repository
   ```
   git clone https://github.com/aedangaming/Radio-Gholam.git
   ```
2. Copy `sample.env` file to `.env`
   ```
   cd Radio-Gholam
   cp sample.env .env
   ```
3. Populate `.env` file with your secret information. (Bot token and etc.)
4. Preferably create a new virtual environment and activate it
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
5. Install required packages
   ```
   pip install -r requirements.txt
   ```
6. Run `main.py` script
   ```
   python3 main.py
   ```

# To-Do

- Support playback of youtube and spotify links
