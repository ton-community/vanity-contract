import hashlib
import pyopencl as cl
import numpy as np
import base64
import time
import os

device = cl.get_platforms()[0].get_devices()[2]
print(device.name)
context = cl.Context(devices=[device], dev_type=None)
queue = cl.CommandQueue(context)
program = cl.Program(context, open('vanity.cl').read()).build()

mf = cl.mem_flags

def crc16(data):
    reg = 0
    for b in data:
        mask = 0x80
        while mask > 0:
            reg <<= 1
            if b & mask:
                reg = reg + 1
            mask >>= 1
            if reg > 0xffff:
                reg = reg & 0xffff
                reg ^= 0x1021
    return reg.to_bytes(2, byteorder='big')

OWNER = 'EQB74ererQXuWClKBzI-LUHYxBtFbxHlwRb_k67I7TEdmYPL'
owner_decoded = base64.urlsafe_b64decode(OWNER)
inner_base =  bytearray.fromhex('00840400') + owner_decoded[2:34]

def solver():
    main = bytearray.fromhex('02013400010000ab385daef0ba67bf96a5dc2c6e2a48b4b0ccd17937748f030b998c6d6c19c0e7e502c2657462e3522b2515e4798636ff5967d5f1db1762053027528f3550ce4300')
    data = np.frombuffer(main, dtype=np.uint32)
    main_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, 72, hostbuf=data)

    salt = bytearray(os.urandom(32))
    inner = inner_base + salt
    inner_data = np.frombuffer(inner, dtype=np.uint32)
    inner_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, 68, hostbuf=inner_data)

    res = np.full(256, 0xffffffff, np.uint32)
    res_g = cl.Buffer(context, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=res)

    start = time.time()
    threads = 10000
    iterations = 10000
    program.hash_main(queue, (threads,), None, np.int32(iterations), main_g, np.int32(71), inner_g, np.int32(68), res_g).wait()
    result = np.empty(256, np.uint32)
    cl.enqueue_copy(queue, result, res_g).wait()

    print('Speed: ', threads * iterations / (time.time() - start) / 1e6, 'Mh/s') 
    
    ps = list(np.where(result != 0xffffffff))[0]
    if len(ps):
        for j in range(0, len(ps), 2):
            p = ps[j]
            assert ps[j + 1] == p + 1
            a = result[p]
            b = result[p+1]

            salt_np = np.frombuffer(salt, np.uint32)
            salt_np[0] ^= a
            salt_np[1] ^= b
            hdata1 = inner_base + salt_np.tobytes()
            hash1 = hashlib.sha256(hdata1).digest()
            main[39:71] = hash1

            hs = hashlib.sha256(main[:71]).digest()
    
            address = bytearray()
            address += b'\x11\x00'
            address += hs
            address += b'\x00\x00'
            crc = crc16(address)
            address[34] = crc[0]
            address[35] = crc[1]
            found = base64.urlsafe_b64encode(address)
            if found.lower().endswith(b'whales'):
                print('Found: ', str(found), 'salt: ', salt_np.tobytes().hex())
            else:
                print('Miss: ', str(found), 'salt: ', salt_np.tobytes().hex())


while True:
    solver()
