# cmdhex
Command line editor for binary files or Intel HEX files

## Command line options
```
usage: cmdhex.py [-h] [-f {bin,hex}] [-o {bin,hex}] filename

positional arguments:
  filename

optional arguments:
  -h, --help            show this help message and exit
  -f {bin,hex}, --in-format {bin,hex}
                        Format of the file being read
  -o {bin,hex}, --out-format {bin,hex}
                        Format to use when writing to the file. If unspecified, the input and output formats are assumed to match
```

## Keyboard bindings

  * __Left/Right/Up/Down__: Move the cursor. In some terminals the mouse wheel can also be used to scroll up and down.
  * __Escape__: Exit edit mode

### When not in edit mode:
  * __i__: Enter edit mode, where new bytes are inserted into the file (like insert mode in vim)
  * __R__: Enter edit mode, where new bytes replace existing bytes (linek replace mode in vim)
  * __Tab__: Toggle between hexadecimal and ASCII modes (only when not in edit mode)
  * `:q`: Exit the editor
  * `:w`: Save the file
  * `:wq`: Save and exit

