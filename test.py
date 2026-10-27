import serial
import time
import sys


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM6"

BAUD_RATE = 115200
READ_TIMEOUT = 2.0

passed = 0
failed = 0


# ------------------------------------------------------------
# Serial connection
# ------------------------------------------------------------

print("=" * 60)
print("STM32 SERIAL GAME SERVER TEST HARNESS")
print("=" * 60)
print(f"Port: {PORT}")
print(f"Baud: {BAUD_RATE}")
print()

try:
    ser = serial.Serial(
        PORT,
        baudrate=BAUD_RATE,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=READ_TIMEOUT,
        write_timeout=1
    )

except serial.SerialException as error:
    print(f"Could not open {PORT}: {error}")
    sys.exit(1)


time.sleep(0.2)

ser.reset_input_buffer()


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def send(command, show=True):
    """
    Send one newline-terminated command and return the STM32 response.
    """

    if show:
        print(f"TX: {command}")

    ser.write((command + "\n").encode("ascii"))
    ser.flush()

    response = ser.readline()

    if not response:
        result = "<NO RESPONSE>"
    else:
        result = response.decode("ascii", errors="replace").strip()

    if show:
        print(f"RX: {result}")

    return result


def expect(command, expected):
    """
    Send a command and check that its response exactly matches expected.
    """

    global passed, failed

    actual = send(command)

    if actual == expected:
        print("PASS\n")
        passed += 1
        return True

    print("FAIL")
    print(f"Expected: {expected}")
    print(f"Actual:   {actual}")
    print()

    failed += 1

    return False


def check_response(actual, expected, description):
    """
    Check a response that was obtained manually rather than through expect().
    """

    global passed, failed

    print(description)
    print(f"Expected: {expected}")
    print(f"Actual:   {actual}")

    if actual == expected:
        print("PASS\n")
        passed += 1
        return True

    print("FAIL\n")
    failed += 1

    return False


def section(name):
    print()
    print("=" * 60)
    print(name)
    print("=" * 60)
    print()


def normalise_server():
    """
    Try to put the STM32 into:
        connected = True
        state = IDLE

    This works whether the previous test ended in:
        IDLE
        IN_PROGRESS
        GAME_OVER
        disconnected
    """

    # Ignore these responses.
    send("RESIGN", show=False)
    send("DISCONNECT", show=False)

    response = send("CONNECT", show=False)

    if response != "OK":
        print(
            "WARNING: Could not normalise server. "
            f"CONNECT returned {response}"
        )

    # Remove any unexpected stale bytes.
    ser.reset_input_buffer()


# ------------------------------------------------------------
# TEST 1
# Connection and IDLE state
# ------------------------------------------------------------

section("TEST 1 - CONNECTION AND IDLE STATE")

normalise_server()

expect(
    "STATE",
    "NACK:NOGAME"
)


# ------------------------------------------------------------
# TEST 2
# NEW game
# ------------------------------------------------------------

section("TEST 2 - NEW GAME")

normalise_server()

expect(
    "NEW",
    "OK:BOARD:........."
)


# ------------------------------------------------------------
# TEST 3
# Official MOVE:<index> protocol
# ------------------------------------------------------------

section("TEST 3 - LEGAL MOVES USING MOVE:<index>")

normalise_server()

expect(
    "NEW",
    "OK:BOARD:........."
)

expect(
    "MOVE:0",
    "OK:BOARD:X........"
)

expect(
    "MOVE:1",
    "OK:BOARD:XO......."
)

expect(
    "STATE",
    "BOARD:XO......."
)


# ------------------------------------------------------------
# TEST 4
# Illegal moves and unchanged state
# ------------------------------------------------------------

section("TEST 4 - MOVE VALIDATION AND STATE PRESERVATION")

normalise_server()

expect(
    "NEW",
    "OK:BOARD:........."
)

expect(
    "MOVE:0:X",
    "OK:BOARD:X........"
)


# Occupied cell
expect(
    "MOVE:0:O",
    "NACK:OCCUPIED"
)

# Board must be unchanged
expect(
    "STATE",
    "BOARD:X........"
)


# Out-of-range cell
expect(
    "MOVE:9:O",
    "NACK:RANGE"
)

# Board must still be unchanged
expect(
    "STATE",
    "BOARD:X........"
)


# Wrong player
expect(
    "MOVE:1:X",
    "NACK:NOTURN"
)

# Board must still be unchanged
expect(
    "STATE",
    "BOARD:X........"
)


# Correct player
expect(
    "MOVE:1:O",
    "OK:BOARD:XO......."
)


# NEW should not be allowed during a game
expect(
    "NEW",
    "NACK:BADSTATE"
)


# CONNECT should not restart an active game
expect(
    "CONNECT",
    "NACK:BADSTATE"
)


# DISCONNECT should not be allowed during a game
expect(
    "DISCONNECT",
    "NACK:BADSTATE"
)


# ------------------------------------------------------------
# TEST 5
# X win
# ------------------------------------------------------------

section("TEST 5 - WIN DETECTION")

normalise_server()

expect(
    "NEW",
    "OK:BOARD:........."
)

expect(
    "MOVE:0:X",
    "OK:BOARD:X........"
)

expect(
    "MOVE:1:O",
    "OK:BOARD:XO......."
)

expect(
    "MOVE:3:X",
    "OK:BOARD:XO.X....."
)

expect(
    "MOVE:4:O",
    "OK:BOARD:XO.XO...."
)

expect(
    "MOVE:6:X",
    "WIN:X:XO.XO.X.."
)


# STATE must still return the final board
expect(
    "STATE",
    "BOARD:XO.XO.X.."
)


# No more moves after game over
expect(
    "MOVE:2:O",
    "NACK:NOGAME"
)


