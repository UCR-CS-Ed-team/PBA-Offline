"""Utility functions to use in anomaly detection processing"""
# Get current and next item from an interable.  Code from https://stackoverflow.com/questions/5434891/iterate-a-list-as-pair-current-next-in-python
def pairwise(iterable):
    it = iter(iterable)
    a = next(it, None)
    for b in it:
        yield (a, b)
        a = b

