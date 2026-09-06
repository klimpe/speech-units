import eval

class DamCopy(object):
    """
    Represents a single damaged variant
    of an original segmentation tier.

    Contains a damaged tier and information about damaging parameters:
    -  damaging method which was used to generate it
    -  magitude of damaging
    """

    def __init__(self, segmentation, method, n, true_n=None):
        """
        tier : annotationdata.tier.Tier
          damaged segmentation
        method : str
          damaging method name
          such as 'add', 'remove', 'shiftA1'
        n : int
          amount of damaging (magnitude)
        """
        self.segmentation = segmentation  # damaged segmentation Tier
        self.method = method
        self.n = n
        self.true_n = true_n

        self.boundaries_inserted = 0
        self.boundaries_removed = 0
        self.boundaries_shifted = 0

        self.items = None # NLTK-style list of 3-element tuples
        self.binary = None
        self.binary_step = None
        self.eval_result = {'kappa': None,
                            'windowdiff_time': None,
                            'windowdiff_unit': None,
                            'boundary_similarity_time': None,
                            'boundary_similarity_unit': None,
                            'precision_start': None,
                            'precision_end': None,
                            'precision_unit': None,
                            'recall_start': None,
                            'recall_end': None,
                            'recall_unit': None,
                            'f_start': None,
                            'f_end': None,
                            'f_unit': None
                            }
        self.segmentation.SetName('DC{}={}'.format(method, n))

    def __str__(self):
        s = 'DamCopy "{}" , n={}'.format(self.method, self.n)
        return s

    def __len__(self):
        return len(self.segmentation)

    def gen_items(self, reference, coder_label=1):
        """
        Converts to nltk format, i.e.
        list of tuples of form (annotator, item:int, label:int{0,1})
        which is stored in .items

        :param reference: annotationdata.tier.Tier
        :param original: annotationdata.tier.Tier
        :param coder_label: str or int
        :return: None
        """
        self.items = eval.convert_to_nltk_format(
            reference, self.segmentation, coder_label)

    def gen_binary(self, step):
        if self.binary:
            if self.binary_step == step:
                return
        self.binary = tierwd.tier_to_binary(self.segmentation, step)
        self.binary_step = step
