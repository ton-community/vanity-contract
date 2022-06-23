import { Cell, StateInit, Address } from 'ton';
import fs from 'fs';

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

console.log(getRepr(init).toString('hex'));