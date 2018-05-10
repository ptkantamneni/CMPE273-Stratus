from ecdsa import SigningKey, VerifyingKey, SECP256k1
import os.path
import json, requests

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-f', '--from_w', default="Arpit", type=str, help='name of from wallet')
    parser.add_argument('-t', '--to_w', default="Arpit", type=str, help='name of to wallet')
    parser.add_argument('-m', '--manu', default="Arpit", type=str, help='name of manufacturer')
    parser.add_argument('-pr', '--prod', default="Arpit", type=str, help='name of product')
    parser.add_argument('-q', '--quantity', default=0, type=int, help='quantity')
    parser.add_argument('-u', '--url', default="http://0.0.0.0:80", type=str, help='url to connect to')
    args = parser.parse_args()
    from_w = args.from_w
    to_w = args.to_w
    manufacture_name = args.manu
    product = args.prod
    quantity = args.quantity
    port = args.url

    if not os.path.isfile("Private-{name}.pem".format(name=from_w)):
        print("From wallet doesn't exist :" + from_w)
        exit
    if not os.path.isfile("Public-{name}.pem".format(name=to_w)):
        print("To wallet doesn't exist : " + to_w)
        exit

    f=open("Private-{name}.pem".format(name=from_w), "r")
    if f.mode == 'r':
        file_data = f.read()
        from_private_key = SigningKey.from_pem(file_data)

        from_public_key = from_private_key.get_verifying_key().to_pem().decode()[27:-26]
        from_public_key = from_public_key[:64] + from_public_key[65:]
    f.close()

    f=open("Public-{name}.pem".format(name=to_w), "r")
    if f.mode == 'r':
        file_data = f.read()
        to_public_key = VerifyingKey.from_pem(file_data)

        to_public_key = to_public_key.to_pem().decode()[27:-26]
        to_public_key = to_public_key[:64] + to_public_key[65:]
    f.close()

    new_transaction = {
        'input_wallet' : from_public_key,
        'output_wallet' : to_public_key,
        'manufacture_name' : manufacture_name,
        'product' : product,
        'quantity' : quantity
    } 

    signature = from_private_key.sign(json.dumps(new_transaction, sort_keys=True).encode("utf-8")).hex()
    send_info = {
        'signature' : signature, 
        'transaction' : new_transaction
    }


    print(json.dumps(send_info, indent=4))
    r = requests.post('http://{port}/transaction/new'.format(port = port), data = json.dumps(send_info),headers = {'content-type': 'application/json'})
    print("Response")
    print(r.text)

