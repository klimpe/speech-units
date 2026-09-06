import damgroup


class MetaEval(object):
    """
     One meta-evaluation experiment.
     Consists of multiple DamagedGroups with the same parameters.
     Plots means with standard deviations
     across methodsand across metrics.
     ? tables and plots of each DamagedGroup -> separate directories
    """

    def __init__(self):
        data = []

    def generate_data(self,
                      reference, original, n_range, iterations,
                      verbose=True):
        for i in range(iterations):
            print '\n\nIteration', i
            dg = damgroup.DamGroup(reference, original)
            print 'Generating: insert'
            dg.generate_damaged_batch('insert', n_range, verbose=verbose)
            print 'Generating: remove'
            dg.generate_damaged_batch('remove', n_range, verbose=verbose)
            print 'Generating: shift'
            dg.generate_damaged_batch('shift', n_range,
                                      shift_max_a=5, multi_a=True,
                                      verbose=verbose)
            print 'Calculating metrics'
            dg.evaluate()

    # def read_data(self):
    #     """
    #     Reads in metric results from multiple CSV files
    #     :return: None
    #     """
    #     pass
