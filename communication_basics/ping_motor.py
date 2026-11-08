import serial                                             

ser = serial.Serial("/dev/tty.usbmodem5AE60584321", 1_000_000, timeout=0.5)   
packet = bytes([0xFF, 0xFF, 0x01, 0x02, 0x01, 0xFB])       # PING packet for motor ID 1 

# print("Sending packet...")
# ser.write(packet)                                         
# print(ser.read())
# print(ser.read(12).hex(" "))  


#Packet : FF FF   01   02   01   FB
#         header  ID   LEN  INSTR CHECKSUM


for i in range(1,7):
    print(f"Sending packet to motor : {i} ")

    body = [i, 0x02, 0x01]            # ID, length, instruction (1 instruction -> read/ping)
    checksum = (~sum(body)) & 0xFF    # add , flipping the bits and keep the low byte
    packet = bytes([0xFF, 0xFF] + body + [checksum])

    ser.write(packet)                                         
    print(f"Motor id : {i} replied with ", ser.read(12).hex(" ")) 
    print("\n")



