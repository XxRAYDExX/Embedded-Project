#include "serial_server.h"
#include "protocol.h"
#include <string.h>
#include <stdint.h>

/* Receive interrupt writes bytes to a ring; the main loop parses them. */
#define RX_RING_SIZE 128u
#define FRAME_MAX 32u  /* including LF */
#define FRAME_TIMEOUT 500u
static UART_HandleTypeDef *uart;
static Game game;
static volatile uint8_t rx_byte;
static volatile uint8_t rx_ring[RX_RING_SIZE];
static volatile uint16_t head, tail;
static volatile uint8_t overflow;
static char frame[FRAME_MAX + 1u];
static uint8_t length, discard, discard_error;
static uint32_t last_byte;

static void send_line(const char *s) {
    char line[64];
    size_t n = strlen(s);
    if (n > sizeof(line) - 2u) return;
    memcpy(line, s, n);
    line[n++] = '\n';
    (void)HAL_UART_Transmit(uart, (uint8_t *)line, (uint16_t)n, 100u);
}
static void arm_receive(void) {
    (void)HAL_UART_Receive_IT(uart, (uint8_t *)&rx_byte, 1u);
}
void server_init(UART_HandleTypeDef *huart) {
    uart = huart;
    game_init(&game);
    head = tail = 0;
    overflow = 0;
    length = discard = discard_error = 0;
    last_byte = HAL_GetTick();
    arm_receive();
}
GameStatus server_status(void) { return game.status; }
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart != uart) return;
    uint16_t next = (uint16_t)((head + 1u) % RX_RING_SIZE);
    if (next == tail) overflow = 1;
    else { rx_ring[head] = rx_byte; head = next; }
    arm_receive();
}
void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart) {
    if (huart == uart) {
        overflow = 1;
        arm_receive();
    }
}
static void reset_frame(void) {
    length = 0;
    discard = 0;
    discard_error = 0;
}
static void parse_byte(uint8_t b) {
    last_byte = HAL_GetTick();
    if (discard) {
        if (b == '\n') {
            reset_frame();
            send_line("NACK:BADCMD");
        }
        return;
    }
    if (b == '\n') {
        if (length && frame[length - 1u] == '\r') --length;
        if (!length) { reset_frame(); send_line("NACK:BADCMD"); return; }
        frame[length] = '\0';
        for (unsigned i = 0; i < length; ++i) {
            uint8_t c = (uint8_t)frame[i];
            if (c < 32u || c > 126u) {
                reset_frame(); send_line("NACK:BADCMD"); return;
            }
        }
        char response[48];
        protocol_handle(&game, frame, response, sizeof(response));
        reset_frame();
        send_line(response);
        return;
    }
    /* The 32nd byte without LF is oversized; discard until LF. */
    if (length >= FRAME_MAX - 1u) {
        discard = 1;
        length = 0;
        return;
    }
    frame[length++] = (char)b;
}
void server_poll(void) {
    if (overflow) {
        __disable_irq();
        overflow = 0;
        tail = head;
        __enable_irq();
        /* Lost bytes make the current frame untrustworthy. */
        reset_frame();
        discard = 1;
        last_byte = HAL_GetTick();
    }
    while (tail != head) {
        uint8_t b = rx_ring[tail];
        tail = (uint16_t)((tail + 1u) % RX_RING_SIZE);
        parse_byte(b);
    }
    if ((length || discard) &&
        (uint32_t)(HAL_GetTick() - last_byte) >= FRAME_TIMEOUT) {
        reset_frame();
        send_line("NACK:TIMEOUT");
    }
}
void server_button_reset(void) {
    /* Call from the main loop after a debounced button press. */
    game_init(&game);
    reset_frame();
    send_line("EVT:RESET");
}
