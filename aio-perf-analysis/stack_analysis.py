#!/usr/bin/python

# Project Clearwater - IMS in the Cloud
# Copyright (C) 2016 Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.

"""
This script analyses two directories, a baseline directory and a new directory,
which contain performance data generated by perfrun.sh.

It compares the per-function CPU usage for the given component.

"""

import re
import gzip
import argparse
from glob import glob
from collections import defaultdict

regex = re.compile("\s+[\d\.]+%\|")


def record_stacks(dict, f):
    """Parses a file generated by 'perf report' into a dictionary mapping
    functions to cumulative time spent"""
    cls = [l.rstrip() for l in f.readlines() if regex.match(l)]
    for cl in cls:
        cumulative, self, binary, library, function = cl.split("|")
        function = function[4:]
        cumulative = float(cumulative.replace("%", ""))
        if function not in dict:
            dict[function] = []
        dict[function].append(cumulative)


def compare_two_runs(component, baseline_dir, new_dir):
    baseline_dict = {}
    new_dict = {}

    baseline_files = glob(baseline_dir + "/perf_*/" + component + ".perf.report.gz")
    new_files = glob(new_dir + "/perf_*/" + component + ".perf.report.gz")

    for a in baseline_files:
        with gzip.open(a) as f:
            record_stacks(baseline_dict, f)

    for b in new_files:
        with gzip.open(b) as f:
            record_stacks(new_dict, f)

    baseline_results = defaultdict(lambda: 0)
    new_results = defaultdict(lambda: 0)

    for k, v in baseline_dict.iteritems():
        baseline_results[k] = sum(v) / len(baseline_files)

    for k, v in new_dict.iteritems():
        new_results[k] = sum(v) / len(new_files)

    functions = list(set(baseline_results.keys() + new_results.keys()))
    functions.sort(key=lambda x: baseline_results[x] - new_results[x], reverse=True)
    for f in functions[:20]:
        print "{}: {}% CPU in baseline, {}% in new release".format(f, baseline_results[f], new_results[f])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline')
    parser.add_argument('--new')
    parser.add_argument('--component')

    args = parser.parse_args()

    compare_two_runs(args.component, args.baseline, args.new)

if __name__ == "__main__":
    main()