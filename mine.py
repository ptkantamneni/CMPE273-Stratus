import requests

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-u', '--url', default="http://0.0.0.0:80", type=str, help='url to connect to')
    args = parser.parse_args()
    port = args.url

    r = requests.post('http://{port}/mine'.format(port = port))

    print(r.text)
    