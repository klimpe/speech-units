import dambatch


class DamData(object):
    """
    Collection of DamBatch objects,
    represents the entire set of generated damaged segmentations
    with different parameters concerning the same original segmentation
    """
    def __init__(self, reference, original):
        self.reference = reference
        self.original = original
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

    def methods(self):
        """
        Lists damaging methods of the available DamBatch objecs
        == OUT ==
        list or None
        """
        return [x.method for x in self.data]

    def generate_batch(self, method, n_range, shift_max_a=1,
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
            batch = dambatch.DamBatch(self.reference, self.original)
            batch.generate_by_inserting(n_range, verbose=verbose)
            self.data.append(batch)
        elif method == 'remove':
            batch = dambatch.DamBatch(self.reference, self.original)
            batch.generate_by_removing(n_range, verbose=verbose)
            self.data.append(batch)
        elif method == 'shift':
            for a in range(1, shift_max_a + 1):
                batch = dambatch.DamBatch(self.reference, self.original)
                batch.generate_by_shifting(n_range, a, skip=skip,
                                           multi_a=multi_a, verbose=verbose)
                self.data.append(batch)


                # def add(self, dbatch):
    #     """
    #     Add one DamBatch
    #     == IN ==
    #     dsegm : DamBatch
    #     == OUT ==
    #     None
    #     """
    #     if not isintance(dbatch, DamBatch):
    #         raise TypeError('Expecting a DamBatch instance')
    #     if method in self.methods():
    #         raise ValueError('There is already a DamBatch'
    #                          'with this damaging method')
    #     self._data.append(dbatch)
