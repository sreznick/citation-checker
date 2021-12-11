import argparse
from features import get_features
import pandas as pd
import pickle


parser = argparse.ArgumentParser()
parser.add_argument('--infile', type=str, help='Input filename (file must contain links to pages for prediction')
parser.add_argument('--outfile', type=str, default='', help='Output .csv filename')
parser.add_argument('--model', type=str, default='model.pkl', help='.pkl file with pretrained classification model')
args = parser.parse_args()

if args.outfile == '':
    args.outfile = args.infile[:-4] + '.csv'

with open(args.infile, 'r') as f:
    links = f.read().split('\n')

X = []
good_links = []
bad_links = []
for link in links:
    features = get_features(link)
    if features is not None:
        X.append(features)
        good_links.append(link)
    else:
        bad_links.append(link)

with open(args.model, 'rb') as file:
    rf = pickle.load(file)

predictions = rf.predict_proba(X)[:, 1]
result = pd.DataFrame({'link': good_links + bad_links, 'prediction': list(predictions) + [None] * len(bad_links)})
result.to_csv(args.outfile, index=False)
