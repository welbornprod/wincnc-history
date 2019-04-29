# WinCNC-History

File/Command history viewer for the WinCNC controller software.

## Motivation

The normal `History` feature in WinCNC does not handle long file names,
and cannot be resized. The WinCNC history list does not contain
any extra information (even though it is logged along side the files/commands).

**WinCNC-History** contains all the information found in the log (`WinCNC.csv`),
is resizable, divides files/commands into browsable sections, shows human-readable
times/dates, and calculates extra information based on the information given
(like time spent between files/commands).

## Usage

Just run `wincnc-history.py`. If it cannot find the `WinCNC.csv` file in the
default location, you can create/edit `wincnc-history.json` to contain the
`wincnc_file` key. The config file should be in the same directory as
`wincnc-history.py`:

```javascript
{
    // Use forward slashes or escaped backslashes. This is python.
    "wincnc_file": "C:/path/to/wincnc.csv"
}
````

## Dependencies

There are a few PyPi packages needed to run this. They are installable
with `pip install -r requirements.txt`.

Package: | Description:
------: | -----
[colr](https://pypi.org/project/colr) | Used for terminal colors.
[docopt](https://pypi.org/project/docopt) | Used for command-line argument parsing.
[easysettings](https://pypi.org/project/easysettings) | Used for JSON-based configuration.
[printdebug](https://pypi.org/project/printdebug) | Used for debug mode printing/logging.
