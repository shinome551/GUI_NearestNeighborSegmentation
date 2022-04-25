# distutils: language=c++
# distutils: extra_compile_args = ["-O3"]
# cython: language_level=3, boundscheck=False, wraparound=False
# cython: cdivision=True

cpdef updateLUT(unsigned short[:,:,:] dlut, unsigned char[:,:,:] tlut):
    cdef:
        int n = dlut.shape[0]
        int i, j, k
        
    ## forwarding
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if i < n - 1:
                    if dlut[j][i+1][k] > dlut[j][i][k] + 1:
                        dlut[j][i+1][k] = dlut[j][i][k] + 1
                        tlut[j][i+1][k] = tlut[j][i][k]
                if j < n - 1:
                    if dlut[j+1][i][k] > dlut[j][i][k] + 1:
                        dlut[j+1][i][k] = dlut[j][i][k] + 1
                        tlut[j+1][i][k] = tlut[j][i][k]
                if k < n - 1:
                    if dlut[j][i][k+1] > dlut[j][i][k] + 1:
                        dlut[j][i][k+1] = dlut[j][i][k] + 1
                        tlut[j][i][k+1] = tlut[j][i][k]

    ## backwarding
    for i in reversed(range(n)):
        for j in reversed(range(n)):
            for k in reversed(range(n)):
                if i > 0:
                    if dlut[j][i-1][k] > dlut[j][i][k] + 1:
                        dlut[j][i-1][k] = dlut[j][i][k] + 1
                        tlut[j][i-1][k] = tlut[j][i][k]
                if j > 0:
                    if dlut[j-1][i][k] > dlut[j][i][k] + 1:
                        dlut[j-1][i][k] = dlut[j][i][k] + 1
                        tlut[j-1][i][k] = tlut[j][i][k]
                if k > 0:
                    if dlut[j][i][k-1] > dlut[j][i][k] + 1:
                        dlut[j][i][k-1] = dlut[j][i][k] + 1
                        tlut[j][i][k-1] = tlut[j][i][k]
