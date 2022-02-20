import { Cell, toNano, StateInit, Address, WalletV3R2Source, TonClient, WalletContract, InternalMessage, CommonMessageInfo, CommentMessage } from 'ton';
import { mnemonicToWalletKey } from 'ton-crypto'
import fs from 'fs';
import qs from 'qs';
import qrcode from 'qrcode-terminal';


//
// Hash Content
//

function getMaxDepth(cell: Cell) {
    let maxDepth = 0;
    if (cell.refs.length > 0) {
        for (let k in cell.refs) {
            const i = cell.refs[k];
            if (getMaxDepth(i) > maxDepth) {
                maxDepth = getMaxDepth(i);
            }
        }
        maxDepth = maxDepth + 1;
    }
    return maxDepth;
}

function getMaxDepthAsArray(cell: Cell) {
    const maxDepth = getMaxDepth(cell);
    const d = Uint8Array.from({ length: 2 }, () => 0);
    d[1] = maxDepth % 256;
    d[0] = Math.floor(maxDepth / 256);
    return Buffer.from(d);
}

function getMaxLevel(cell: Cell) {
    //TODO level calculation differ for exotic cells
    let maxLevel = 0;
    for (let k in cell.refs) {
        const i = cell.refs[k];
        if (getMaxLevel(i) > maxLevel) {
            maxLevel = getMaxLevel(i);
        }
    }
    return maxLevel;
}

function getRefsDescriptor(cell: Cell) {
    const d1 = Uint8Array.from({ length: 1 }, () => 0);
    d1[0] = cell.refs.length + (cell.isExotic ? 1 : 0) * 8 + getMaxLevel(cell) * 32;
    return Buffer.from(d1);
}

/**
 * @return {Uint8Array}
 */
function getBitsDescriptor(cell: Cell) {
    const d2 = Uint8Array.from({ length: 1 }, () => 0);
    d2[0] = Math.ceil(cell.bits.cursor / 8) + Math.floor(cell.bits.cursor / 8);
    return Buffer.from(d2);
}

/**
 * @return {Uint8Array}
 */
function getDataWithDescriptors(cell: Cell) {
    const d1 = getRefsDescriptor(cell);
    const d2 = getBitsDescriptor(cell);
    const tuBits = cell.bits.getTopUppedArray();
    return Buffer.concat([d1, d2, tuBits]);
}

function getRepr(cell: Cell) {
    const reprArray: Buffer[] = [];
    reprArray.push(getDataWithDescriptors(cell));
    for (let k in cell.refs) {
        const i = cell.refs[k];
        reprArray.push(getMaxDepthAsArray(i));
    }
    for (let k in cell.refs) {
        const i = cell.refs[k];
        reprArray.push(i.hash());
    }
    let x = Buffer.alloc(0);
    for (let k in reprArray) {
        const i = reprArray[k];
        x = Buffer.concat([x, i]);
    }
    return x;
}


const contractCode = Cell.fromBoc(fs.readFileSync(__dirname + '/vanity-address.cell'))[0];
const contractData = new Cell();
const salt = Buffer.from('1c85f256c6d974818d6e', 'hex');
const owner = Address.parseFriendly('EQB74ererQXuWClKBzI-LUHYxBtFbxHlwRb_k67I7TEdmYPL').address
contractData.bits.writeAddress(owner)
contractData.bits.writeBuffer(salt);
let init = new Cell();
new StateInit({
    code: contractCode,
    data: contractData
}).writeTo(init);
let address = new Address(0, init.hash());
console.log(getRepr(contractData).toString('hex'))
console.log(salt.toString('hex'));
console.log(address.toFriendly(), address.toString());
let link = 'https://test.tonhub.com/transfer/' + address.toFriendly() + '?' + qs.stringify({
    text: 'Deploy contract',
    amount: toNano(0.01).toString(10),
    init: init.toBoc({ idx: false }).toString('base64')
});
console.log('Deploy: ' + link);
qrcode.generate(link, { small: true }, (code) => {
    console.log(code)
})

console.log('\n===========================================================\n');

(async () => {
    let mnemonic = [
        'anchor', 'patient', 'shadow',
        'spell',  'balcony', 'develop',
        'point',  'achieve', 'peanut',
        'wonder', 'amateur', 'easily',
        'token',  'dance',   'year',
        'lake',   'soft',    'predict',
        'word',   'tell',    'escape',
        'dream',  'defy',    'loan'
    ];
    let key = await mnemonicToWalletKey(mnemonic, '');
    let source = WalletV3R2Source.create({ workchain: 0, publicKey: key.publicKey })
    let data = new Cell()
    data.refs.push(source.initialCode)
    data.refs.push(source.initialData)
    link = 'https://test.tonhub.com/transfer/' + address.toFriendly() + '?' + qs.stringify({
        text: 'Redeploy conract',
        amount: toNano(0.01).toString(10),
        bin: data.toBoc({ idx: false }).toString('base64')
    });
    console.log('Redeploy: ' + link)
    qrcode.generate(link, { small: true }, (code) => {
        console.log(code)
    })


    // console.log('send coins back...')
    // let client = new TonClient({
    //     endpoint: 'https://testnet.tonhubapi.com/jsonRPC'
    // })

    // let contract = new WalletContract(client, source, address)
    // let transfer = contract.createTransfer({
    //     seqno: await contract.getSeqNo(),
    //     secretKey: key.secretKey,
    //     sendMode: 0,
    //     order: new InternalMessage({
    //         to: owner,
    //         value: toNano(0.01),
    //         bounce: false,
    //         body: new CommonMessageInfo({ body: new CommentMessage('kek') })
    //     })
    // })
    // client.sendExternalMessage(contract, transfer)
})()


