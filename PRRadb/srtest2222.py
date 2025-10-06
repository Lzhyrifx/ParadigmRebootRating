





cmd = []
cmd.append('adb')
device = sqlite.get_device()
if not device is None:
    cmd.append('-s')
    cmd.append(device)
cmd.append('shell')
cmd.append('screencap')
cmd.append('-p')
print(cmd, end='...')
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
# p.wait()
output = p.communicate()[0]
# print(output)
size = len(output)
print('size', size)
# file = open(tmp, 'rb')
w = open(path, 'wb')
find = False
c = 0
for i in range(size):
    data = output[i].to_bytes(1, byteorder='little', signed=False)  # file.read(1)
    if c < 10:
        print(data, end=' ')
    c += 1
    if data == '': break
    if find:
        if data != b'\n':
            w.write(b'\r')
        find = False

    if data == b'\r':
        find = True
        continue
    w.write(data)
w.close()