"""Run against a flashed STM32: python test_serial.py COM5"""
import sys
import time
import serial

def check(port, command, expected):
    port.write((command + "\n").encode("ascii"))
    reply = port.readline().decode("ascii").strip()
    assert reply == expected, f"{command!r}: {reply!r} != {expected!r}"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python test_serial.py COM5")
    with serial.Serial(sys.argv[1], 115200, timeout=2) as port:
        time.sleep(.2)
        port.reset_input_buffer()
        check(port, "CONNECT", "OK")
        check(port, "DISCONNECT", "OK")
        check(port, "NEW", "OK:BOARD:.........")
        check(port, "MOVE:0:O", "NACK:NOTURN")
        check(port, "MOVE:9:X", "NACK:RANGE")
        check(port, "MOVE:0:X", "OK:BOARD:X........")
        check(port, "MOVE:0:O", "NACK:OCCUPIED")
        check(port, "STATE", "BOARD:X........")
        check(port, "MOVE:3:O", "OK:BOARD:X..O.....")
        check(port, "MOVE:1:X", "OK:BOARD:XX.O.....")
        check(port, "MOVE:4:O", "OK:BOARD:XX.OO....")
        check(port, "MOVE:2:X", "WIN:X:XXXOO....")
        check(port, "MOVE:5:O", "NACK:NOGAME")
        check(port, "NEW", "OK:BOARD:.........")
        check(port, "RESIGN", "OK:GAMEOVER")
        check(port, "DISCONNECT", "OK")
        port.write(b"MOVE:0:X")
        time.sleep(.7)
        assert port.readline().decode().strip() == "NACK:TIMEOUT"
        port.write(b"A" * 32 + b"\n")
        assert port.readline().decode().strip() == "NACK:BADCMD"
        print("Hardware UART integration tests passed")
