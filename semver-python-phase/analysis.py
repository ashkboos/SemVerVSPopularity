import os
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import stats

sns.set_theme()
project_location = '/Users/mehdi/Desktop/MyMac/Phd/Research/MyPapers/MavenAPIPopularity/semver-vs-popularity/'


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

    def get_name(self, index):
        return self.callables[index].split("/")[1], self.callables[index].split("//")[1]

    def __hash__(self) -> int:
        return hash(self.groupId + "|" + self.artifactId)

    def __str__(self) -> str:
        return self.groupId + ":" + self.artifactId


def to_string(inp):
    if inp == 'breaking_changes' or inp == 'breaking_changes_bynow':
        return 'breaking changes'
    else:
        return 'illegal API extensions'


def read_file(file: str):
    # Use a breakpoint in the code line below to debug your script.
    path = Path(project_location + 'semver-python-phase/resources/' + file + '.txt')
    with open(path, 'r') as file:
        versions = list()
        file.readline()
        i = 0
        for version in file:
            i += 1
            # if version[0] == '#': continue
            groupId = version.split(":")[0]
            artifactId = version.split(":")[1]
            majorVersion = int(version.split(":")[2])
            violations = int(version.split(":")[3].split("/")[0])
            numberMethods = int(version.split(":")[3].split("/")[1])
            callables = [x.strip() for x in version.split(":")[4][1:-2].split(", ")]
            if str(callables) == "['']":
                callables = list()
            versions.append(Major(groupId, artifactId, majorVersion, violations, numberMethods, callables))
    return versions


def read_all_coordinates(file: str):
    # Use a breakpoint in the code line below to debug your script.
    path = Path(project_location + 'semver-python-phase/resources/' + file + '.txt')
    print(path)
    with open(path, 'r') as file:
        artifacts = set()
        file.readline()
        for version in file:
            groupId = version.split(":")[0]
            artifactId = version.split(":")[1]
            artifacts.add(groupId + "|" + artifactId)

    return artifacts


def read_artifacts_txt():
    # Use a breakpoint in the code line below to debug your script.
    path = Path(project_location + 'semver-python-phase/resources/artifacts.txt')

    with open(path, 'r') as file:
        input_artifacts = set()
        for version in file:
            groupId = version.split(":")[0]
            artifactId = version.split(":")[1]
            input_artifacts.add(groupId + "|" + artifactId)

    return input_artifacts


def read_expanded_coords():
    # Use a breakpoint in the code line below to debug your script.
    path = Path(project_location + 'semver-python-phase/resources/mvn.expanded_coords.txt')
    i = 0
    with open(path, 'r') as file:
        for _ in file:
            i += 1
    return i


def read_popularity(metric: str):
    popularities = dict()
    files = set()

    for version in breaking_changes:
        if len(version.callables) > 0:
            package_name = version.groupId + ':' + version.artifactId + '$'
            prefixed_files = [filename for filename in os.listdir(Path(os.getcwd()).parent.joinpath(
                project_location + 'semver-python-phase/resources/popularity/')) if
                              filename.startswith(package_name)]
            if len(prefixed_files) > 0:
                files.add(str(prefixed_files[0]))

    for one in files:
        try:
            with open(Path(os.getcwd()).parent.joinpath(
                    project_location + 'semver-python-phase/resources/popularity/' + one + '/' + metric + '.bin')) as file:
                for line in file:
                    callable_id = line.split(",")[0]
                    popularity = line.split(",")[1][:-1]
                    popularities[callable_id] = popularity
        except FileNotFoundError:
            continue

    return popularities


