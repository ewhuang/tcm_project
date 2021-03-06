### Author: Edward Huang

from collections import OrderedDict
import matplotlib
import math
import numpy as np
import scipy.cluster.hierarchy as hier
from scipy.spatial.distance import pdist, squareform
import time

### Performs the baseline for the herb symptom dictionary to build an herb
### ontology. The dictionary file is directly from the e-mail.
### Run time: 14 seconds.

matplotlib.use('Agg')
import pylab

def calc_row_idx(k, n):
    return int(math.ceil((1/2.) * (- (-8*k + 4 *n**2 -4*n - 7)**0.5 + 2*n -1) - 1))

def elem_in_i_rows(i, n):
    return i * (n - 1 - i) + (i*(i + 1))/2

def calc_col_idx(k, i, n):
    return int(n - elem_in_i_rows(i + 1, n) + k)

def condensed_to_square(k, n):
    i = calc_row_idx(k, n)
    j = calc_col_idx(k, i, n)
    return i, j

def import_dictionary_file():
    '''
    Returns the dictionary produced by the file.
    Keys: herbs
    Values: lists of symptoms
    Also returns the list of all symptoms as a feature vector.
    '''
    # Feature vector is the set of all symptoms.
    symptom_features = set([])
    # Keys are herbs, and values are the symptoms that the herbs treat.
    herb_dct = {}
    f = open('./data/herb_symptom_dictionary.txt', 'r')
    for i, line in enumerate(f):
        if i == 0:
            continue
        line = line.strip().split('\t')

        line_length = len(line)
        # Some symptoms don't have good English translations.
        assert line_length == 2 or line_length == 5
        if line_length == 2:
            herb, symptom = line
        elif line_length == 5:
            herb, symptom, english_symptom, db_src, db_src_id = line

        # Add to the herb dictionary.
        if herb in herb_dct:
            herb_dct[herb] += [symptom]
        else:
            herb_dct[herb] = [symptom]

        # Add to the feature vector.
        symptom_features.add(symptom)

    f.close()

    return list(symptom_features), herb_dct


def main():
    symptom_features, herb_dct = import_dictionary_file()

    # For each herb, construct the feature vector for the herb.
    herb_feature_vectors = OrderedDict({})
    for herb in herb_dct:
        treated_symptoms = herb_dct[herb]

        current_feature_vector = []
        # Loop through all of the possible symptoms, adding to the feature vec.
        for symptom in symptom_features:
            current_feature_vector += [treated_symptoms.count(symptom)]
        assert len(current_feature_vector) == len(symptom_features)

        assert herb not in herb_feature_vectors
        herb_feature_vectors[herb] = np.array(current_feature_vector)

    # Now, perform the hierarchical clustering.
    feature_matrix = herb_feature_vectors.values()
    distance_matrix = pdist(feature_matrix, 'cosine')

    # Get top 100 most similar pairs of herbs.
    herb_indices = distance_matrix.argsort()
    n = len(feature_matrix)
    herbs = herb_feature_vectors.keys()

    out = open('./results/most_similar_herbs.txt', 'w')
    out.write('herb_1\therb_2\tshared_symptoms\tdistance\n')
    line_counter = 0
    for condensed_index in herb_indices:
        print distance_matrix[condensed_index]
        if distance_matrix[condensed_index] == 0:
            continue

        i, j = condensed_to_square(condensed_index, n)
        herb_i = herbs[i]
        herb_j = herbs[j]
        out.write('%s\t%s\t' % (herb_i, herb_j))

        herb_i_symptoms = herb_feature_vectors[herb_i]
        herb_j_symptoms = herb_feature_vectors[herb_j]
        shared_symptom_indices = np.nonzero(herb_i_symptoms & herb_j_symptoms)[0]
        for index in shared_symptom_indices:
            out.write('%s,' % symptom_features[index])
        out.write('\t%g\n' % distance_matrix[condensed_index])

        # Break when we write 100 lines.
        line_counter += 1
        if line_counter == 100:
            break
    out.close()

    # Clustering with dendrogram.
    clusters = hier.linkage(distance_matrix, method='single')

    cluster_dct = {}
    for herb, cluster_index in enumerate(hier.fcluster(clusters, t = 1)):
        if cluster_index in cluster_dct:
            cluster_dct[cluster_index] += [herb]
        else:
            cluster_dct[cluster_index] = [herb]
    out = open('./results/dendrogram_clusters.txt', 'w')
    for cluster_index in cluster_dct:
        cluster = cluster_dct[cluster_index]
        if len(cluster) < 5:
            continue
        for node in cluster:
            out.write(herbs[node] + '\t')
        out.write('\n')
    out.close()

    # Plotting the dendrogram.
    R = hier.dendrogram(
        clusters,
        leaf_rotation=90.,  # rotates the x axis labels
        leaf_font_size=0.25,  # font size for the x axis labels
        )
    
    out = open('./results/baseline_dendrogram_herbs.txt', 'w')
    for leaf in R['leaves']:
        out.write(herbs[leaf] + '\t' + str(leaf) + '\n')
    out.close()
    pylab.savefig('./results/baseline_dendrogram.pdf')

if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))