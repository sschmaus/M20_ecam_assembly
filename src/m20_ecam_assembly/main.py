import argparse
import sys

from m20_ecam_assembly.assemble_tiles import assemble_from_glob

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', default='./*.png', help='glob pattern for input files')

    args = parser.parse_args()

    assemble_from_glob(args.input)


if __name__ == '__main__':
    sys.exit(main())
