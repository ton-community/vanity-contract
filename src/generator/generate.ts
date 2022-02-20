import { Address, Cell, StateInit } from 'ton';
import fs from 'fs'
import { randomBytes } from 'crypto';

let addressesCount = 0
setInterval(() => {
    console.log('addresses per second: ', addressesCount / 5)
    addressesCount = 0
}, 5000)

setInterval(() => {
    const contractCode = Cell.fromBoc(fs.readFileSync(__dirname + '/../contract/vanity-address.cell'))[0];
const contractData = new Cell();
const salt = randomBytes(10);
const owner = Address.parseFriendly('EQB74ererQXuWClKBzI-LUHYxBtFbxHlwRb_k67I7TEdmYPL').address
contractData.bits.writeAddress(owner)
contractData.bits.writeBuffer(salt);
let init = new Cell();
new StateInit({
    code: contractCode,
    data: contractData
}).writeTo(init);
let address = new Address(0, init.hash());
if (address.toFriendly().toLowerCase().endsWith('hale')) {
    console.log(salt.toString('hex'), address.toFriendly())
}
addressesCount++
}, 0)