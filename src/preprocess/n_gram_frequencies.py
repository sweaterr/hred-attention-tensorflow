
from collections import defaultdict
import argparse
import pickle
import os
import operator
import sys

"""
Make n-gram freq
"""
BG_FILE_PATH = './data/full_data/bg_session.ctx'
DIST_OUTPUT_FOLDER = './data/output/ngram_dist'
MAX_N = 3

OUTPUT_FILE = './data/output/output.out'

SAVE_DIST = True
MAKE_DIST = True

CUTOF_POINTS = "200,300,1000000000"


def make_ngram_distributions(background_session_file, max_n, output_folder, save_dicts=True):
        n_gram_dist_list = []
        for n in range(1, max_n+1):
            dist = make_ngram_distribution(background_session_file, n)
            n_gram_dist_list.append(dist)
            if save_dicts:
                make_dir(output_folder)
                file_name = str(n) + 'gram_dist'
                file_path = os.path.join(output_folder, file_name)
                pickle.dump(dist, open(file_path + ".p", "wb"))

        file_name = 'distribution_array'
        file_path = os.path.join(output_folder, file_name)

        pickle.dump(n_gram_dist_list, open(file_path, "wb"))
        return n_gram_dist_list


def make_ngram_distribution(bg_session_file, n=3):
    frequency_dict = defaultdict()
    for session in open(bg_session_file, 'r'):
        session = session.strip('\n')
        queries = session.strip().split('\t')
        for query in queries:
            for i in range(0, len(query)-n):
                ngram = query[i:i + n]
                frequency_dict[ngram] = frequency_dict.get(ngram, 0) + 1
    return frequency_dict


def load_ngram_dist(file_path):
    return pickle.load(open(os.join(file_path, "distribution_array.p", "rb")))


def prune_dicts(n_gram_distributions, cutoff_points):

    n_gram_distributions = list(reversed(n_gram_distributions))
    dist_list = []

    for idx in range(0, len(n_gram_distributions)):
        dist = n_gram_distributions[idx]
        cuttoff = cutoff_points[idx]

        sorted_dist = sorted(dist.items(), key=operator.itemgetter(1))
        sorted_dist = list(reversed(sorted_dist))

        if len(sorted_dist) > cuttoff:

            sorted_dist = sorted_dist[:cuttoff]

        dist = {}

        for key, value in sorted_dist:
            dist[key] = value
        dist_list.append(dist)
    return dist_list


def make_dir(file_path):
    if not os.path.exists(file_path):
        os.makedirs(file_path)


def ngram_to_ids(pruned_dicts):
    lst = []
    for dict in pruned_dicts:
        _dict = {}
        for idx,key in enumerate(dict.keys()):
            _dict[key] = idx + 1
        lst.append(_dict)
    return lst


def txt_to_ngram_idx(file, idx_ngramss, FLAGS, outfile):
    with open(outfile, 'w') as f_out:
        for session in open(file, 'r'):
            session_list = []
            session = session.strip('\n')
            queries = session.strip().split('\t')
            idx_ngramss = idx_ngramss[::-1]
            for query in queries:
                idx = 0
                query_list = []
                while idx <= len(query):
                    for n in range(FLAGS.max_n, 0, -1):
                        found_ngram = False
                        n_gram = query[idx:idx+(n)]
                        _dict = idx_ngramss[n - 1]
                        if n_gram in _dict:
                            _id = _dict[n_gram]
                            query_list.append(str(_id))
                            found_ngram = True
                            idx += n
                            break
                    if not found_ngram:
                        query_list.append(str(0))
                        idx += FLAGS.max_n
                query = " ".join(query_list)
                session_list.append(query)
            session = "\t".join(session_list) + "\n"
            f_out.write(session)


def store_dist(n_gram_ids, dist_output_dir):
    output_dir = '/full_dist'
    make_dir(dist_output_dir + output_dir)

    pickle.dump(n_gram_ids, open(output_dir + '/full-ngram_dist.p', "wb"))




def main(FLAGS):
    """
    :param make_dist:
    :return:
    """


    if FLAGS.make_dist:
        print ('start making dict')
        n_gram_distributions = make_ngram_distributions(FLAGS.bg_file_path, FLAGS.max_n, FLAGS.dist_output_dir, FLAGS.save_dist)
        pruned_dicts = prune_dicts(n_gram_distributions, FLAGS.cutoff_points)
        n_gram_ids = ngram_to_ids(pruned_dicts)


        print ('translating n-grams to ids')
        print ('starting with tr sessions')

        txt_to_ngram_idx('./data/full_data/tr_sessions.ctx', n_gram_ids, FLAGS, './data/output/tr_session.out')

        print ('starting with val sessions')
        txt_to_ngram_idx('./data/full_data/val_sessions.ctx', n_gram_ids, FLAGS, './data/output/val_session.out')

        print ('done!')

if __name__ == '__main__':
    """
        Parse the flags, all FLAGS has default parameters
    """

    parser = argparse.ArgumentParser()

    parser.add_argument('--make_dist', type=bool, default=MAKE_DIST,
                        help='Make a distribution of the ngrams in the background data set')

    parser.add_argument('--bg_file_path', type=str, default=BG_FILE_PATH,
                        help='File path of the background datas et')

    parser.add_argument('--max_n', type=str, default=MAX_N,
                        help='All the n-grams we parse, starting with uni-grams up to n-grams')

    parser.add_argument('--dist_output_dir', type=str, default=DIST_OUTPUT_FOLDER,
                        help='Folder to output the dist')

    parser.add_argument('--save_dist', type=bool, default=SAVE_DIST,
                        help='Save the dists to a folder')

    parser.add_argument('--cutoff_points', type=str, default=CUTOF_POINTS,
                        help='Comma')

    parser.add_argument('--output_file', type=str, default=OUTPUT_FILE,
                        help='Comma')

    FLAGS, unparsed = parser.parse_known_args()

    """
        Cutoffpoints are the points where we cut off the distribution, and go over the next ngram distribution,
    """
    if FLAGS.cutoff_points:

        cutoff_points = FLAGS.cutoff_points.split(",")
        FLAGS.cutoff_points = [int(cutoff_point) for cutoff_point in cutoff_points]

        if not len(FLAGS.cutoff_points) == FLAGS.max_n:
            print ("not enough or to much cutoff points")
            sys.exit()

    main(FLAGS)

