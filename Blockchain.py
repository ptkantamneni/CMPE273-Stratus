from ecdsa import VerifyingKey
import requests
from flask import Flask, jsonify, request
import json
import hashlib
from time import time
from threading import Thread

app = Flask(__name__)

class Blockchain:
    def __init__(self):
        self.registered_manufacturer = {}
        self.utxo = {}
        self.current_transactions = {}
        self.chain = []

        self.new_block(proof = self.proof_of_work('CMPE273 - Team Stratus'),previous_hash='CMPE273 - Team Stratus')

    def new_block(self, proof,previous_hash = None):
        block = {
            'timestamp': time(),
            'header' : {
                'index': len(self.chain),
                'proof': proof,
                'root': self.merkel_root(self.current_transactions),
                'previous_hash': previous_hash or self.hash(self.chain[-1]['header'])
            },
            'transactions': self.current_transactions
        }

        # Reset the current list of transactions
        self.current_transactions = {}

        self.chain.append(block)
        return block
    
    def merkel_root(self,my_transactions):
        block_string = json.dumps(my_transactions, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
        
    def hash(self,data):
        block_string = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self,previous_hash = None):
        me = {
            'index': len(self.chain),
            'proof': 0,
            'root': self.merkel_root(self.current_transactions),
            'previous_hash': previous_hash or self.hash(self.chain[-1]['header'])
        }

        while self.hash(me)[:4]!="0000":
            me['proof'] += 1

        return me['proof']

    def valid_chain(self,new_chain):
        return True
@app.route('/manufacturer/produce', methods=['POST'])
def produce():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['manufacture_name', 'signature', 'data']
    if not all(k in values for k in required):
        return jsonify({ 'message' :'Missing values'}), 400

    if values['manufacture_name'] not in my_blockchain.registered_manufacturer:
        return jsonify({ 'message' :'Unregistered manufacturer'}), 400

    public_key = VerifyingKey.from_pem(my_blockchain.registered_manufacturer[values['manufacture_name']])

    result = public_key.verify(bytes.fromhex(values['signature']),json.dumps(values['data'], sort_keys=True).encode("utf-8"))

    if not result:
        return jsonify({ 'message' :'Authentacation Failed: Dropping transaction'}), 400

    output_wallet = my_blockchain.registered_manufacturer[values['manufacture_name']]
    manufacture_name = values['manufacture_name']
    product = values['data']['product']
    quantity = values['data']['quantity']
    new_transaction = {
        'input_wallet' : 0,
        'output_wallet' : output_wallet,
        'manufacture_name' : manufacture_name,
        'product' : product,
        'quantity' : quantity
    } 
    my_blockchain.utxo[output_wallet]= my_blockchain.utxo.get(output_wallet,{})
    my_blockchain.utxo[output_wallet][manufacture_name]= my_blockchain.utxo[output_wallet].get(manufacture_name,{})
    my_blockchain.utxo[output_wallet][manufacture_name][product]= my_blockchain.utxo[output_wallet][manufacture_name].get(product,0) + quantity

    my_blockchain.current_transactions[values['signature']] = new_transaction

    response = {
        'message' : 'Transaction will be adden in block number: ' + str(len(my_blockchain.chain)),
        'Manufacturers_wallet' : my_blockchain.utxo[output_wallet]
    }

    print(response)
    start_gossip()
    return jsonify(response), 201

@app.route('/manufacturer/register', methods=['POST'])
def register():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['public_key','manufacture_name']
    if not all(k in values for k in required):
        return jsonify({ 'message' :'Missing values'}), 400

    if values['manufacture_name'] in my_blockchain.registered_manufacturer:
        return jsonify({ 'message' :'Name Already Registered'}), 400

    my_blockchain.registered_manufacturer[values['manufacture_name']] = values['public_key']
    response = 'Manufacturer added - ' + values['manufacture_name']
    print(response)
    # start_gossip()
    return  jsonify({ 'message' :response}), 201

