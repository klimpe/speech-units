# from .annotationdata import Annotation, Tier, TimeInterval, Transcription, aio
import os
from matplotlib import pyplot
import dambatch
# import tierutil
import eval
# from . import GroupSegm
import util


class DamGroup(object):
    """
    Generates and evaluates and stores damaged copies
    of a segmentation.

    ---------- Methods ----------
    [1. Damage tier]
    Methods to create sets of damaged copies a tier.
    The copies are added to the group and their indices
    are stored in the dictionnary self.damaged_indices[shuffling_method
      damage(self, index, n_min, n_max, step)
      damage_add_nrange(self, index n_min, n_max, step)
      damage_remove_nrange(self, n_min, n_max, step)
      damage_move_nrange(self, n_min, n_max, step, a_max)

      damage_add(self, n)
      damage_remove(self, n)
      damage_move(self, n, a)
    """

    def __init__(self, reference, original):
        """
        reference : Tier
        original : Tier
        """
        #super(DamGroup, self).__init__(data=[reference, original],
        #                               reference_index=0)
        # self.original_index = 1

        self.reference = reference
        self.original = original
        self._original_ntlk = None  # original segm converted to nltk format
        self.data = []

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, index):
        return self.data[index]

    def __str__(self):
        s = ''
        for batch in self.data:
            s += '{} : {} copies\n'.format(batch.method, len(batch))
        return s

    @property
    def methods(self):
        """
        Lists damaging methods of the already created DamBatch objecs
        == OUT ==
        list or None
        """
        return [x.method for x in self.data]

    @property
    def metrics(self):
        metrics = set(self[0].metrics)
        for batch in self:
            metrics = metrics.intersection(batch.metrics)
        metrics = list(metrics)
        metrics.sort()
        return metrics


    # @data.setter
    # def data(self, sequence):
    #     if sequence is None:
    #         return
    #     if len(sequence) > 2:
    #         raise ValueError('Expecting 2 tiers, in order: (reference, original)')
    #     data = []
    #     for tier in sequence:
    #         if not isinstance(tier, Tier):
    #             raise TypeError('Expecting a sequence of Tiers')
    #         data.append(copy.deepcopy(tier))
    #     self._data = data
    #     self._create_dict()

    # @property
    # def original(self):
    #     return self.data[self.original_index]



    #  ==================== Damaging ====================

    # def damage(self, n_range):
    #     """
    #     Generate tiers with every kind of error for different values of 'n'
    #     and add them to the group.
    #     'n' defines percentage of perturbed boundaries.
    #     """
    #     pass

    def generate_damaged_batch(self, method, n_range, shift_max_a=1,
                               skip='', multi_a=False, verbose=False):
        """
        Create a new batch of damaged copies inside
        this DamData object

        :param method: str
          values {'insert'|'remove'|'shift'}
        :param n_range: tuple
          format (n_min, n_max[, n_step])
        :param shift_max_a: int
        """
        if method == 'insert':
            batch = dambatch.DamBatch(self.reference, self.original, n_range)
            batch.generate_by_inserting(verbose=verbose)
            self.data.append(batch)
        elif method == 'remove':
            batch = dambatch.DamBatch(self.reference, self.original, n_range)
            batch.generate_by_removing(verbose=verbose)
            self.data.append(batch)
        elif method == 'shift':
            for a in range(1, shift_max_a + 1):
                print 'a =', a
                batch = dambatch.DamBatch(self.reference, self.original, n_range)
                batch.generate_by_shifting(a, skip=skip,
                                           multi_a=multi_a, verbose=verbose)
                self.data.append(batch)

    def get_damaged_copies(self, source_index, method):
        """
        Return set of previously created damaged copies matching the criteria.
        In:
          source_index (int)
          method (str)
        Out:
          DamagedGroup object
        """
        if not self.data:
            return None
        dgroups = [x for x in self.data
                   if x.method == method and x.source_index == source_index]

        if len(dgroups) == 0:
            return None
        if len(dgroups) > 1:
            print dgroups, '\nWARNING: More than 1 damaged batches match the criteria, returning the first'
        return dgroups[0]

    #  ==================== Evaluation ====================

    def evaluate(self):
        print 'Calculating Kappa'
        self.eval_kappa()
        print 'Calculating Boundary Similarity (time)'
        self.eval_boundary_similarity_time()
        print 'Calculating Boundary Similarity (unit)'
        self.eval_boundary_similarity_unit()
        print 'Calculating Precision, Recall & F'
        self.eval_precision_recall_f1()
        print 'Calculating WindowDiff (time)'
        self.eval_windowdiff_time()
        print 'Calculating WindowDiff (unit)'
        self.eval_windowdiff_unit()

    def convert_original_to_nltk(self):
        if self._original_ntlk:
            return
        print 'Converting original to NLTK format'
        self._original_ntlk = eval.convert_to_nltk_format(
            self.reference, self.original, 0)

    def eval_kappa(self):
        self.convert_original_to_nltk()
        for batch in self.data:
            print batch.name
            batch.eval_kappa(self._original_ntlk)

    def eval_boundary_similarity_time(self):
        for batch in self.data:
            print batch.name            
            batch.eval_boundary_similarity_time()

    def eval_boundary_similarity_unit(self):
        for batch in self.data:
            print batch.name
            batch.eval_boundary_similarity_unit()
            
    def eval_windowdiff_time(self):
        for batch in self.data:
            print batch.name            
            batch.eval_windowdiff_time()

    def eval_windowdiff_unit(self):
        for batch in self.data:
            print batch.name
            batch.eval_windowdiff_unit()

    def eval_precision_recall_f1(self):
        for batch in self.data:
            print batch.name            
            batch.eval_precision_recall_f1()

    #  ==================== Plotting ====================

    def plot_compare_methods(self, metric, directory):
        """
        Plot results for one metric across different damaging methods

        :param metric:
        :param directory: Directory for writing the plot in PDF format
        """
        if metric not in self.metrics:
            raise ValueError('No results to plot for ' + metric)
        pyplot.axis([0, 100, 0.0, 1.05])
        pyplot.grid(which='major', color='0.75', linestyle='-')
        pyplot.xlabel('n (%)')
        for batch in self.data:
            pyplot.plot(batch.n_list, batch.list_results_metric(metric),
                        label=batch.method, linewidth=0.6)
        pyplot.legend(loc=8, ncol=2, fontsize=9)
        pyplot.savefig(os.path.join(directory,
                                    'compare_methods_{}.pdf'.format(metric)))
        pyplot.cla()

    def write_csv(self, directory):
        """
        Write all information including evaluation results about
        each damaged copy batch by batch to CSV
        """
        for batch in self.data:
            batch.write_csv(directory)


