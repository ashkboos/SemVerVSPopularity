from collections import defaultdict
from pathlib import Path
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import random


class Major:
    def __init__(self, groupId, artifactId, majorVersion, violations, numberMethods, callables):
        self.groupId = groupId
        self.artifactId = artifactId
        self.majorVersion = majorVersion
        self.violations = violations
        self.numberMethods = numberMethods
        self.callables = callables


class Artifact:
    def __init__(self, groupId, artifactId, violations, numberMethods):
        self.groupId = groupId
        self.artifactId = artifactId
        self.violations = violations
        self.numberMethods = numberMethods


def to_string(inp):
    if inp == 'breaking_changes':
        return 'breaking changes'
    else:
        return 'illegal API extensions'


def read_file():
    # Use a breakpoint in the code line below to debug your script.
    path = Path('breaking_changes.txt')
    print(path)
    with open(path, 'r') as file:
        versions = set()
        file.readline()

        for version in file:
            if version[0] == '#': continue
            groupId = version.split(":")[0]
            artifactId = version.split(":")[1]
            majorVersion = int(version.split(":")[2])
            violations = int(version.split(":")[3].split("/")[0])
            numberMethods = int(version.split(":")[3].split("/")[1])
            callables = [x.strip() for x in version.split(":")[4][1:-2].split(",")]
            if str(callables) == "['']":
                callables = list()
            versions.add(Major(groupId, artifactId, majorVersion, violations, numberMethods, callables))
    return versions


def compress_major_to_package(versions):
    compressed_set = set()

    for version in versions:
        found = False
        for entry in compressed_set:
            if entry.groupId == version.groupId and entry.artifactId == version.artifactId:
                entry.numberMethods = max(entry.numberMethods, version.numberMethods)
                entry.violations += version.violations
                found = True
        if not found:
            compressed_set.add(Artifact(version.groupId, version.artifactId, version.violations, version.numberMethods))

    return compressed_set


def percentage_in_n_windows(first, second, n, max):
    interval = max / n
    window = [0, interval]
    result = list()

    while window[1] <= max:

        second_count = count_values_in_window(second, window, max)
        first_count = count_values_in_window(first, window, max)
        if second_count > 0 and first_count != 1:
            if first_count != 0:
                window_value = second_count / first_count
            else:
                window_value = 0
            result.append(window_value)
        window = [window[1], window[1] + interval]

    return result


def count_values_in_window(values, window, max):
    upper_bound = window[1]
    if window[1] == max:
        upper_bound = 2
    return sum(window[0] <= i < upper_bound for i in values)


def histogram_of_popularities_bc_all(bc, all):
    sns.histplot(data=all, color="#7f8fa6", label="all versioned packages", alpha=1, bins=10)
    sns.histplot(data=bc, color="#0097e6", label="versioned packages with breaking changes", alpha=1, bins=10)
    plt.yscale('log')
    plt.legend()
    plt.xlabel('popularity of versioned packages')
    plt.ylabel('number of versioned packages (log scale)')
    plt.show()
    plt.savefig('tess.pdf')


def pairs_of_popularities(bc, all):
    bc_non_zero = [i for i in bc if i != 0]
    no_bc_non_zero = [i for i in all if i != 0]
    no_bc_same_size = random.choices(no_bc_non_zero, k=len(bc_non_zero))
    a = np.array(no_bc_same_size)
    b = np.array(bc_non_zero)
    c = np.divide(a, b)
    i = sns.lineplot(data=sorted(c))
    print(len(c))
    i.set_xlabel("pairs of versioned packages")
    i.set_ylabel("popularity of random vps divided by braking change vps")
    i.figure.savefig("random.pdf")


if __name__ == '__main__':
    versions = read_file()
    files = set()
    popularity_per_artifact = defaultdict(int)
    dependent_per_artifact = defaultdict(set)
    all_dependents = set()
    for version in versions:
        package_name = version.groupId + '_' + version.artifactId
        prefixed_files = [filename for filename in os.listdir('input/') if filename.startswith(package_name)]
        if len(prefixed_files) > 0:
            files.add(str(prefixed_files[0]))

    for one in files:
        try:
            with open('input/' + one + '/' + 'dependents.txt') as file:
                for line in file:
                    all_dependents.add(line)
                    popularity_per_artifact[one.split("_")[0] + ":" + one.split("_")[1]] += 1
                    dependent_per_artifact[one.split("_")[0] + ":" + one.split("_")[1]].add(line)
        except FileNotFoundError:
            continue

    print("all dependents: " + str(len(all_dependents)))
    print(len(popularity_per_artifact.keys()))

    for package in popularity_per_artifact.keys():
        if package not in dependent_per_artifact.keys():
            popularity_per_artifact[package] /= len(all_dependents)
            continue
        popularity_per_artifact[package] = len(dependent_per_artifact[package]) / len(all_dependents)

    compressed = compress_major_to_package(read_file())
    print("compressed: " + str(len(compressed)))

    # KDE plot with or without breaking changes
    all = list()
    bc = list()

    for entry in compressed:
        if entry.violations > 0:
            bc.append(popularity_per_artifact[entry.groupId + ":" + entry.artifactId])
        all.append(popularity_per_artifact[entry.groupId + ":" + entry.artifactId])

    n = 130
    max_all = max(all)
    dots = percentage_in_n_windows(all, bc, n, max_all)
    print(len(dots))
    intervals = np.arange(0, max_all, max_all / len(dots))
    sns.set_theme()
    q = sns.regplot(y=dots, x=intervals, order=2)
    plt.ylim(0, 1)
    q.set_xlabel("popularity of versioned packages")
    q.set_ylabel("ratio of versioned packages with violation")
    q.figure.savefig("popularity_vs_violation" + str(n) + ".pdf")

