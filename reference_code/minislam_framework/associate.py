import argparse
import sys
import os
import numpy

def read_file_list(filename):
    file = open(filename)
    data = file.read()
    lines = data.replace(","," ").replace("\t"," ").split("\n")
    list = [[v.strip() for v in line.split(" ") if v.strip()!=""] for line in lines if len(line)>0 and line[0]!="#"]
    list = [(float(l[0]),l[1:]) for l in list if len(l)>1]
    return dict(list)

def associate(first_list, second_list, offset, max_difference):
    first_keys = list(first_list.keys())
    second_keys = list(second_list.keys())
    potential_matches = [(abs(a - (b + offset)), a, b) for a in first_keys for b in second_keys if abs(a - (b + offset)) < max_difference]
    potential_matches.sort()
    matches = []
    first_flag = set()
    second_flag = set()
    for diff, a, b in potential_matches:
        if a not in first_flag and b not in second_flag:
            first_flag.add(a)
            second_flag.add(b)
            matches.append((a, b))
    matches.sort()
    return matches

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('first_file')
    parser.add_argument('second_file')
    parser.add_argument('--offset', default=0.0, type=float)
    parser.add_argument('--max_difference', default=0.02, type=float)
    args = parser.parse_args()

    first_list = read_file_list(args.first_file)
    second_list = read_file_list(args.second_file)
    matches = associate(first_list, second_list, args.offset, args.max_difference)

    for a, b in matches:
        print("%f %s %f %s" % (a, " ".join(first_list[a]), b, " ".join(second_list[b])))
