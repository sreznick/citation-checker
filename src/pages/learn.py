import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--df', type=str, default='texts.csv', help='Input .csv dataframe for learning')
parser.add_argument('--model', type=str, default='model.pkl', help='Output, .pkl file for pretrained classification '
                                                                   'model')
args = parser.parse_args()

df = pd.read_csv(args.df)
X = df.drop('is_text', axis=1).values
y = df['is_text'].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=0)

clf = RandomForestClassifier(max_depth=4, random_state=0)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)
print(accuracy_score(y_test, y_pred))

pkl_filename = args.model
with open(pkl_filename, 'wb') as file:
    pickle.dump(clf, file)
