import glob, os, re
from statistics import median

import matplotlib.pyplot as plt
import numpy
import pandas as pd
import seaborn as sns
from numpy import average

sns.set_theme()

NUM_BINS = 1000
OUTPUT_DIR = 'resources/only_publics'
FIGURE_DIR = 'plots'

def split(a, n):
    k, m = divmod(len(a), n)
    return [a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]


def analyse(type):
    data = [[] for _ in range(NUM_BINS)]
    for file in glob.glob(os.path.join(OUTPUT_DIR, '*', f'{type}.bin')):
        temp_data = [float(x) for x in re.findall(r',(.*)\n', open(file).read()) if x != '0.0']

        if len(temp_data) < 10:
            continue

        for i, vals in enumerate(split(temp_data, NUM_BINS)):
            data[i].extend(vals)

    df = pd.DataFrame(data).transpose()

    df.plot(kind='box', showfliers=False)
    plt.yscale('log')
    # plt.savefig(os.path.join(FIGURE_DIR, f'boxplot-{type}'))
    plt.cla()

    ys = [average(d) for d in data]
    xs = numpy.arange(0, 5 + 1 / len(ys), 5 / (len(ys) - 1))

    p = sns.regplot(x=xs, y=ys, scatter_kws={ 's': 5}, line_kws={"color": "orange"}, order=3)

    x_data = p.get_lines()[0].get_xdata()
    y_data = p.get_lines()[0].get_ydata()
    total_area = numpy.trapz(y=y_data, x=x_data)
    cutoff_point = 0.8 * total_area
    print(total_area, cutoff_point)

    epsilon = 0.01
    for i in range(1, len(y_data)):
        area_left = numpy.trapz(y=y_data[0:i], x=x_data[0:i])
        area_right = numpy.trapz(y=y_data[i:100], x=x_data[i:100])
        if (abs(area_left - area_right)) < epsilon:
            print(i)
            print(total_area)
            print('areas: ', area_left, area_right)
            print('cutoff point:', x_data[i] / 5)
            print(x_data[i])
            print(y_data[i])
            break

    # print('auc', metrics.auc(x_data, y_data))

    plt.xlabel('Quintile')
    plt.ylabel(
        'Eigenvector Centrality' if type == 'eigenvector' else 'Degree Centrality' if type == 'degree' else 'Dependent Usage Ratio')

    # plt.ylim([1e-2, 1e-1])
    # plt.yscale('log')
    plt.savefig(os.path.join(FIGURE_DIR, f'lineplot-{type}-unique.pdf'), bbox_inches="tight")
    plt.cla()


def zero_usage_details():
    temp_data = list()
    type = 'public-dependent-percentage'
    for file in glob.glob(os.path.join(OUTPUT_DIR, '*', f'{type}.bin')):
        public_methods = [float(x) for x in re.findall(r',(.*)\n', open(file).read())]
        temp_data.append(public_methods)
        if len(public_methods) > 30000:
            print()

    lens = list()
    zeros = list()
    division = list()
    for i in temp_data:
        l = len(i)
        zero = i.count(0)
        lens.append(l)
        zeros.append(zero)
        division.append(zero / l)

    fig, (ax1) = plt.subplots(nrows=1, ncols=3)
    ax1[0].violinplot(lens, showmedians=True)
    ax1[1].violinplot(zeros, showmedians=True, sharex=ax1[0])
    ax1[2].violinplot(division, showmedians=True)
    ax1[0].set_title('all')
    ax1[1].set_title('zeros')
    ax1[2].set_title('division')
    fig.show()
    plt.close()

    fig = plt.figure(figsize=(8, 5.5))
    ax1 = fig.add_subplot(1, 3, 1)
    ax2 = fig.add_subplot(1, 3, 2, sharey=ax1)
    ax3 = fig.add_subplot(1, 3, 3)
    ax1.violinplot(lens, showmedians=True)
    ax2.violinplot(zeros, showmedians=True)
    ax3.violinplot(division, showmedians=True)
    ax1.set_title('all public methods')
    ax2.set_title('unused methods')
    ax3.set_title('ratio of unsused')
    plt.setp(ax2.get_yticklabels(), visible=False)
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.setp(ax2.get_xticklabels(), visible=False)
    plt.setp(ax3.get_xticklabels(), visible=False)
    plt.savefig("used_vs_unused_methods.pdf")
    plt.close()

    print('average lens', average(lens))
    print('median lens', median(zeros))
    print('minimum lens', min(lens))
    print('maximum lens', max(lens))

    print('average zeros', average(zeros))
    print('median zeros', median(zeros))
    print('minimum zeros', min(zeros))
    print('maximum zeros', max(zeros))

    print('average division', average(division))
    print('median division', median(division))
    print('minimum division', min(division))
    print('maximum division', max(division))

    print(len([i for i in zeros if i < 10]))

# analyse('eigenvector')
# analyse('degree')
analyse('public-dependent-percentage')
# zero_usage_details()