# knit-code-lib

clone with command: `git clone --recurse-submodules https://github.com/gabrielle-ohlson/knit-code-lib`

## Importing the `knitout-frontend-py` submodule
If you didn't clone with the flag `--recurse-submodules`, run the command `git submodule init` and then `git submodule update` to add the necessary submodules to the project. \

Next, create a symbolic link to the `knitout.py` file in the `knitout-frontend-py` directory, so that you can just do `import knitout` in a python file located in the main directory (see `example.py` for reference).

To create a symbolic link on Unix-based systems, run the following command:
```
ln -s knitout-frontend-py/knitout.py knitout.py
```

On Windows, run:
```
mklink knitout.py knitout-frontend-py\knitout.py
```