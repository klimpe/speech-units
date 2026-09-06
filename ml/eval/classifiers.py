from sklearn.preprocessing import PolynomialFeatures
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


log_lin = [
    # ('Log c=1', LogisticRegression(C=1)),
    # ('Log c=10', LogisticRegression(C=10)),
    ('Log c=1000', LogisticRegression(C=1000))
    # ('Log c=1 weighted', LogisticRegression(C=1, class_weight='auto')),
    # ('Log c=10 weighted', LogisticRegression(C=10, class_weight='auto')),
    # ('Log c=1000 weighted', LogisticRegression(C=1000, class_weight='auto'))
]

log_poly = [
    ('Log poly1 C=1000', Pipeline([('poly1', PolynomialFeatures(degree=1)),
                                   ('logistic', LogisticRegression(C=1000))])),
    ('Log poly2 C=1000', Pipeline([('poly2', PolynomialFeatures(degree=2)),
                                   ('logistic', LogisticRegression(C=1000))])),

    ('Log poly-int C=1000', Pipeline([('poly-int', PolynomialFeatures(interaction_only=True)),
                                      ('logistic', LogisticRegression(C=1000))]))
    # ('Log poly-int', Pipeline([('poly-int', PolynomialFeatures(interaction_only=True)),
    #                                     ('logistic', LogisticRegression(class_weight=None))]))
]

dtree = [
    ('DecisionTree depth=3', DecisionTreeClassifier(max_depth=3, min_samples_leaf=100)),
    ('DecisionTree depth=4', DecisionTreeClassifier(max_depth=4, min_samples_leaf=100)),
    ('DecisionTree depth=5', DecisionTreeClassifier(max_depth=5, min_samples_leaf=100)),
    ('DecisionTree depth=7', DecisionTreeClassifier(max_depth=7, min_samples_leaf=100)),
    ('DecisionTree depth=10', DecisionTreeClassifier(max_depth=10, min_samples_leaf=100))
]


def list_classifiers(which):
    '''
    === In ===
    which : list
      List of strings identifying classifier groups.
      Available: log_lin, log_poly, dtree
    === Out ===
    List of tuples (classifier, description)
    '''
    clflist = []
    if 'log_lin' in which:
        clflist += log_lin
    if 'log_poly' in which:
        clflist += log_poly
    if 'dtree' in which:
        clflist += dtree
    return clflist