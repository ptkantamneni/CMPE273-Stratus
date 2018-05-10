from ecdsa import SigningKey , SECP256k1
import json, requests
from random import random
import os.path

def register(name):
    with open ("Private-{name}.pem".format(name=name), "w") as prv_file:
        print("{}".format(key.to_pem().decode()), file=prv_file)

    with open ("Public-{name}.pem".format(name=name), "w") as pub_file:
        print("{}".format(key.get_verifying_key().to_pem().decode()), file=pub_file)

    public_key = key.get_verifying_key().to_pem().decode()[27:-26]
    public_key = public_key[:64] + public_key[65:]
    send_info = {
        'public_key': public_key,
        'manufacture_name': name
    }

    r = requests.post('http://{port}/manufacturer/register'.format(port = port), data = json.dumps(send_info),headers = {'content-type': 'application/json'})
    print(r.text)
 
def manufacture(name,product_name,product_quantity):

    try:
        product_quantity = int(product_quantity)
    except ValueError:
        print("Please Only enter an Interger value for Quantity.")
        return
    
    data = {
        'product': product_name,
        'quantity': product_quantity,
        'salt': random()
    }

    signature = key.sign(json.dumps(data, sort_keys=True).encode("utf-8")).hex()
    send_info = {
        'manufacture_name' : name,
        'signature' : signature, 
        'data' : data
    }

    print(json.dumps(send_info, indent=4))
    r = requests.post('http://{port}/manufacturer/produce'.format(port = port), data = json.dumps(send_info),headers = {'content-type': 'application/json'})
    print("Response")
    print(r.text)

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-u', '--url', default="http://0.0.0.0:80", type=str, help='url to connect to')
    parser.add_argument('-n', '--name', default="Arpit", type=str, help='name of manufacturer')
    parser.add_argument('-pr', '--prod', default="Arpit", type=str, help='name of product')
    parser.add_argument('-q', '--quantity', default=0, type=int, help='quantity')
    args = parser.parse_args()
    port = args.url
    name = args.name
    product = args.prod
    quantity = args.quantity

    if os.path.isfile("Private-{name}.pem".format(name=name)):
        f=open("Private-{name}.pem".format(name=name), "r")
        if f.mode == 'r':
            file_data = f.read()
            key = SigningKey.from_pem(file_data)

            public_key = key.get_verifying_key().to_pem().decode()[27:-26]
            public_key = public_key[:64] + public_key[65:]
            send_info = {
                'public_key': public_key,
                'manufacture_name': name
            }
            r = requests.post('http://{port}/manufacturer/register'.format(port = port), data = json.dumps(send_info),headers = {'content-type': 'application/json'})
        f.close()
    else:
        key = SigningKey.generate(curve=SECP256k1) 
        register(name)

    manufacture(name,product,quantity)
