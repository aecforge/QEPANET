import numpy
import scipy


xs = [1, 2, 3]
ys = [10, 4, 1]

print numpy.polyfit(xs, ys, 2, full=True)


print scipy.polyfit(xs, ys, 2, full=True)
print scipy.stats