def compress_major_to_package(versions):
    compressed_set = list()

    for version in versions:
        found = False
        for entry in compressed_set:
            if entry.groupId == version.groupId and entry.artifactId == version.artifactId:
                entry.numberMethods = max(entry.numberMethods, version.numberMethods)
                entry.violations += version.violations
                entry.callables += version.callables
                found = True
        if not found:
            compressed_set.append(
                Artifact(version.groupId, version.artifactId, version.violations, version.numberMethods,
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
    # plt.xlim(40, None)
    plt.savefig(
        project_location + 'semver-python-phase/resources/plots/trendline_' + violation + '.pdf')
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
    plt.savefig(project_location + 'semver-python-phase/resources/plots/violin_' + violation + '.pdf')
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
    sns.histplot(x=bc_list, bins=35, binrange=[0, 35])
    plt.ylabel("Number of artifacts")
    plt.xlabel("Percentage of methods with " + to_string(violation))
    # plt.yscale('log')
    plt.savefig(
        project_location + 'semver-python-phase/resources/plots/histogram_' + violation + '.pdf')
    plt.show()
    return bc_list


def calculate_popularity(pop_metric):
    pop_dict = read_popularity(pop_metric)

    bc_callables_ids = list()
    bc_popularity_metrics = list()
    all_popularity_metrics = list()
    callable_ids = set()
    with open(project_location + 'semver-python-phase/resources/callables.txt') as callable_file:
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

    sns.kdeplot(non_zero_bc, label="Methods involved in a breaking change", cut=0)
    sns.kdeplot(non_zero_no_bc, label="Methods not involved in a breaking change", cut=0)
    plt.xlabel("Percentage of dependents that call method")

    plt.legend()
    plt.savefig(
        project_location + 'semver-python-phase/resources/plots/kdeplot_' + pop_metric + '.pdf')
    plt.show()

    f, ax = plt.subplots(2, figsize=(8, 6))

    ax[0].set_xlim(-0.17, 1.18)
    ax[1].set_xlim(-0.17, 1.18)

    sns.violinplot(x=non_zero_no_bc, ax=ax[0], cut=0)
    sns.violinplot(x=non_zero_bc, ax=ax[1], cut=0)

    ax[0].set_title("All methods")
    ax[1].set_title("Methods involved in a breaking change")

    plt.subplots_adjust(hspace=0.4)
    plt.savefig(
        project_location + 'semver-python-phase/resources/plots/violin_popularity_' + pop_metric + '.pdf')
    plt.show()

    print(stats.ttest_ind(non_zero_no_bc, non_zero_bc, alternative='greater'))
    print(stats.ttest_ind(non_zero_no_bc, non_zero_bc, alternative='less'))
    print(stats.ttest_ind(non_zero_no_bc, non_zero_bc, alternative='two-sided'))


def average_breaking_changes(versions):
    average_bc_dict = defaultdict(int)
    number_of_major_versions = defaultdict(int)
    total_methods = defaultdict(int)

    for bc in versions:
        key = str(bc.groupId + ':' + bc.artifactId)
        average_bc_dict[key] += bc.violations / bc.numberOfVersions
        total_methods[key] += bc.numberMethods
        number_of_major_versions[key] += 1

    filtered_bc = dict(filter(lambda x: x[1] > 0, average_bc_dict.items()))
    output = defaultdict(float)
    for key in filtered_bc.keys():
        output[key] = average_bc_dict[key] / (total_methods[key] / number_of_major_versions[key])

    sum = 0
    for value in output.values():
        sum += value
    return sum / len(output) * 100


def quintile_dep_percentage():
    popularities = read_popularity("public-dependent-percentage")

    xs = np.arange(0, 5 + 1 / len(popularities), 5 / (len(popularities) - 1))
    i = [float(x) for x in popularities.values()]
    sns.regplot(x=xs, y=i)
    plt.savefig(project_location + 'semver-python-phase/resources/plots/quintile-dep-percentage.pdf')


class Duplicate:
    class_name = None
    module_name = None
    method_name = None
    return_type = None
    parameters = None
    category = None

    def __eq__(self, other):
        if self.category == "module":
            return self.class_name == other.class_name and self.method_name == other.method_name and self.parameters == other.parameters and self.return_type == other.return_type
        if self.category == "class":
            return self.module_name == other.module_name and self.method_name == other.method_name and self.parameters == other.parameters and self.return_type == other.return_type
        if self.category == "method":
            return self.module_name == other.module_name and self.class_name == other.class_name  and self.parameters == other.parameters and self.return_type == other.return_type
        if self.category == "params":
            return self.module_name == other.module_name and self.class_name == other.class_name and self.method_name == other.method_name and self.return_type == other.return_type
        if self.category == "return":
            return self.module_name == other.module_name and self.class_name == other.class_name and self.method_name == other.method_name and self.parameters == other.parameters
        else:
            raise Exception("No duplication category specified!")

    def __init__(self, complete_label, category):
        split_slash = complete_label.split("/")
        self.module_name = split_slash[0]
        split_dot = split_slash[1].split(".")
        self.class_name = split_dot[0]
        self.method_name = ''.join(split_dot[1::]).split("(")[0]
        return_and_parameters = ''.join(split_dot[1::]).split("(")[1].split(")")
        self.return_type = return_and_parameters[0]
        self.parameters = return_and_parameters[1]
        self.category = category

    def __hash__(self):
        if self.category == "module":
            return hash(self.class_name + self.method_name + self.parameters + self.return_type)
        if self.category == "class":
            return hash(self.module_name + self.method_name + self.parameters + self.return_type)
        if self.category == "method":
            return hash(self.module_name + self.class_name + self.parameters + self.return_type)
        if self.category == "params":
            return hash(self.module_name + self.class_name + self.method_name + self.return_type)
        if self.category == "return":
            return hash(self.module_name + self.class_name + self.method_name + self.parameters)
        else:
            raise Exception("No duplication category specified!")


def calculate_duplicate_names(breaking_changes, api_extensions_list):
    """
    This method calculated all duplicated names. A duplicated name is:
        A version has removed the method m(), but added m(int). This version is then attributed a
        breaking change for removing m(), and an illegal API extension for adding m(int). The following
        method outputs how often a method signature is altered by changing the return type or changing
        the arguments.
    """
    countOverlapOfBCAndAPIEX(breaking_changes, api_extensions_list)

    api_extensions_without_duplicates = set()

    categories = ['module', 'class', 'method', 'params', 'return']
    for category in categories:
        acc = 0
        total_removed = 0
        for (artifact_bc, artifact_api) in zip(breaking_changes, api_extensions_list):
            assert hash(artifact_bc) == hash(artifact_api)
            api_version_dict = dict()
            bc_version_dict = dict()

            # For each callable involved in bc:
            for i in range(0, len(artifact_bc.callables)):
                version, name = artifact_bc.get_name(i)
                possible_duplicate = Duplicate(name, category)
                if version not in bc_version_dict:
                    bc_version_dict[version] = set()
                bc_version_dict[version].add(possible_duplicate)

            # For each callable involved in apix:
            for i in range(0, len(artifact_api.callables)):
                version, name = artifact_api.get_name(i)
                possible_duplicate = Duplicate(name, category)
                if version not in api_version_dict:
                    api_version_dict[version] = set()
                api_version_dict[version].add(possible_duplicate)

            to_remove_from_aix = set()
            # Finally for each version see if there is an overlap in the breaking change names
            # and the api extension names:
            for version in bc_version_dict.keys():
                if version in api_version_dict:
                    intersection = bc_version_dict[version].intersection(api_version_dict[version])
                    to_remove_from_aix = to_remove_from_aix.union(intersection)
                    # acc += len(intersection)

            acc += len(to_remove_from_aix)

            # Remove duplicated names from AIX
            callables_without_duplicates = list()
            for i in range(0, len(artifact_api.callables)):
                version, name = artifact_api.get_name(i)
                searching_for_duplicate = Duplicate(name, category)
                if searching_for_duplicate not in to_remove_from_aix:
                    callables_without_duplicates.append(artifact_api.callables[i])
                else:
                    total_removed += 1

            artifact_to_add = artifact_api
            artifact_to_add.callables = callables_without_duplicates
            artifact_to_add.violations = len(callables_without_duplicates)

            api_extensions_without_duplicates.add(artifact_to_add)
        print("%s methods are in category %s" % (total_removed, category))
        print("%s unique methods are removed" % acc)

    return api_extensions_without_duplicates


def countOverlapOfBCAndAPIEX(breaking_changes, api_extensions_list):
    number_of_names = 0
    for (artifact_bc, artifact_api) in zip(breaking_changes, api_extensions_list):
        callable_set_package = set()
        for i in range(0, len(artifact_bc.callables)):
            version, name = artifact_bc.get_name(i)
            callable_set_package.add(name)
        for i in range(0, len(artifact_api.callables)):
            version, name = artifact_api.get_name(i)
            callable_set_package.add(name)
        number_of_names += len(callable_set_package)
    print("Total number of unique names involved in bc or apix:", number_of_names)


def difference_between_majors():
    major_dict = dict()

    for major in breaking_changes:

        key = major.groupId + "|" + major.artifactId
        if key not in major_dict:
            major_dict[key] = list()
        major_dict[key].append(major.violations)

    for key in major_dict.keys():
        if 0 in major_dict[key] and len(list(filter(lambda x: x > 0, major_dict[key]))) > 0:
            print(key)


def calculate_percentage(versions):
    incremented = [1 for x in versions if x.violations > 0]
    return len(incremented), sum(incremented) / len(versions) * 100


def calculate_percentage_or(versions_one, versions_two):
    incremented_one = [(x.groupId + ":" + x.artifactId) for x in versions_one if x.violations > 0]
    incremented_two = [(x.groupId + ":" + x.artifactId) for x in versions_two if x.violations > 0]
    unio = set(incremented_one).union(set(incremented_two))
    return len(unio), len(unio) / len(versions_one) * 100


def versions_with_modules_bc(versions):
    artifacts = [(x.groupId + ":" + x.artifactId) for x in versions]
    path = Path(project_location + 'semver-python-phase/resources/mvn.expanded_coords.txt')
    i = 0
    with open(path, 'r') as file:
        for version in file:
            split = version.split(":")
            formatted_version = split[0] + ":" + split[1]
            if formatted_version in artifacts:
                if len(split[2][:-1].split(".")) > 2 and split[2][:-1].split(".")[1] == '0' and \
                        split[2][:-1].split(".")[2] == '0':
                    continue
                i += 1
    return i


def versions_with_modules_ax(versions):
    artifacts = [(x.groupId + ":" + x.artifactId) for x in versions]
    path = Path(project_location + 'semver-python-phase/resources/mvn.expanded_coords.txt')
    i = 0
    with open(path, 'r') as file:
        for version in file:
            split = version.split(":")
            formatted_version = split[0] + ":" + split[1]
            if formatted_version in artifacts:
                if len(split[2][:-1].split(".")) > 2 and split[2][:-1].split(".")[2] == '0':
                    continue
                i += 1
    return i


def versions_with_violations(versions):
    version_dict = dict()
    for version in versions:
        groupId = version.groupId
        artifactId = version.artifactId

        for callable in version.callables:
            version_number = callable.split("/")[1]

            hashed_version = groupId + ":" + artifactId + ":" + version_number
            if hashed_version not in version_dict:
                version_dict[hashed_version] = 1

    return len(version_dict)


def artifacts_with_more_than_1_percent_violations(versions):
    version_set = set()
    for version in versions:
        groupId = version.groupId
        artifactId = version.artifactId

        if version.violations > (version.numberMethods / 100):
            version_set.add(groupId + ":" + artifactId)
    return len(version_set), len(version_set) / len(versions) * 100


def intersect(removed, added):
    removals = set()
    additions = set()
    for version in removed:
        if version.violations != 0:
            removals.add(version.groupId + version.artifactId)

    for version in added:
        if version.violations != 0:
            additions.add(version.groupId + version.artifactId)
    print(len(removals))
    print(len(additions))
    print(len(removals.union(additions)))


def add_missing_artifacts(bc_list, aix_list):
    artifacts = read_artifacts_txt()

    for artifact in artifacts:
        found = False
        for inner_artifact in bc_list:
            inner_artifact_name = inner_artifact.groupId + "|" + inner_artifact.artifactId
            if inner_artifact_name == artifact:
                found = True
        if not found:
            artifact_to_add = Artifact(artifact.split("|")[0], artifact.split("|")[1], 0, 1, list())
            bc_list.append(artifact_to_add)
            aix_list.append(artifact_to_add)

    return bc_list, aix_list


if __name__ == '__main__':
    try:
        os.makedirs(project_location + 'semver-python-phase/resources/plots')
    except OSError:
        pass

    # OLD:
    breaking_changes_missing = compress_major_to_package(read_file('breaking_changes'))
    api_extensions_missing = compress_major_to_package(read_file('api_extensions'))

    breaking_changes, all_api_extensions = add_missing_artifacts(breaking_changes_missing, api_extensions_missing)

    api_extensions = calculate_duplicate_names(breaking_changes, all_api_extensions)

    print("Numbers:")
    # print("Number of artifacts:", len(artifacts))
    print("Percentage of artifacts with BC or AX %s(%s percent)" %(calculate_percentage_or(breaking_changes, api_extensions)))
    print("Number of artifacts with at least one BC %s(%s percent)" %(calculate_percentage(breaking_changes)))
    print("Number of artifacts with at least one AX %s(%s percent)" %(calculate_percentage(api_extensions)))

    # TODO check with Simcha
    print("percentage of minor and patch releases containing bc:",
          versions_with_violations(breaking_changes) / versions_with_modules_bc(breaking_changes) * 100)

    # print("percentage of releases released through ax:",
    #       versions_with_violations(api_extensions) / versions_with_modules_ax(api_extensions) * 100)
    # print("Artifacts with more than 1% BC %s(%s percent)", artifacts_with_more_than_1_percent_violations(breaking_changes))
    # print("Artifacts with more than 1% ac %s(%s percent)", artifacts_with_more_than_1_percent_violations(api_extensions))

    for violation in 'breaking_changes', 'api_extensions':
        print(violation + ":")
        bc_list = histogram(violation)
        non_zero = [x for x in bc_list if x != 0]
        count = 0
        for num in non_zero:
            if num < 1:
                count += 1
        print("Number of artifacts with violated methods less than 1 percent:", count)
        count = 0
        for num in non_zero:
            if num >= 50:
                count += 1
        print("Number of artifacts with violated methods more than equal 50 percent:", count)

        count = 0
        for num in non_zero:
            if num < 15:
                count += 1
        print("Number of artifacts with violated methods less than 15 percent:", count)

        average = sum(non_zero) / len(non_zero)
        print("average number of methods involved in violation in artifacts that at least have one : ", average)

        trendline(violation)

    for metric in 'dependent-percentage', 'eigenvector', 'degree':
        calculate_popularity(metric)

    quintile_dep_percentage()


