"""
Serial client for the EEE3095S Serial Game Server.

Serial settings: 115200 baud, 8 data bits, no parity, 1 stop bit (8N1).

The STM32 firmware is not available yet, so real game communication
has not been tested.
"""

import time

import serial
from serial.tools import list_ports


BAUD_RATE = 115200
READ_TIMEOUT = 3.0
WRITE_TIMEOUT = 1.0


def available_ports():
    """Return the serial ports detected by the computer."""
    return [
        (port.device, port.description)
        for port in list_ports.comports()
    ]


class SerialGameClient:
    """Send commands to the STM32 and receive response lines."""

    def __init__(self, port, timeout=READ_TIMEOUT):
        self.port = port
        self.timeout = timeout
        self.connection = None

    @property
    def is_connected(self):
        """Check whether the serial port is open."""
        return (
            self.connection is not None
            and self.connection.is_open
        )

    def open(self):
        """Open the serial connection."""
        if self.is_connected:
            return

        try:
            self.connection = serial.serial_for_url(
                self.port,
                baudrate=BAUD_RATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                write_timeout=WRITE_TIMEOUT,
            )

            # Allow the board time to initialise after opening.
            time.sleep(0.1)

            # Discard old data already waiting in the receive buffer.
            self.connection.reset_input_buffer()

            print(f"Connected to serial port {self.port}.")

        except serial.SerialException as error:
            self.connection = None
            raise ConnectionError(
                f"Could not open {self.port}. "
                "Check the port and close other serial programs."
            ) from error

    def send_command(self, command):
        """
        Send one command followed by a newline.
        Return the response without its newline characters.
        """
        if not self.is_connected:
            raise RuntimeError(
                "Serial port is not open. Call open() first."
            )

        if not isinstance(command, str):
            raise TypeError("Command must be a string.")

        if not command or not command.strip():
            raise ValueError("Command cannot be empty.")

        if "\n" in command or "\r" in command:
            raise ValueError(
                "Provide one command without a newline."
            )

        try:
            data = command.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError(
                "Commands must contain ASCII characters only."
            ) from error

        try:
            self.connection.write(data + b"\n")
            self.connection.flush()

            response = self.connection.readline()

        except serial.SerialException as error:
            raise ConnectionError(
                f"Serial communication failed on {self.port}."
            ) from error

        if not response:
            raise TimeoutError(
                f"No response received from {self.port} "
                f"within {self.timeout} seconds."
            )

        try:
            return response.decode("ascii").rstrip("\r\n")
        except UnicodeDecodeError as error:
            raise ValueError(
                f"Received invalid response: {response!r}"
            ) from error

    def close(self):
        """Close the serial connection."""
        if self.connection is not None:
            if self.connection.is_open:
                self.connection.close()

            self.connection = None
            print("Serial connection closed.")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def main():
    """List ports and optionally test the STM32 connection."""
    ports = available_ports()

    if not ports:
        print("No serial ports detected.")
        return

    print("Available serial ports:")

    for device, description in ports:
        print(f"  {device}: {description}")

    port = input(
        "\nEnter the STM32 port (for example COM5), "
        "or press Enter to exit: "
    ).strip()

    if not port:
        return

    try:
        with SerialGameClient(port) as client:
            print("Sending CONNECT...")
            response = client.send_command("CONNECT")
            print("Response:", repr(response))

    except (ConnectionError, TimeoutError, RuntimeError,
            ValueError) as error:
        print("Error:", error)


if __name__ == "__main__":
    main()