import { Cell, toNano, StateInit, Address, contractAddress } from 'ton';
import fs from 'fs';
import qs from 'qs';

const contractCode = Cell.fromBoc(fs.readFileSync(__dirname + '/vanity-address.cell'))[0];
const salt = Buffer.from('546b0298521c095a2b125870d0219215944802604a87efa019d096254df4f315', 'hex');
const owner = Address.parseFriendly('kQB74ererQXuWClKBzI-LUHYxBtFbxHlwRb_k67I7TEdmThB').address
const contractData = new Cell();
contractData.bits.writeInt(0, 5); // padding
contractData.bits.writeAddress(owner); // owner
contractData.bits.writeBuffer(salt); // salt
let init = new Cell();
new StateInit({
    code: contractCode,
    data: contractData
}).writeTo(init);
let address = contractAddress({
    workchain: 0,
    initialCode: contractCode,
    initialData: contractData
})

let newCode = Cell.fromBoc(fs.readFileSync('./code.cell'))[0];
let newData = Cell.fromBoc(fs.readFileSync('./data.cell'))[0];

let payload = new Cell();
payload.withReference(newCode);
payload.withReference(newData);

let link = 'https://test.tonhub.com/transfer/' + address.toFriendly({ testOnly: true }) + '?' + qs.stringify({
    text: 'Deploy contract',
    amount: toNano(0.01).toString(10),
    init: init.toBoc({ idx: false }).toString('base64'),
    bin: payload.toBoc({ idx: false }).toString('base64')
});

console.log(link);
