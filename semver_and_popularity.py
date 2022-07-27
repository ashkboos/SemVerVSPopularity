import os
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import stats

inDir = 'MavenResultsAnalysis/resources/new/'

sns.set_theme()


class Major:
    def __init__(self, groupId, artifactId, majorVersion, violations, numberMethods, callables):
        self.groupId = groupId
        self.artifactId = artifactId
        self.majorVersion = majorVersion
        self.violations = violations
        self.numberMethods = numberMethods
        self.callables = callables


class Artifact:
    def __init__(self, groupId, artifactId, violations, numberMethods, callables):
        self.groupId = groupId
        self.artifactId = artifactId
        self.violations = violations
        self.numberMethods = numberMethods
        self.callables = callables


def to_string(inp):
    if inp == 'breaking_changes':
        return 'breaking changes'
    else:
        return 'illegal API extensions'


def read_file(file: str):
    # Use a breakpoint in the code line below to debug your script.
    path = Path('resources/' + file + '.txt')
    print('reading ', path)
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


def read_popularity(metric: str):
    popularities = dict()
    files = set()
    for version in breaking_changes:
        if len(version.callables) > 0:
            package_name = version.groupId + ':' + version.artifactId + '$'
            prefixed_files = [filename for filename in os.listdir(Path(os.getcwd()).parent.joinpath(inDir)) if
                              filename.startswith(package_name)]

            if len(prefixed_files) > 0:
                files.add(str(prefixed_files[0]))

    for one in files:
        try:
            with open(Path(os.getcwd()).parent.joinpath(
                    inDir + one + '/' + metric + '.bin')) as file:
                for line in file:
                    callable_id = line.split(",")[0]
                    popularity = line.split(",")[1][:-1]
                    popularities[callable_id] = popularity
        except FileNotFoundError:
            continue

    return popularities


def compress_major_to_package(versions):
    compressed_set = set()

    for version in versions:
        found = False
        for entry in compressed_set:
            if entry.groupId == version.groupId and entry.artifactId == version.artifactId:
                entry.numberMethods = max(entry.numberMethods, version.numberMethods)
                entry.violations += version.violations
                entry.callables += version.callables
                found = True
        if not found:
            compressed_set.add(Artifact(version.groupId, version.artifactId, version.violations, version.numberMethods,
                                        version.callables))

    return compressed_set


def trendline(violation):
    if violation == 'breaking_changes':
        versions = breaking_changes
    else:
        versions = api_extensions

    bc_array = list(map(lambda x: x.violations, versions))
    method_array = list(map(lambda x: x.numberMethods, versions))
    zipped = zip(method_array, bc_array)
    filtered = list(filter(lambda x: x[1] > 0 and x[0] > 0, zipped))
    filtered_x = list(map(lambda x: x[0], filtered))
    filtered_y = list(map(lambda x: x[1], filtered))

    sns.regplot(x=filtered_x, y=filtered_y, order=1)
    plt.xlabel("Total number of methods")
    plt.ylabel("Total number of " + to_string(violation))
    plt.yscale("log")
    plt.xscale("log")
    plt.savefig('plots/trendline_' + violation + '_compressed.pdf')
    plt.show()


def violin(violation):
    if violation == 'breaking_changes':
        versions = breaking_changes
    else:
        versions = api_extensions

    percentages = list(map(lambda x: x.violations / x.numberMethods, versions))
    filtered = [x for x in percentages if 0.6 > x > 0]
    # f = plt.figure(figsize=[6,3])
    sns.violinplot(x=filtered)
    plt.xlabel("Ratio of " + to_string(violation) + " to respective number of methods")
    ax = plt.gca()
    ax.set_xlim([None, 0.55])
    # plt.savefig('plots/violin_' + violation + '.pdf')
    plt.show()


def histogram(violation):
    if violation == 'breaking_changes':
        versions = breaking_changes
    else:
        versions = api_extensions
    bc_list = list()

    for version in versions:
        bc_list.append(version.violations / version.numberMethods * 100)

    bc_list.sort()
    non_zeros = [x for x in bc_list if x != 0]
    sns.histplot(x=non_zeros, bins=30, binrange=[0, 30])
    plt.ylabel("Number of artifacts")
    viol_str = to_string(violation)
    plt.xlabel("Percentage of methods with " + viol_str)

    avg_value = sum(non_zeros) / len(non_zeros)
    ones = [x for x in non_zeros if x >= 10]
    print(viol_str + ' len of ones : ', len(ones), len(ones)/len(non_zeros)*100 , '%')
    print(viol_str + ' len of all : ', len(bc_list))
    print(viol_str + ' non zero len :', len(non_zeros))
    print(viol_str + ' average non zero : ' + str(avg_value))

    # plt.yscale('log')
    plt.savefig('plots/histogram-' + violation.replace('_', '-') + '-compressed.pdf')
    plt.show()


