import requests

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    r = requests.post('http://0.0.0.0:{port}/mine'.format(port = port))

    print(r.text)
    