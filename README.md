# M20_ecam_assembly

WIP python script to reassemble the tiled images from the Mars 2020 engineering cameras. 

The current implementation is very hacky and overly complicated and is in desperate need of a rewrite. 

However, it but produces very good results for normal 2x2 and 4x4 tiled ECAM images

## Installation

```
pip install git+https://github.com/sschmaus/m20_ecam_assembly.git
```

## Usage

```
m20_ecam_assembly -i [glob pattern for the desired images]
```

## TODO

* clean up code (probably rewrite)
* propagate changed image geometry into CAHVORE model parameters
* add compatibility for tiles that are saved out of order (e.g. workspace mosaics)
* make unstretch more robust, currently it considers every zero count histogram bin as a gap (ideally only count reliable bins and extraploate from there)
