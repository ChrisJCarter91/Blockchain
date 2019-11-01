# Paste your version of blockchain.py from the client_mining_p
# folder here

import hashlib
import json
from time import time
from uuid import uuid4

from flask import Flask, jsonify, request
from flask_cors import CORS


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        A block should have:
        * Index
        * Timestamp
        * List of current transactions
        * The proof used to mine this block
        * The hash of the previous block
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": self.current_transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        # Append the chain to the block
        self.chain.append(block)

        # Return the new block
        return block

    def hash(self, block):
        """
        Creates a SHA-256 hash of a Block
        :param block": <dict> Block
        "return": <str>
        """

        # Use json.dumps to convert json into a string
        # Use hashlib.sha256 to create a hash
        # It requires a `bytes-like` object, which is what
        # .encode() does.
        # It convertes the string to bytes.
        # We must make sure that the Dictionary is Ordered,
        # or we'll have inconsistent hashes

        # TODO: Create the block_string
        string_object = json.dumps(block, sort_keys=True)
        block_string = string_object.encode()

        # TODO: Hash this string using sha256
        raw_hash = hashlib.sha256(block_string)
        hex_hash = raw_hash.hexdigest()

        # By itself, the sha256 function returns the hash in a raw string
        # that will likely include escaped characters.
        # This can be hard to read, but .hexdigest() converts the
        # hash to a string of hexadecimal characters, which is
        # easier to work with and understand

        # Return the hashed block string in hexadecimal format
        return hex_hash

    @property
    def last_block(self):
        return self.chain[-1]

    # def proof_of_work(self, block):
    #     """
    #     Simple Proof of Work Algorithm
    #     Stringify the block and look for a proof.
    #     Loop through possibilities, checking each one against `valid_proof`
    #     in an effort to find a number that is a valid proof
    #     :return: A valid proof for the provided block
    #     """
    #     # GUESS
    #     # proof is a sha356 hash with 3 leading zeros
    #     block_string = json.dumps(block, sort_keys=True).encode()
    #     proof = 0
    #     while self.valid_proof(block_string, proof) is False:
    #         proof += 1
    #     return proof

    @staticmethod
    def valid_proof(block_string, proof):
        """
        Validates the Proof:  Does hash(block_string, proof) contain 3
        leading zeroes?  Return true if the proof is valid
        :param block_string: <string> The stringified block to use to
        check in combination with `proof`
        :param proof: <int?> The value that when combined with the
        stringified previous block results in a hash that has the
        correct number of leading zeroes.
        :return: True if the resulting hash is a valid proof, False otherwise
        """
        # CHECK
        guess = f'{block_string}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        print(guess_hash)
        return guess_hash[:3] == "000"

    def new_transaction(self, sender, recipient, amount):
        transaction = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount
        }

        self.current_transactions.append(transaction)

        return self.last_block["index"] + 1


# Instantiate our Node
app = Flask(__name__)
CORS(app)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['POST'])
def mine():
    data = request.get_json()

    if "id" not in data or "proof" not in data:
        response = {
            "message": "Please include id and proof"
        }

        return jsonify(response), 400

    # Run the proof of work algorithm to get the next proof
    proof = data["proof"]

    # Forge the new Block by adding it to the chain with the proof
    block_string = json.dumps(blockchain.last_block, sort_keys=True).encode()
    guessed = f'{block_string}{proof}'.encode()
    guessed_hash = hashlib.sha256(guessed).hexdigest()

    # blockchain.valid_proof(block_string, proof)
    if guessed_hash[:3] == "000":
        blockchain.new_transaction(sender="0", recipient=data["id"], amount=1)

        previous_hash = guessed_hash

        block = blockchain.new_block(proof, previous_hash)

        response = {
            "message": "New Block Forged",
            "index": block['index'],
            "transactions": block['transactions'],
            "proof": block['proof'],
            "previous_hash": block['previous_hash'],
        }

        return jsonify(response), 200

    else:
        response = {
            "message": "ERROR: not valid proof"
        }

        return jsonify(response), 200


@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    data = request.get_json()

    required = ["recipient", "sender", "amount"]

    if not all(k in data for k in required):
        response = {
            "message": "ERROR: Please supply a recipient, sender and amount."
        }

        return jsonify(response), 400

    index = blockchain.new_transaction(
        data["sender"], data["recipient"], data["amount"])

    response = {
        "message": f"Transaction will be added to block {index}"
    }

    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        "length": len(blockchain.chain),
        "chain": blockchain.chain
    }
    return jsonify(response), 200


@app.route('/last_block', methods=['GET'])
def last_block_endpoint():
    response = {
        "last_block": blockchain.last_block
    }
    return jsonify(response), 200


# Run the program on port 5000
if __name__ == '__main__':
    app.run(host='localhost', port=5000)