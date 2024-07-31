# Author: 赩林, xilin0x7f@163.com
import argparse

def parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-s', '--surface', required=True, nargs='+', help='input a surface file for calculating area')
    parser.add_argument(
        '-a', '--atlas', required=True, help='input a atlas file for report brain regions')

    return parser.parse_args()


args = parser()
for arg in vars(args):
    print(f"variable:{arg}, value:{getattr(args, arg)}")
