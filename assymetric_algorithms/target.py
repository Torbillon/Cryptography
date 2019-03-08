import sys, hashlib, string, getpass, binascii, struct, cPickle, random, sympy, socket, select
from copy import copy
from random import randint
from struct import *
from Crypto.Util import number
from Crypto.Cipher import AES

# produce p and q
def rand_prime(n_length):
    primeNum = number.getPrime(n_length)
    while sympy.isprime(2*primeNum + 1) == False:
        primeNum = number.getPrime(n_length)
    return primeNum, (2*primeNum + 1)

# calculates a^b (mod n)
def square_and_multiply(a,b,n):
    rem = 1
    alpha = a


    if b & 0x1 == 0x1:
        rem = a
    b //= 2;


    while b != 0:
        alpha = (alpha * alpha) % n
        if b & 0x1 == 0x1:
            rem = (rem * alpha) % n
        b //= 2

    return rem

# generate a number-theoretic generator
def gen_generator(q,p):
    i = 2
    while i < q:
        if square_and_multiply(i,q,p) == 1:
            return i
        i = i + 1


def decrypt(msg_one,msg_two,p,key):
    zeta = square_and_multiply(msg_one,key,p)
    zeta_inverse = mult_inverse(zeta,p)
    return (msg_two * zeta_inverse) % p


# calculate a^(-1) (mod b)
def mult_inverse(a,b):
    p_old = 1
    p_prime = 0
    rem_old = a
    rem_prime = b
    while rem_prime != 0:
        quot = rem_old//rem_prime
        rem_old, rem_prime = rem_prime, rem_old - (quot * rem_prime)
        p_old, p_prime = p_prime, p_old - (quot * p_prime)

    return (p_old % b)


# passively connect
def passive_connect():
    s = socket.socket()
    host = socket.gethostname()
    port = 36799
    s.bind((host,port))

    s.listen(5)
    c, addr = s.accept()

    return s, c


# generate beta, alpha, q, and p
def get_public_keys():
    n_length = 256
    q_prime, p_prime = rand_prime(n_length)
    alpha = gen_generator(q_prime,p_prime)


    key = number.getPrime(n_length)
    beta = square_and_multiply(alpha,key,p_prime)
    return q_prime, p_prime, alpha, key, beta


def send_msgs(sock,password):
    key = hashlib.sha256(password).digest()
    IV = 16 * '\x00'
    mode = AES.MODE_CBC
    cryptor = AES.new(key, mode, IV=IV)

    socks = [sock,sys.stdin]
    flag = 1
    while flag == 1:

        readable,_,_ = select.select(socks,[],[])


        for s in readable:
            if s == sock:
                try:
                    data = sock.recv(256)
                except ConnectionResetError:
                    data = 0

                if data == '':
                    flag = 0
                    break

                pad(data)
                decrypted_data = cryptor.decrypt(data)
                print "Bob: ", decrypted_data


            if s == sys.stdin:
                line = sys.stdin.readline()

                if line != "exit\n":
                    line = line[:len(line)-1] + '\0'
                    line = pad(line)
                    encrypted_line = cryptor.encrypt(line)
                    print encrypted_line

                    sock.send(encrypted_line)
                else:
                    flag = 0


# add spaces to string st to make len(st) divisible by 16
def pad(st):
    extra = len(st) % 16
    if extra > 0:
        padsize = 16 - extra
        st = st + (' ' * padsize)

    return st


def main():
    # listen for connection
    s, c = passive_connect()


    # get generator, g, and primes q, p
    q_prime, p_prime, alpha, key, beta = get_public_keys()
    print "alpha: ", alpha
    print "beta: ", beta
    print "p: ", p_prime
    print "private key: ",key

    # send alpha, beta, and p over to shooter in that order
    c.send(str(alpha) + " " + str(beta) + " " + str(p_prime))


    # get encrypted messages
    toks = c.recv(514).split()
    message_one = int(toks[0])
    message_two = int(toks[1])


    # begin decryption
    aes_int = decrypt(message_one,message_two,p_prime,key)
    aes_string = binascii.unhexlify('%x' % aes_int)
    print "AES_key: ", aes_string

    send_msgs(c,aes_string)

    s.shutdown(2)
    s.close()

if __name__ == "__main__":
    main()
