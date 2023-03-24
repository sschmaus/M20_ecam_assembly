import argparse
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                        help='an integer for the accumulator')

    parser.add_argument('-i', '--input', type='str', default='./' help='glob pattern for input files')

    args = parser.parse_args()
    print(args.accumulate(args.integers))