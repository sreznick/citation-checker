from wiki_ru_wordnet import WikiWordnet


class SynonymSet:
    def __init__(self, w, wordnet, eps):
        self._wiki_ru_wordnet = wordnet
        self._word = w
        self._synset = {w: 1}
        self._eps = eps

        # here we make a set of synonyms and hypernyms for a particular word
        coef = 1
        for i, synset in enumerate(wordnet.get_synsets(w), start=1):
            # print(i, [w.lemma() for w in synset.get_words()])
            coef *= eps
            for w in synset.get_words():
                w = w.lemma()
                if w not in self._synset.keys():
                    self._synset[w] = coef * eps ** (len(w.split(" ")) - 1)
            for hyp in wordnet.get_hypernyms(synset):
                for w in hyp.get_words():
                    w = w.lemma()
                    if w not in self._synset.keys():
                        self._synset[w] = coef ** 2 * eps ** (len(w.split(" ")) - 1)
                # print("    ", [w.lemma() for w in hyp.get_words() if w.lemma() not in self._synset])
        if w == 'я':
            self._synset['мну'] = 0
        #print(self._synset)

    def get_items(self):
        return self._synset.items()

    def score(self):
        return self.score()


if __name__ == '__main__':
    wikiwordnet = WikiWordnet()
    line = "рожденный в СССР"
    for word in line.split():
        # word_s = hun.stem(word)[0].decode("utf-8")
        st = SynonymSet(word, wikiwordnet, 0.5)
