import serial

PORT = "/dev/tty.usbmodem5AE60584321"
BAUD = 1_000_000


# ┌─────────┬────────┬────────┬─────┬─────┬───────┬──────┬──────┬──────────┐
# │  index  │   0    │   1    │  2  │  3  │   4   │  5   │  6   │    7     │
# ├─────────┼────────┼────────┼─────┼─────┼───────┼──────┼──────┼──────────┤
# │ byte    │ FF     │ FF     │ 01  │ 04  │ 00    │ 00   │ 08   │ F2       │
# ├─────────┼────────┼────────┼─────┼─────┼───────┼──────┼──────┼──────────┤
# │ meaning │ header │ header │ ID  │ LEN │ ERROR │ data │ data │ checksum │
# └─────────┴────────┴────────┴─────┴─────┴───────┴──────┴──────┴──────────┘



def checksum(body: bytes) -> int:
    """~(sum of body bytes) & 0xFF"""
    ...
    return (~sum(body)) & 0xFF

def make_packet(motor_id: int, instruction: int, params: bytes = b"") -> bytes:
    """FF FF  ID  LEN  INSTR  PARAMS  CHK     (LEN = len(params) + 2)"""
    ...
    body = [motor_id, len(params) + 2, instruction]  + list(params)
    checksum_value =  checksum(body=body)   
    packet = bytes([0xFF, 0xFF] + body + [checksum_value]) 
    return packet


#  body = [motor_id, len(params) + 2, instruction] + list(params)


def parse_reply(raw: bytes, expected_id: int) -> bytes:
    """Check FF FF ID LEN ERR PARAMS CHK. Return PARAMS, or raise ValueError if anything is wrong."""
    if len(raw) < 6:                        
        raise ValueError("reply too short")
    
    if raw[0] != 0xFF or raw[1] != 0xFF:
        raise ValueError("Headers corrupted")

    if len(raw) != 4 + raw[3]:
        raise ValueError("Length of the packet error")

    if checksum(raw[2:-1]) != raw[-1]:
        raise ValueError("Checksum error")

    if raw[4] != 0:
        raise ValueError("Error byte")
    
    if raw[2] != expected_id:
        raise ValueError("Wrong ID received")

    return raw[5:-1]

def send(ser, motor_id, instruction, params=b""):
    ser.reset_input_buffer()
    
    packet = make_packet(motor_id=motor_id, instruction=instruction, params=params)
    ser.write(packet)

    #  Replies have different lengths -> ping (6 bytes), read position (8 bytes) etc
    reply_first_half = ser.read(4) # Expected :-  FF FF ID LEN 

    if len(reply_first_half) < 4:
        return None
    
    # print(reply_first_half)
    # get the packet size from it's encoded info itself
    rest_bytes = ser.read(reply_first_half[3])

    raw = reply_first_half + rest_bytes

    if len(rest_bytes) < reply_first_half[3]:
        return None #timeout
    
    return parse_reply(raw=raw, expected_id=motor_id)

def ping(ser, motor_id):
    reply = send(ser=ser, motor_id=motor_id, instruction=0x01)
    # if reply:
    #     return True
    return reply is not None

def read_position(ser, motor_id):

    data = send(ser, motor_id=motor_id, instruction=0x02,  params=bytes([56, 2])) # read box 56 and 2 bytes form there for the pos 
    if data is None:
        return None
    
    # print(data)
    return int.from_bytes(data, "little") # little -> reads in reverse order , ir 00 08 becomes 2048 and not 8 -> the right way



if __name__ == "__main__":
    assert checksum(bytes([1, 2, 1])) == 0xFB  # PING motor 1
    assert checksum(bytes([6, 2, 1])) == 0xF6        # PING motor 6 
    assert make_packet(1, 0x01) == bytes.fromhex("FFFF010201FB")    # PING motor 1
    assert make_packet(6, 0x01) == bytes.fromhex("FFFF060201F6")   # PING motor 6
    assert make_packet(1, 0x02, bytes([56, 2])) == bytes.fromhex("FFFF0104023802BE")
    print("all checks passed")