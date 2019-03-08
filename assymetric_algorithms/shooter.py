import sys, hashlib, string, getpass, binascii, struct, cPickle, random, sympy, socket, select
from copy import copy
from random import randint
from struct import *
from Crypto.Util import number
from Crypto.Cipher import AES


# produce 2 large random primes if and only if q and 2q + 1 are prime
def rand_prime(n_length):

    primeNum = number.getPrime(n_length)
    while sympy.isprime(2*primeNum + 1) == False:
        primeNum = number.getPrime(n_length)
    return (2*primeNum + 1)


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


# connect to desired address
def connect(addr):
    s = socket.socket()
    port = 36799
    s.connect((addr, port))

    return s


# get alpha, beta, and p  from "Bob" (target.py)
def get_public_keys(s):
    toks = s.recv(1024).split()
    alpha = int(toks[0])
    beta = int(toks[1])
    p = int(toks[2])

    return alpha, beta, p


# get AES key in string and int form from user input
def get_aes_key(n_length):
    aes_string = raw_input("AES_key to send: ")

    end = len(aes_string)
    if end > n_length:
        end = n_length

    aes_int = int(binascii.hexlify(aes_string[0:end]),16)

    return aes_string, aes_int

# send messages back and forth
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
                print "Alice: ", decrypted_data


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

    if len(sys.argv) != 2:
        print "expected address of target\n",

    n_length = 256

    # connect to target
    s = connect(sys.argv[1])


    # get alpha, beta, and p
    alpha, beta, p = get_public_keys(s)
    print "alpha: ", alpha
    print "beta: ", beta
    print "p: ", p


    # produce own key
    key = number.getPrime(256)
    print "private key: ", key

    # send encrypted messages y_1 and y_2, and get input x from user in string and integer form
    message_one = square_and_multiply(alpha,key,p)
    aes_string, aes_int = get_aes_key(5)
    message_two = (aes_int * square_and_multiply(beta,key,p)) % p

    s.send(str(message_one) + " " + str(message_two))


    # keep sending message
    send_msgs(s,aes_string)

    s.shutdown(2)
    s.close()


if __name__ == "__main__":
    main()
