import tierutil


def preprocess(tier, onlycheck=True):
    '''
    If sequence of labels '[^#]+', '', '#' is detected,
    the second interval is removed. Modifies the tier in-place.
    
    In:
      tier (Tier)
      onlycheck (bool) Don't modify, only count
    '''
    itr = 0
    to_remove = []
    labels = [x.TextValue.strip() for x in tier] 
    print 'Empty intervals', labels.count('')
    while itr < len(tier)-2:
        if tier[itr].TextValue.strip() not in ('#', ''):
            if tier[itr+1].TextValue.strip()=='':
                if tier[itr+2].TextValue.strip()=='#':
                    to_remove.append(tier[itr].End)
        itr += 1

    print 'len(tier)',len(tier)
    print len(to_remove)
    if not onlycheck:
        for boundary in to_remove:
            tierutil.boundary_remove(tier, boundary)
    print 'len(tier)', len(tier)