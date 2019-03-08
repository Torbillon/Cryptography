import sys, hashlib, string, getpass, binascii, struct, cPickle
from copy import copy
from random import randint
from struct import *

size = 5
length = 50
# w
dub = 2
# l
log = 1
# x and y offset from middle
offset = 2
# ascii value of 0
zeroii = 48
# used for rho(), shifts
delta = [
    [1,1,1,0,1], #4
    [1,0,0,0,0], #3
    [0,1,0,1,0], #2
    [0,0,0,0,1], #1
    [1,0,1,1,1]  #0
   # 0 1 2 3 4
]

X = (3,4,0,1,2)

# turn state matrix to binary string
def binary2chr(v):
    count = 0
    x = ""
    for j in range(size):
        for i in range(size):
            count += 2
            if count % 8 == 0:
                x += byte2chr(i,j,v)
    x += chr(v[1][1][0]<<7 | v[1][1][1]<<6)
    return x

#turn 8-length binary string to char
def byte2chr(i,j,v):
    x = 0
    z = 1
    for k in range(4):
        x += v[(i+offset)%5][(j+offset)%5][0]*2*z + v[(i+offset)%5][(j+offset)%5][1]*z
        z *= 4
        i= (i-1) % size
        if i == 4:
            j= (j-1) % size
    return chr(x)

#turn string str of char to binary string x
def bytes2binary(str):
    x = ""
    for ch in str[0:]:
        x += byte2binary(ord(ch))
    return x

# turn integer v to binary string x
# ex. byte2binary: 2 -> "0010"
def byte2binary(v):
    x = ""
    for i in range(8):
        x = str(v & 0x1) + x
        v /= 2
    return x

# initialize state matrix from binary string v
# first slice of array is of form:
# [0,0,0,0,0] 4
# [0,0,0,0,0] 3
# [0,0,0,0,0] 2
# [0,0,0,0,0] 1
# [0,0,0,0,0] 0
#  0 1 2 3 4
def fill(v):
    x = [[[0 for k in range(dub)] for j in range(size)] for i in range(size)]
    if len(v) > length:
        temp = length
    else:
        temp = len(v)
    for i in range(0,temp):
        x[((i/2)%5+offset)%5][((i/10)+offset)%5][i%2] = ord(v[i]) - zeroii

    # 0-pad it if not enough bytes
    for i in range(temp,length):
        x[((i/2)%5+offset)%5][((i/10)+offset)%5][i%2] = 0
    return x


# DONE
def theta(v):
    c = [[0 for k in range(dub)] for i in range(size)]
    d = [[0 for k in range(dub)] for i in range(size)]
    x = [[[0 for k in range(dub)] for j in range(size)] for i in range(size)]
    # for all x
    for i in range(size):
        # for all z
        for k in range(dub):
            c[i][k] = v[i][0][k] ^ v[i][1][k] ^ v[i][2][k] ^ v[i][3][k] ^ v[i][4][k]
    # for all x
    for i in range(size):
        #for all z
        for k in range(dub):
            d[i][k] = c[(i-1)%5][k] ^ c[(i+1)%5][(k-1)%dub]

    # for all x
    for i in range(size):
        # for all y
        for j in range(size):
            # for all z
            for k in range(dub):
                x[i][j][k] = v[i][j][k] ^ d[i][k]
    return x

#DONE
def rho(v):

    # for all x
    for i in range(size):
        # for all y
        for j in range(size):
            # switch
            if delta[4-j][i] == 1:
                v[i][j][0], v[i][j][1] = v[i][j][1], v[i][j][0]

    return v

#DONE
def pi(v):
    x = [[[0 for k in range(dub)] for j in range(size)] for i in range(size)]

    # for all x
    for i in range(size):
        # for all y
        for j in range(size):
            # for all z
            for k in range(dub):
                x[i][j][k] = v[(i + 3*X[j])%5][(j+X[i]-X[j])%5][k]
    return x

#DONE
def chi(v):
    x = [[[0 for k in range(dub)] for j in range(size)] for i in range(size)]

    # for all x
    for i in range(size):
        # for all y
        for j in range(size):
            # for all z
            for k in range(dub):
                x[i][j][k] = v[i][j][k] ^ ((v[(i+1)%5][j][k]^1) & v[(i+2)%5][j][k])

    return x

#DONE
def iota(v,n):

    r = [0,0]
    r[0] = rc(0+7*n)
    r[1] = rc(1+7*n)

    for k in range(dub):
        v[0][0][k] ^= r[k]

    return v

#DONE
def rc(t):
    if t%225 == 0:
        return 1

    R = [1,0,0,0,0,0,0,0,0]
    for i in range(1,((t+1)%225)):
        R = shift(R)
        R[0] = R[0] ^ R[8]
        R[4] = R[4] ^ R[8]
        R[5] = R[5] ^ R[8]
        R[6] = R[6] ^ R[8]

    return R[0]

# mimics  0 | R
def shift(x):
    #shift everything
    for i in range(8,0,-1):
        x[i] = x[i-1]
    x[0] = 0
    return x

# rounds
def Rnd(v,i):
    return iota(chi(pi(rho(theta(v)))),i)

def keccak(raw,n):
    # v becomes a state matrix
    v = fill(raw)

    for i in range(12+2*log-n,12+2*log):
        v = Rnd(v,i)

    # convert state matrix to string
    x = binary2chr(v)


    fileV = "p-hash.sha3"

    try:
        outfile = open(fileV,"w")
    except:
        print "cannot open output file -", filV
        sys.exit()

    outfile.write(x)

def main():
    if len(sys.argv) == 3:
        infile = sys.argv[1]
        numRounds = sys.argv[2]
    else:
        print "expected file and number of rounds as input"
        sys.exit()

    try:
        fp = open(infile, "rb")
    except:
        print "failed to open input file -", myInput
        sys.exit()

    raw = fp.read(7)
    raw_prime = bytes2binary(raw)
    keccak(raw_prime,int(numRounds))


if __name__ == "__main__":
    main()
