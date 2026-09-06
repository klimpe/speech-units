import segmentools
import metaeval_run

reference, original = metaeval_run.load_test_ip_300_seconds()
dg = segmentools.DamGroup(reference,original)
dg.generate_damaged_batch('shift', (10, 50, 10), verbose=True, shift_max_a=5)