@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['signature', 'transaction']
    if not all(k in values for k in required):
        return jsonify({ 'message' :'Missing values'}), 400
    required = ['input_wallet', 'output_wallet', 'manufacture_name' , 'product' ,'quantity'] 
    if not all(k in values['transaction'] for k in required):
        return jsonify({ 'message' :'Missing values in transaction'}), 400

    input_wallet = VerifyingKey.from_pem(values['transaction']['input_wallet'])
    result = input_wallet.verify(bytes.fromhex(values['signature']),json.dumps(values['transaction'], sort_keys=True).encode("utf-8"))

    if not result:
        return jsonify({ 'message' :'Authentacation Failed: Dropping transaction'}), 400

    input_wallet = values['transaction']['input_wallet']
    output_wallet = values['transaction']['output_wallet']
    manufacture_name = values['transaction']['manufacture_name']
    product = values['transaction']['product']
    quantity = values['transaction']['quantity']
    if (input_wallet in my_blockchain.utxo) and (manufacture_name in my_blockchain.utxo[input_wallet]) and (product in my_blockchain.utxo[input_wallet][manufacture_name]):
        if my_blockchain.utxo[input_wallet][manufacture_name][product] >= quantity:
            my_blockchain.utxo[input_wallet][manufacture_name][product] -= quantity
            my_blockchain.utxo[output_wallet]= my_blockchain.utxo.get(output_wallet,{})
            my_blockchain.utxo[output_wallet][manufacture_name]= my_blockchain.utxo[output_wallet].get(manufacture_name,{})
            my_blockchain.utxo[output_wallet][manufacture_name][product]= my_blockchain.utxo[output_wallet][manufacture_name].get(product,0) + quantity
            my_blockchain.current_transactions[values['signature']] = values['transaction']
            response = {
                'message' : 'Transaction will be adden in block number: ' + str(len(my_blockchain.chain)),
                'new_input_wallet' : my_blockchain.utxo[input_wallet],
                'new_output_wallet' : my_blockchain.utxo[output_wallet]
            }
            print(response)
            start_gossip()
            return jsonify(response), 201
        else:
            return jsonify({ 'message' :'Wallet does not have enough product(Required = {r}, Available = {a}): Dropping transaction'.format(r=my_blockchain.utxo[input_wallet][manufacture_name][product],a=quantity)}), 400
    else:
        return jsonify({ 'message' :'Wallet does not have the product: Dropping transaction'}), 400

@app.route('/mine', methods=['POST'])
def mine_block():
    proof = my_blockchain.proof_of_work()
    my_blockchain.new_block(proof)

    start_gossip()
    return jsonify(my_blockchain.chain[-1]), 200

@app.route('/state', methods=['GET'])
def get_state():
    response = {
        'registered_manufacturer' : my_blockchain.registered_manufacturer,
        'utxo' : my_blockchain.utxo,
        'current_transactions': my_blockchain.current_transactions,
        'chain': my_blockchain.chain
    }
    return jsonify(response), 200

@app.route('/gossip', methods=['POST'])
def gossip():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['registered_manufacturer', 'utxo','current_transactions','chain']
    if not all(k in values for k in required):
        return jsonify({ 'message' :'Missing values'}), 400
    
    # spread_gossip = False

    response = {
        'registered_manufacturer' : my_blockchain.registered_manufacturer,
        'utxo' : my_blockchain.utxo,
        'current_transactions': my_blockchain.current_transactions,
        'chain': my_blockchain.chain
    }
    values_string = json.dumps(values, sort_keys=True).encode()
    my_string = json.dumps(response, sort_keys=True).encode()

    if values_string==my_string:
        return jsonify({'message':'We are equal'}), 200

    # spread_gossip = True

    if len(values['chain']) >= len(my_blockchain.chain):
        print("length greater")
        if(my_blockchain.valid_chain(values['chain'])):
            my_blockchain.chain = values['chain']

    my_blockchain.utxo = values['utxo']
    my_blockchain.current_transactions = values['current_transactions']
    
    my_blockchain.registered_manufacturer.update(values['registered_manufacturer'])

    start_gossip()

    return jsonify({'message':'Gossiping'}), 200

@app.route('/gossip/friend_request', methods=['POST'])
def friend_request():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['my_info']
    if not all(k in values for k in required):
        return jsonify({ 'message' :'Missing values'}), 400

    if values['my_info'] not in gossip_friends:
        gossip_friends.append(values['my_info'])
        friend_request = {'my_info': port}
        try:
            requests.post('http://0.0.0.0:{port}/gossip/friend_request'.format(port = values['my_info']), data = json.dumps(friend_request),headers = {'content-type': 'application/json'})
        except :
            pass
    
    return jsonify({ 'message' :'Hi Friend'}), 200

@app.route('/gossip/friends', methods=['GET'])
def gossip_friends():
    return jsonify({'gossip_friends':gossip_friends}), 200

def start_gossip():
    send_friend_requests()
    response = {
        'registered_manufacturer' : my_blockchain.registered_manufacturer,
        'utxo' : my_blockchain.utxo,
        'current_transactions': my_blockchain.current_transactions,
        'chain': my_blockchain.chain
    }
    
    for gossip_friend in gossip_friends:
        Thread(target=dispatch_gossip, args=(gossip_friend,response )).start()

def dispatch_gossip(gossip_friend,response):
    try:
        requests.post('http://0.0.0.0:{port}/gossip'.format(port = gossip_friend), data = json.dumps(response),headers = {'content-type': 'application/json'})
    except :
        pass

def send_friend_requests():
    # senf friend requests
    friend_request = {'my_info': port}
    for gossip_friend in gossip_friends:
        try:
            requests.post('http://0.0.0.0:{port}/gossip/friend_request'.format(port = gossip_friend), data = json.dumps(friend_request),headers = {'content-type': 'application/json'})
        except :
            pass
    
if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-f','--friends', nargs='+', type=int,default=[], help='set ports to gossip')
    args = parser.parse_args()
    port = args.port
    gossip_friends = args.friends

    send_friend_requests()

    # Instantiate the Blockchain
    my_blockchain = Blockchain()

    app.run(host='0.0.0.0', port=port)