def calculate_popularity(pop_metric):
    pop_dict = read_popularity(pop_metric)

    bc_callables_ids = list()
    bc_popularity_metrics = list()
    all_popularity_metrics = list()
    callable_ids = set()
    with open('resources/callables.txt') as callable_file:
        for callable_id in callable_file.readline().split(","):
            callable_ids.add(callable_id)

    for version in breaking_changes:
        for callable_bc in version.callables:
            callable_id = callable_bc.split('/')[0]
            bc_callables_ids.append(callable_id)
            if callable_id in pop_dict:
                if pop_dict[callable_id] != 'na':
                    bc_popularity_metrics.append(float(pop_dict[callable_id]))

    for callable_id in pop_dict.keys():
        if callable_id not in bc_callables_ids and pop_dict[callable_id] != 'na' \
                and callable_id in callable_ids:
            all_popularity_metrics.append(float(pop_dict[callable_id]))
    print('poplen', len(all_popularity_metrics))
    non_zero_no_bc = list(filter(lambda x: x > 0.0, all_popularity_metrics))
    non_zero_bc = list(filter(lambda x: x > 0.0, bc_popularity_metrics))

    print("all no bc : %s" % (len(all_popularity_metrics)))
    print("no bc zeros: %s" % (len(all_popularity_metrics) - len(non_zero_no_bc)))
    print("all bc: %s" % (len(bc_popularity_metrics)))
    print("bc zeros: %s" % (len(bc_popularity_metrics) - len(non_zero_bc)))

    sns.kdeplot(non_zero_bc, label="Methods involved in a breaking change", cut=0)
    sns.kdeplot(non_zero_no_bc, label="Methods not involved in a breaking change", cut=0)
    plt.xlabel("Percentage of dependents that call method")

    plt.legend()
    # plt.savefig('plots/kdeplot_' + pop_metric + '.pdf')
    plt.show()

    f, ax = plt.subplots(2, figsize=(8, 6))

    ax[0].set_xlim(-0.17, 1.18)
    ax[1].set_xlim(-0.17, 1.18)

    sns.violinplot(x=non_zero_no_bc, ax=ax[0], cut=0)
    sns.violinplot(x=non_zero_bc, ax=ax[1], cut=0)

    ax[0].set_title("All methods")
    ax[1].set_title("Methods involved in a breaking change")

    plt.subplots_adjust(hspace=0.4)
    # plt.savefig('plots/violin_popularity_' + pop_metric + '.pdf')
    plt.show()

    print(stats.ttest_ind(non_zero_no_bc, non_zero_bc, alternative='greater'))
    print(stats.ttest_ind(non_zero_no_bc, non_zero_bc, alternative='less'))
    print(stats.ttest_ind(non_zero_no_bc, non_zero_bc, alternative='two-sided'))


def average_breaking_changes():
    bc_dict = defaultdict(int)
    number_of_major_versions = defaultdict(int)
    total_methods = defaultdict(int)

    for bc in breaking_changes:
        key = str(bc.groupId + ':' + bc.artifactId)
        bc_dict[key] += bc.violations
        total_methods[key] += bc.numberMethods
        number_of_major_versions[key] += 1

    filtered_bc = dict(filter(lambda x: x[1] > 0, bc_dict.items()))
    output = defaultdict(float)
    for key in filtered_bc.keys():
        output[key] = bc_dict[key] / (total_methods[key] / number_of_major_versions[key])

    sum = 0
    for value in output.values():
        sum += value
    print(sum / len(output))


def quintile_dep_percentage():
    popularities = read_popularity("public-dependent-percentage")

    xs = np.arange(0, 5 + 1 / len(popularities), 5 / (len(popularities) - 1))
    i = [float(x) for x in popularities.values()]
    sns.regplot(x=xs, y=i)
    plt.savefig('plots/quintile-dep-percentage.pdf')


def intersect(removed, added):
    removals = set()
    additions = set()
    for version in removed:
        if version.violations != 0:
            removals.add(version.groupId + version.artifactId)

    for version in added:
        if version.violations != 0:
            additions.add(version.groupId + version.artifactId)
    print("removals: ", len(removals))
    print("additions: ", len(additions))
    print("uniton", len(removals.union(additions)))

if __name__ == '__main__':
    try:
        os.makedirs('plots')
    except OSError:
        pass
    bc = read_file('breaking_changes')
    ext = read_file('api_extensions')
    breaking_changes = compress_major_to_package(bc)
    api_extensions = compress_major_to_package(ext)
    average_breaking_changes()
    intersect(breaking_changes, api_extensions)

    for violation in 'breaking_changes', 'api_extensions':
        # violin(violation)
        histogram(violation)
        trendline(violation)

    # for metric in 'dependent-percentage', 'eigenvector', 'degree':
        calculate_popularity('dependent-percentage')
    quintile_dep_percentage()
