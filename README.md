# wasd-presser

Holds **W → A → S → D** for 0.75 s each, in a loop. Toggle it with global hotkeys.

Works on **Windows** and **Linux** (Wayland and X11).

## Hotkeys

| Key | Action |
|-----|--------|
| `F5` | Start |
| `F6` | Stop |
| `Ctrl+C` | Quit (in the terminal) |

## Requirements

Python 3.

### Windows

No extra packages. It sends scan codes with `SendInput`, so most games pick up the key presses.

- If the game runs as administrator, run the script as administrator too.
- Some anti-cheat systems block simulated input.

### Linux

```sh
pip install evdev
```

Your user needs to be able to read `/dev/input/*` and write to `/dev/uinput`:

```sh
sudo usermod -aG input $USER   # log out and back in afterwards
```

If you still can't write to `/dev/uinput`, add a udev rule or run the script with `sudo`.

## Usage

```sh
python3 wasd_presser.py
```

## Configuration

Edit the constants at the top of `wasd_presser.py`:

```python
HOLD_TIME = 0.75                              # seconds per key
KEYS = ["w", "a", "s", "d"]                   # keys, in order
```
