# wasd-presser

Holds **W → A → S → D** for 0.75 s each, in a loop. Toggle it with global hotkeys.

Built on `evdev`/`uinput`, so it works on **Linux under Wayland** as well as X11.

## Hotkeys

| Key | Action |
|-----|--------|
| `F5` | Start |
| `F6` | Stop |
| `Ctrl+C` | Quit (in the terminal) |

## Requirements

- Linux
- Python 3
- [`evdev`](https://pypi.org/project/evdev/)

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
KEYS = [e.KEY_W, e.KEY_A, e.KEY_S, e.KEY_D]   # keys, in order
```
