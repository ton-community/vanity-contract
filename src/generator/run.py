import pyopencl as cl
import numpy as np
import base64

device = cl.get_platforms()[0].get_devices()[2]
print(device.name)
context = cl.Context(devices=[device], dev_type=None)
queue = cl.CommandQueue(context)
program = cl.Program(context, open('vanity.cl').read()).build()

mf = cl.mem_flags

main = bytearray.fromhex('02013400010000ab385daef0ba67bf96a5dc2c6e2a48b4b0ccd17937748f030b998c6d6c19c0e7e502c2657462e3522b2515e4798636ff5967d5f1db1762053027528f3550ce4300')
data = np.frombuffer(main, dtype=np.uint32)
main_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, 72, hostbuf=data)

inner = bytearray.fromhex('008404007be1eadead05ee58294a07323e2d41d8c41b456f11e5c116ff93aec8ed311d9966af50c6685145280c287ea35c289ce100f0f791717e03ecb46e5011ea03dc7f')
inner_data = np.frombuffer(inner, dtype=np.uint32)
inner_g = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, 68, hostbuf=inner_data)

res = np.full(8, 0x00000000, np.uint32)
res_g = cl.Buffer(context, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=res)

program.hash_main(queue, (1000,), None, np.int32(10000), main_g, np.int32(71), inner_g, np.int32(68), res_g).wait()
result = np.empty(8, np.uint32)
cl.enqueue_copy(queue, result, res_g).wait()

print(base64.urlsafe_b64encode(b'\x11\x00' + result.tobytes()))
