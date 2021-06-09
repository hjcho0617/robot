import serial
import time
import signal
import threading
import datetime
import platform

line = []

sys = platform.system()
if sys == "Windows":
    port = "COM6"
elif sys == "Linux":
    port = "/dev/ttyUSB0"
baud = 19200

sndData = [0xAF, 0xFA, 0x60, 0x05, 0x01, 0x60, 0x45, 0x00, 0x0B, 0xAF, 0xA0]

exitThread = False

max_batt = 28.8    #  max : 29.4
min_batt = 23.1

volt = 0.00
temp = 0.0
bat = 0

# Error code
LENGTH_ERROR = 0x01
COMMAND_ERROR = 0x02
ORDER_ERROR = 0x04
CHECKSUM_ERROR = 0x08


def checksum(packet):
    sum = 0
    for i in packet:
        sum += i
    sum = sum & 0xFF
    return sum


def handler(signum, frame):
    exitThread = True


def parsing_data(data):
    global volt, temp, bat
    print("Response packet:", str.join("", ("0x%02X " % i for i in data)))
    # Start Sentence
    if data[0] == 0xAF and data[1] == 0xFA:
        # Checksum
        if data[-3] != checksum(data[2:-3]):
            print("checksum: %s, %s" % (data[-3], checksum(data[2:-3])))
            print("Not matching Checksum")
            return
        # Address
        if data[2] != 0x60:
            print("Not matching Address")
            return
        # Length and Command
        if data[3] == 0x09 and data[4] == 0x03:
            # voltage
            volt = (int(data[6] << 8) + int(data[7])) / 100
            '''
            if volt > 29.4:
                volt = 29.4
            elif volt < 23.1:
                volt = 23.1
            # Battery percent
            bat = int(round(((volt - min_batt) / (max_batt - min_batt)) * 100, 0))
            if bat > 100:
                bat = 100
            elif bat < 0:
                bat = 0
            '''
            bat = (int(data[8] << 8) + int(data[9]))
            # Temperature
            temp = (int(data[10] << 8) + int(data[11])) / 10
            print("Volt:%s V, Batt:%s %%, Temp:%s 'C" % (volt, bat, temp))
        elif data[3] == 0x07 and data[4] == 0x1F:
            if data[5] & LENGTH_ERROR:
                print("Length Error!!")
            if data[5] & COMMAND_ERROR:
                print("Command Error!!")
            if data[5] & ORDER_ERROR:
                print("Order Error!!")
            if data[5] & CHECKSUM_ERROR:
                print("Checksum Error!!")
    else:
        print("Packet Error!!")
        return


def readThread(ser):
    global line
    global sndData
    global exitThread

    while not exitThread:
        try:
            t = time.time()
            sndData[8] = checksum(sndData[2:-3])
            ser.write(bytearray(sndData))
            time.sleep(0.04)
            for c in ser.read():
                line.append(c)
                # End Sentence
                if c == 0xA0 and line[-2] == 0xAF:
                    parsing_data(line)
                    del line[:]
                    print(datetime.datetime.now(), "tick:", round(time.time() - t, 4))
                    time.sleep(10)
        except:
            del line[:]


if __name__ == "__main__":
    # signal.signal(signal.SIGINT, handler)

    ser = serial.Serial(port, baud, timeout=1)
    print("### Battery Status Test ###\r\nCom Status:", ser.portstr, ser.is_open)
    print("Com BaudRate:", ser.baudrate)

    thread = threading.Thread(target=readThread, args=(ser,))
    thread.start()
