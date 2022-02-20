import pyopencl as cl
import numpy as np
import hashlib 

device = cl.get_platforms()[0].get_devices()[2]
print(device.name)
context = cl.Context(devices=[device], dev_type=None)
queue = cl.CommandQueue(context)
program = cl.Program(context, open('vanity.cl').read()).build()

mf = cl.mem_flags

main = bytearray.fromhex('020134000200003227043a3252738df0b6ba13a792a928b752324c1019b74f8e21468b007466bcf7ab28519389b0ac09c63e70f9f11fdae9f0a4e29d6914891ba0a71486c4936800')
data = np.frombuffer(main, dtype=np.uint32)
main_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, 72, hostbuf=data)

inner = bytearray.fromhex('0057800f7c3d5bd5a0bdcb052940e647c5a83b188368ade23cb822dff275d91da623b32390be4ad8db2e9031add00000')
inner_data = np.frombuffer(inner, dtype=np.uint32)
inner_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, 48, hostbuf=inner_data)

res = np.full(8, 0x00000000, np.uint32)
res_g = cl.Buffer(context, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=res)

program.hash_main(queue, (1,), None, np.int32(1), main_g, np.int32(71), inner_g, np.int32(46), res_g).wait()
result = np.empty(8, np.uint32)
cl.enqueue_copy(queue, result, res_g).wait()

print(hashlib.sha256(main[:71]).hexdigest(), result.tobytes().hex())

assert hashlib.sha256(main[:71]).hexdigest() == result.tobytes().hex()
