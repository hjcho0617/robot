
def checksum(packet):
    sum = 0
    for i in packet:
        sum += i
    sum = sum & 0xFF
    print(sum)
    return sum



