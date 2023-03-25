# M20_ecam_assembly

WIP python script to reassemble the tiled images from the Mars 2020 engineering cameras. 

The current implementation is very hacky and overly complicated but produces good results most of the time. 

## Installation

```
pip install git+https://github.com/sschmaus/m20_ecam_assembly.git
```

## Usage

```
m20_ecam_assembly -i [glob pattern for the desired images]
```

## TODO

* add comments
* clean up code (probably rewrite)
* propagate changed image geometry into CAHVORE model parameters
