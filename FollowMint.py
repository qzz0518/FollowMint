import json
import time
import requests
from blocknative.stream import Stream
from web3 import Web3
import os

configExample = {
    "RPC": "https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
    "privateKey": "",
    "blocknativeKey": "",
    "barkKey": "",
    "maxGasPrice": 50,
    "maxGasLimit": 1000000,
    "follow": [
        "0x8888887a5e2491fec904d90044e6cd6c69f1e71c",
        "0x555555B63d1C3A8c09FB109d2c80464685Ee042B",
        "0x99999983c70de9543cdc11dB5DE66A457d241e8B"
    ]
}


def print_green(message):
    stime = time.strftime("%m-%d %H:%M:%S", time.localtime())
    print(f'[{stime}] \033[1;32m{message}\033[0m')


def print_red(message):
    stime = time.strftime("%m-%d %H:%M:%S", time.localtime())
    print(f'[{stime}] \033[1;31m{message}\033[0m')


def print_blue(message):
    stime = time.strftime("%m-%d %H:%M:%S", time.localtime())
    print(f'[{stime}] \033[1;34m{message}\033[0m')


def bark(info, data):
    if barkKey != '':
        requests.get('https://api.day.app/' + barkKey + '/' + info + '?url=' + data)


def getMethodName(methodSignature):
    try:
        if methodSignature in methodNameList:
            return methodNameList[methodSignature]
        res = requests.get('https://www.4byte.directory/api/v1/signatures/?hex_signature=' + methodSignature)
        if res.status_code == 200:
            methodName = res.json()['results'][0]['text_signature'].split('(')[0].lower()
            print_blue(res.json()['results'][0]['text_signature'])
            if 'mint' in methodName:
                methodNameList[methodSignature] = True
                return True
        methodNameList[methodSignature] = False
        return False
    except:
        return False


async def txn_handler(txn, unsubscribe):
    to_address = txn['to']
    from_address = txn['from']
    to_address = w3.toChecksumAddress(to_address)
    gasPrice = txn['gasPrice']
    gasPrice = int(gasPrice)
    inputData = txn['input']
    value = txn['value']
    if value != '0':
        print_blue("非免费，跳过")
        return
    if to_address in mintadd:
        print_blue("mint过，跳过")
        return
    inputData = inputData.replace(from_address[2:].lower(), account.address[2:].lower())
    if not getMethodName(inputData[:10]):
        print_blue('可能不是mint交易,跳过')
        return
    if gasPrice > maxGasPrice:
        print_blue('gasPrice过高,跳过')
        return
    transaction = {
        'from': account.address,
        'chainId': chainId,
        'to': to_address,
        'gas': 2000000,
        'gasPrice': gasPrice,
        'nonce': w3.eth.getTransactionCount(account.address),
        'data': inputData
    }
    try:
        estimateGas = w3.eth.estimateGas(transaction)
        if estimateGas > maxGasLimit:
            print_blue('超过gasLimit上限，跳过')
            return
        transaction['gas'] = estimateGas
        signed = w3.eth.account.sign_transaction(transaction, privateKey)
        new_raw = signed.rawTransaction.hex()
        if to_address in mintadd:
            print_blue("mint过，跳过")
            return
        tx_hash = w3.eth.sendRawTransaction(new_raw)
        mintadd.append(to_address)
        print_green("mint交易发送成功" + w3.toHex(tx_hash))
        freceipt = w3.eth.waitForTransactionReceipt(tx_hash, 600)
        if freceipt.status == 1:
            print_green("mint成功")
            bark('mint成功', 'https://cn.etherscan.com/tx/' + w3.toHex(tx_hash))
        else:
            print_green("mint失败")
            bark('mint失败', 'https://cn.etherscan.com/tx/' + w3.toHex(tx_hash))
    except:
        print_blue('预测失败，跳过')
        return


def main():
    try:
        stream = Stream(blocknativeKey)
        filters = [{"status": "pending"}]
        print_blue(account.address)
        print_blue('开始监控')
        for follow in follows:
            stream.subscribe_address(follow, txn_handler, filters)
        stream.connect()
    except Exception as e:
        print_red(str(e))
        time.sleep(10)


if __name__ == '__main__':
    if not os.path.exists('config.json'):
        print_blue('请先配置config.json')
        file = open('config.json', 'w')
        file.write(json.dumps(configExample))
        file.close()
        time.sleep(10)
    try:
        file = open('config.json', 'r')
        config = json.loads(file.read())
        RPC = config['RPC']
        privateKey = config['privateKey']
        blocknativeKey = config['blocknativeKey']
        barkKey = config['barkKey']
        follows = config['follow']
        w3 = Web3(Web3.HTTPProvider(RPC))
        maxGasPrice = config['maxGasPrice']
        maxGasPrice = w3.toWei(maxGasPrice, 'gwei')
        maxGasLimit = int(config['maxGasLimit'])
        chainId = w3.eth.chainId
        account = w3.eth.account.privateKeyToAccount(privateKey)
        mintadd = []
        methodNameList = {}
        main()
    except Exception as e:
        print_red(str(e))
        time.sleep(10)
