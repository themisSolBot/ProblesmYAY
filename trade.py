import requests
import time
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from solders.commitment_config import CommitmentLevel
from solders.rpc.requests import SendVersionedTransaction
from solders.rpc.config import RpcSendTransactionConfig

def execute_trade(action, amount, TOKEN_TO_SWAP, publickey, privatekey, denominatedInSol, custom_tip, custom_slippage, pool):
    print('POOL HERE:')
    print(pool)
    start_time = time.time()
    response = requests.post(url="https://pumpportal.fun/api/trade-local", data={
        "publicKey": publickey,
        "action": action,
        "mint": TOKEN_TO_SWAP,
        "amount": amount,
        "denominatedInSol": denominatedInSol,
        "slippage": float(custom_slippage),
        "priorityFee": float(custom_tip),
        "pool": pool
    })

    keypair = Keypair.from_base58_string(privatekey)
    tx = VersionedTransaction(VersionedTransaction.from_bytes(response.content).message, [keypair])
    commitment = CommitmentLevel.Confirmed
    config = RpcSendTransactionConfig(preflight_commitment=commitment)
    txPayload = SendVersionedTransaction(tx, config)
    response = requests.post(
        url="https://mainnet.helius-rpc.com/?api-key=36bac32f-6707-4e3c-8905-7aef46a042a6",
        headers={"Content-Type": "application/json"},
        data=SendVersionedTransaction(tx, config).to_json()
    )

    txSignature = response.json()['result']
    print(f'{action.capitalize()} transaction: https://solscan.io/tx/{txSignature}')
    end_time = time.time()
    execution_time = end_time - start_time
    print(f'{action.capitalize()} transaction took {execution_time:.2f} seconds to execute')
    return 'https://solscan.io/tx/'+str(txSignature)

action = 'buy'
amount = 0.1
TOKEN_TO_SWAP = 'EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm'
publickey ='<pubkey>'
privatekey ='<privatekey>'
denominatedInSol = 'true'
custom_tip=0.002
custom_slippage = 10
pool = 'raydium'

tx = execute_trade(action, amount, TOKEN_TO_SWAP, publickey, privatekey, denominatedInSol, custom_tip, custom_slippage, pool)
print(tx)
