# Basic AI App Evaluation

## What Evaluation Means in AI

Testing a sorting function is simple: feed in a list, check the output. LLM outputs are different — the model might give you a correct answer phrased three different ways. Evaluation means deciding in advance what "correct" looks like, writing test cases that check for it, and measuring how often your app passes.

The smallest possible evaluator is a function that takes a predicted value and an expected value and returns True or False.

```python run
def exact_match(predicted, expected):
    return predicted == expected

print(exact_match('Paris', 'Paris'))   # True
print(exact_match('paris', 'Paris'))   # False — case matters
print(exact_match('', ''))             # True — empty strings match
```

A real evaluation pipeline runs this function over a whole test set — a list of (input, expected) pairs you prepare ahead of time. The test set is what makes evaluation repeatable: run it today, run it after changing your prompt, compare the scores.

```python run
cases = [
    ('Paris', 'Paris'),
    ('London', 'London'),
    ('X', 'Tokyo'),
]
results = [p == e for p, e in cases]
print(results)        # [True, True, False]
print(sum(results))   # 2 passed
```

## Exact Match and Contains Checks

Exact match is strict — every character must be identical. That is useful for structured outputs like labels, IDs, and JSON fields, but too strict for prose answers where the model might phrase things differently.

A contains check asks: does the output include these key phrases? It is more forgiving and still catches obvious failures.

```python run
def exact_match(predicted, expected):
    return predicted == expected

def contains_check(predicted, keywords):
    return all(kw.lower() in predicted.lower() for kw in keywords)

# Exact match fails on paraphrased answers
print(exact_match('The capital of France is Paris', 'Paris'))  # False

# Contains check passes as long as key words appear
print(contains_check('The capital of France is Paris', ['Paris', 'capital']))  # True
print(contains_check('Berlin is the capital of Germany', ['Paris']))           # False
```

For classification tasks (sentiment, topic, intent), exact match is usually the right choice because the output should be one of a fixed set of labels. For open-ended answers, a contains check catches whether the key facts appear, even if the phrasing varies.

```python run
def classify_eval(predicted, valid_labels):
    return predicted.strip().lower() in [lb.lower() for lb in valid_labels]

print(classify_eval('Positive', ['positive', 'negative', 'neutral']))  # True
print(classify_eval('somewhat positive', ['positive', 'negative']))     # False
```

## Normalizing Before Comparing

The most common source of false negatives in eval is whitespace and case. The model returns `"Paris\n"` and your expected value is `"Paris"` — they are not equal, but the comparison fails for a trivial reason that tells you nothing about quality.

Normalizing before comparing means stripping outer whitespace and lowercasing before the check.

```python run
def normalize(text):
    return text.strip().lower()

raw_prediction = '  Paris\n'
expected = 'Paris'

print(raw_prediction == expected)                        # False — false negative
print(normalize(raw_prediction) == normalize(expected))  # True — correct
```

Apply normalization in your evaluator, not in the data. That way the original output is preserved for logging and debugging while comparisons still work.

```python run
def normalized_exact(predicted, expected):
    return predicted.strip().lower() == expected.strip().lower()

cases = [('paris\n', 'Paris'), ('  BERLIN', 'Berlin'), ('Tokyo', 'Tokyo')]
results = [normalized_exact(p, e) for p, e in cases]
print(results)  # [True, True, True]
```

## Scoring a Test Set

A single pass/fail tells you one data point. A score tells you how your app performs across your whole test set. The standard metric is pass rate: passed cases divided by total cases.

```python run
def score_batch(predictions, labels, evaluator_fn):
    if not labels:
        return 0.0
    passed = sum(1 for p, e in zip(predictions, labels) if evaluator_fn(p, e))
    return passed / len(labels)

exact = lambda p, e: p.strip().lower() == e.strip().lower()
preds    = ['paris', 'Berlin', 'tokyo', 'london']
expected = ['Paris', 'Berlin', 'Tokyo', 'London']

print(score_batch(preds, expected, exact))  # 1.0

preds_with_errors = ['paris', 'rome', 'tokyo', 'london']
print(score_batch(preds_with_errors, expected, exact))  # 0.75
```

