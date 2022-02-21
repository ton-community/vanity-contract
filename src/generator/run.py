import hashlib
import pyopencl as cl
import numpy as np
import base64
import time
import os
import argparse

parser = argparse.ArgumentParser('vanity-generator', description='Generate beautiful wallet for TON on GPU using vanity contract')
parser.add_argument('owner', help='An owner of vanity contract')
parser.add_argument('--end', type=str, default='', help='Search in the end of address')
parser.add_argument('--start', type=str, default='', help='Search in the start of address')
parser.add_argument('-nb', action='store_true', default=False, help='Search for non-bouncable addresses')
parser.add_argument('-t', action='store_true', default=False, help='Search for testnet addresses')
parser.add_argument('-w', type=int, required=True, help='Address workchain')
parser.add_argument('--case-sensitive', action='store_true', help='Search for case sensitive address (case insensitive by default)')


args = parser.parse_args()
if not args.end and not args.start:
    parser.print_usage()
    print('vanity-generator: error: the following arguments are required: end or start')
    os._exit(0)


OWNER = args.owner
owner_decoded = base64.urlsafe_b64decode(OWNER)
inner_base =  bytearray.fromhex('00840400') + owner_decoded[2:34]

BOUNCEABLE_TAG = 0x11
NON_BOUNCEABLE_TAG = 0x51
TEST_FLAG = 0x80
WORKCHAIN = (args.w + (1 << 8)) % (1 << 8)

flags = (NON_BOUNCEABLE_TAG if args.nb else BOUNCEABLE_TAG)
if args.t:
    flags |= TEST_FLAG
flags <<= 8
flags |= WORKCHAIN

if not args.case_sensitive:
    args.start = args.start.lower()
    args.end = args.end.lower()

conditions = []
kernel_conditions = []
if args.case_sensitive:
    conditions.append('case-sensitive')
if args.start:
    conditions.append(f'starting with "{args.start}"')
    for i, c in enumerate(args.start):
        pos = i + 3
        if args.case_sensitive:
            kernel_conditions.append(f"result[{pos}] == '{c}'")
        else:
            kernel_conditions.append(f"(result[{pos}] == '{c}' || result[{pos}] == '{c.upper()}')")
if args.end:
    conditions.append(f'with "{args.end}" in the end')
    for i, c in enumerate(args.end):
        pos = 47 - len(args.end) + i + 1
        if args.case_sensitive:
            kernel_conditions.append(f"result[{pos}] == '{c}'")
        else:
            kernel_conditions.append(f"(result[{pos}] == '{c}' || result[{pos}] == '{c.upper()}')")

print()
print('Searching wallets', ', '.join(conditions))
print("Owner: ", OWNER)
print("Flags: ", flags.to_bytes(2, 'big').hex())
print("Kernel conditions:", ' && '.join(kernel_conditions))
print()


device = cl.get_platforms()[0].get_devices()[2]
print("Using device: ", device.name)
context = cl.Context(devices=[device], dev_type=None)
queue = cl.CommandQueue(context)

kernel_code = open(os.path.join(os.path.dirname(__file__), 'vanity.cl')).read()
kernel_code = kernel_code.replace("<<CONDITION>>", ' && '.join(kernel_conditions))
program = cl.Program(context, kernel_code).build()

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

def solver():
    main = bytearray.fromhex('02013400010000ab385daef0ba67bf96a5dc2c6e2a48b4b0ccd17937748f030b998c6d6c19c0e7e502c2657462e3522b2515e4798636ff5967d5f1db1762053027528f3550ce4300')
    data = np.frombuffer(main, dtype=np.uint32)
    main_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, 72, hostbuf=data)

    salt = bytearray(os.urandom(32))
    inner = inner_base + salt
    inner_data = np.frombuffer(inner, dtype=np.uint32)
    inner_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, 68, hostbuf=inner_data)

    res = np.full(2048, 0xffffffff, np.uint32)
    res_g = cl.Buffer(context, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=res)

    end = np.frombuffer((args.end or '\0').encode('utf-8'), dtype=np.byte)
    end_g = cl.Buffer(context,  mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=end)
    start = np.frombuffer((args.start or '\0').encode('utf-8'), dtype=np.byte)
    start_g = cl.Buffer(context,  mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=start)

    start = time.time()
    threads = 10000
    iterations = 10000
    program.hash_main(
        queue, 
        (threads,), 
        None, 
        np.int32(iterations),
        np.ushort(flags),
        np.int32(71),
        main_g,
        np.int32(68),
        inner_g, 
        res_g
    ).wait()
    result = np.empty(2048, np.uint32)
    cl.enqueue_copy(queue, result, res_g).wait()
    
    ps = list(np.where(result != 0xffffffff))[0]
    misses = 0
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
            address += flags.to_bytes(2, 'big') # flags
            address += hs
            address += b'\x00\x00'
            crc = crc16(address)
            address[34] = crc[0]
            address[35] = crc[1]
            found = base64.urlsafe_b64encode(address).decode('utf-8')
            if (len(args.end) > 0 and found.lower().endswith(args.end.lower())) or (len(args.start) > 0 and found[3:].lower().startswith(args.start.lower())):
                print('Found: ', found, 'salt: ', salt_np.tobytes().hex())
            else:
                misses += 1
    print('Speed:', round(threads * iterations / (time.time() - start) / 1e6), 'Mh/s, miss:', misses) 


while True:
    solver()
