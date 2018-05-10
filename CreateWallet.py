from ecdsa import SigningKey , SECP256k1
import os.path


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-n', '--name', default="Arpit", type=str, help='name of wallet')
    args = parser.parse_args()
    name = args.name

    if os.path.isfile("Private-{name}.pem".format(name=name)):
        print("Wallet with this name already exists")
    else:
        # SECP256k1 is the Bitcoin elliptic curve
        key = SigningKey.generate(curve=SECP256k1) 
        with open ("Private-{name}.pem".format(name=name), "w") as prv_file:
            print("{}".format(key.to_pem().decode()), file=prv_file)

        with open ("Public-{name}.pem".format(name=name), "w") as pub_file:
            print("{}".format(key.get_verifying_key().to_pem().decode()), file=pub_file)
        
        print("Wallet created :" + name)