# Test file, all tests **must** be deleted before commiting/pushing. This file can be used to test out functions if you don't want to test them out using the commands.
import numpy as np
import numpy
import time
st = time.time()

x = np.arange(2400).reshape(5,6,8,10)
print(np.sum(x, axis=(0, 1)).shape)