# NEW must work after game over
expect(
    "NEW",
    "OK:BOARD:........."
)


# ------------------------------------------------------------
# TEST 6
# Draw detection
# ------------------------------------------------------------

section("TEST 6 - DRAW DETECTION")

normalise_server()

expect(
    "NEW",
    "OK:BOARD:........."
)

# Final board:
#
# X O X
# X O O
# O X X

expect(
    "MOVE:0",
    "OK:BOARD:X........"
)

expect(
    "MOVE:1",
    "OK:BOARD:XO......."
)

expect(
    "MOVE:2",
    "OK:BOARD:XOX......"
)

expect(
    "MOVE:4",
    "OK:BOARD:XOX.O...."
)

expect(
    "MOVE:3",
    "OK:BOARD:XOXXO...."
)

expect(
    "MOVE:5",
    "OK:BOARD:XOXXOO..."
)

expect(
    "MOVE:7",
    "OK:BOARD:XOXXOO.X."
)

expect(
    "MOVE:6",
    "OK:BOARD:XOXXOOOX."
)

expect(
    "MOVE:8",
    "DRAW:XOXXOOOXX"
)


expect(
    "STATE",
    "BOARD:XOXXOOOXX"
)


expect(
    "MOVE:0",
    "NACK:NOGAME"
)


# ------------------------------------------------------------
# TEST 7
# RESIGN
# ------------------------------------------------------------

section("TEST 7 - RESIGN")

normalise_server()

expect(
    "NEW",
    "OK:BOARD:........."
)

expect(
    "MOVE:4:X",
    "OK:BOARD:....X...."
)

expect(
    "RESIGN",
    "OK:GAMEOVER"
)

expect(
    "STATE",
    "BOARD:....X...."
)

expect(
    "MOVE:0:O",
    "NACK:NOGAME"
)


# ------------------------------------------------------------
# TEST 8
# DISCONNECT and reconnect
# ------------------------------------------------------------

section("TEST 8 - DISCONNECT AND RECONNECT")

normalise_server()

expect(
    "DISCONNECT",
    "OK"
)


# Server should reject commands when disconnected.
expect(
    "STATE",
    "NACK:BADCMD"
)


expect(
    "CONNECT",
    "OK"
)


expect(
    "NEW",
    "OK:BOARD:........."
)


# ------------------------------------------------------------
# TEST 9
# Malformed and garbage commands
# ------------------------------------------------------------

section("TEST 9 - MALFORMED COMMANDS")

normalise_server()

expect(
    "HELLO",
    "NACK:BADCMD"
)


expect(
    "",
    "NACK:BADCMD"
)


expect(
    "NEW",
    "OK:BOARD:........."
)


expect(
    "MOVE:abc",
    "NACK:BADCMD"
)


expect(
    "MOVE:1:Q",
    "NACK:BADCMD"
)


expect(
    "MOVE:",
    "NACK:BADCMD"
)


# Verify garbage commands did not modify the board.
expect(
    "STATE",
    "BOARD:........."
)


# ------------------------------------------------------------
# TEST 10
# Oversized frame
# ------------------------------------------------------------

section("TEST 10 - OVERSIZED FRAME")

normalise_server()

expect(
    "NEW",
    "OK:BOARD:........."
)


oversized = "A" * 100

print(f"TX: [100-character oversized frame]")

ser.write((oversized + "\n").encode("ascii"))
ser.flush()

response = ser.readline().decode(
    "ascii",
    errors="replace"
).strip()

print(f"RX: {response}")

check_response(
    response,
    "NACK:BADCMD",
    "Oversized frame rejection"
)


# Make sure the parser recovered after the oversized frame.
expect(
    "STATE",
    "BOARD:........."
)


# ------------------------------------------------------------
# TEST 11
# Partial frame timeout
# ------------------------------------------------------------

section("TEST 11 - INCOMPLETE FRAME TIMEOUT")

normalise_server()

expect(
    "NEW",
    "OK:BOARD:........."
)


print("TX: STA   (no newline)")

ser.write(b"STA")
ser.flush()


# STM32 timeout is currently 1000 ms.
time.sleep(1.3)


response = ser.readline().decode(
    "ascii",
    errors="replace"
).strip()

print(f"RX: {response}")


check_response(
    response,
    "NACK:TIMEOUT",
    "Incomplete frame timeout"
)


# Verify the parser recovered afterwards.
expect(
    "STATE",
    "BOARD:........."
)


# ------------------------------------------------------------
# TEST 12
# CRLF support
# ------------------------------------------------------------

section("TEST 12 - CRLF TERMINATION")

normalise_server()


print(r"TX: NEW\r\n")

ser.write(b"NEW\r\n")
ser.flush()

response = ser.readline().decode(
    "ascii",
    errors="replace"
).strip()

print(f"RX: {response}")


check_response(
    response,
    "OK:BOARD:.........",
    "CRLF command termination"
)


# ------------------------------------------------------------
# TEST 13
# Final connection recovery
# ------------------------------------------------------------

section("TEST 13 - FINAL RECOVERY CHECK")

# End current game.
expect(
    "RESIGN",
    "OK:GAMEOVER"
)

expect(
    "DISCONNECT",
    "OK"
)

expect(
    "CONNECT",
    "OK"
)

expect(
    "NEW",
    "OK:BOARD:........."
)


# ------------------------------------------------------------
# Results
# ------------------------------------------------------------

section("TEST RESULTS")

total = passed + failed

print(f"Total tests: {total}")
print(f"Passed:      {passed}")
print(f"Failed:      {failed}")

print()


ser.close()


if failed == 0:
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)

    sys.exit(0)

else:
    print("=" * 60)
    print("SOME TESTS FAILED")
    print("=" * 60)

    sys.exit(1)