Run this score after every prompt change. If the score drops, your change made things worse. If it rises, you improved the app. This is how you turn prompt engineering from guesswork into a feedback loop.

```python run
def compare_scores(score_before, score_after, label=''):
    delta = score_after - score_before
    direction = 'improved' if delta > 0 else 'regressed' if delta < 0 else 'unchanged'
    return {'label': label, 'before': score_before, 'after': score_after,
            'delta': round(delta, 3), 'result': direction}

print(compare_scores(0.75, 0.90, label='v2 prompt'))
```

## Multi-Metric Evaluation

No single metric tells the whole story. A response can pass a contains check but be too long, or pass exact match but be grammatically wrong. Multi-metric evaluation combines several checks into a single result dictionary.

```python run
def multi_metric(predicted, expected, keywords=None):
    norm = lambda s: s.strip().lower()
    exact = norm(predicted) == norm(expected)
    contains = all(kw.lower() in predicted.lower() for kw in (keywords or []))
    length_ok = 5 <= len(predicted.split()) <= 100
    return {'exact': exact, 'contains': contains, 'length_ok': length_ok}

print(multi_metric('Paris', 'Paris', ['Paris']))
# {'exact': True, 'contains': True, 'length_ok': False} — too short

print(multi_metric('The capital of France is Paris today', 'Paris', ['Paris', 'France']))
# {'exact': False, 'contains': True, 'length_ok': True}
```

Each metric catches a different kind of failure. Exact match fails when the model paraphrases. Contains fails when it omits key facts. Length fails when it rambles or truncates. Combining them gives you a richer picture of where the model is going wrong.

```python run
def aggregate_metrics(results_list):
    if not results_list:
        return {}
    keys = results_list[0].keys()
    return {k: sum(r[k] for r in results_list) / len(results_list) for k in keys}

results = [
    {'exact': True,  'contains': True,  'length_ok': False},
    {'exact': False, 'contains': True,  'length_ok': True},
    {'exact': True,  'contains': True,  'length_ok': True},
]
print(aggregate_metrics(results))
```

## Writing a Repeatable Eval Harness

A harness is a small class that holds your test cases, runs the evaluator over them, and reports the results. The goal is to make evaluation a one-liner so you actually run it.

```python run
class EvalHarness:
    def __init__(self):
        self.cases = []
        self.results = []

    def add_case(self, predicted, expected):
        self.cases.append((predicted, expected))
        return self

    def run(self, evaluator_fn):
        self.results = [evaluator_fn(p, e) for p, e in self.cases]
        return self

    def score(self):
        if not self.results:
            return 0.0
        return sum(self.results) / len(self.results)

    def report(self):
        return {'cases': len(self.cases), 'passed': sum(self.results), 'score': self.score()}

harness = EvalHarness()
harness.add_case('paris', 'Paris')
harness.add_case('Berlin', 'Berlin')
harness.add_case('rome', 'Tokyo')

exact = lambda p, e: p.strip().lower() == e.strip().lower()
harness.run(exact)
print(harness.report())
```

The harness pattern scales naturally: add more cases, swap in a different evaluator, compare scores before and after a change. This is the core of every production eval pipeline — the same idea, just with more metrics and a database instead of a list.

```python run
class EvalHarness:
    def __init__(self):
        self.cases = []
        self.results = []

    def add_case(self, predicted, expected):
        self.cases.append((predicted, expected))
        return self

    def run(self, evaluator_fn):
        self.results = [evaluator_fn(p, e) for p, e in self.cases]
        return self

    def score(self):
        if not self.results:
            return 0.0
        return sum(self.results) / len(self.results)

harness = EvalHarness()
for pred, exp in [('a', 'a'), ('b', 'b'), ('c', 'x'), ('d', 'd')]:
    harness.add_case(pred, exp)
harness.run(lambda p, e: p == e)
print(f'Score: {harness.score():.0%}')  # Score: 75%
```
