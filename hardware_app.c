#include "hardware_app.h"
#include "serial_server.h"
/* Define BOARD_LED_GPIO_Port/BOARD_LED_Pin and BOARD_BUTTON_GPIO_Port/
 * BOARD_BUTTON_Pin in CubeMX-generated main.h or a board-specific header.
 * Define BOARD_LED_ACTIVE_HIGH=0 for active-low LEDs.
 * Define BOARD_BUTTON_PRESSED=GPIO_PIN_SET for active-high buttons.
 * If unspecified, that feature is disabled rather than guessing pins.
 */
#include "main.h"
#ifndef BOARD_LED_ACTIVE_HIGH
#define BOARD_LED_ACTIVE_HIGH 1
#endif
#ifndef BOARD_BUTTON_PRESSED
#define BOARD_BUTTON_PRESSED GPIO_PIN_RESET
#endif
static uint32_t last_button_change;
static GPIO_PinState last_raw;
static GPIO_PinState stable;
static uint8_t initialized;
void hardware_app_init(void) {
    last_button_change = HAL_GetTick();
#ifdef BOARD_BUTTON_GPIO_Port
    last_raw = HAL_GPIO_ReadPin(BOARD_BUTTON_GPIO_Port, BOARD_BUTTON_Pin);
    stable = last_raw;
#endif
    initialized = 1;
}
void hardware_app_poll(void) {
    if (!initialized) hardware_app_init();
#ifdef BOARD_BUTTON_GPIO_Port
    GPIO_PinState raw = HAL_GPIO_ReadPin(BOARD_BUTTON_GPIO_Port, BOARD_BUTTON_Pin);
    if (raw != last_raw) { last_raw = raw; last_button_change = HAL_GetTick(); }
    if (raw != stable && (uint32_t)(HAL_GetTick()-last_button_change)>=30u) {
        stable = raw;
        if (stable == BOARD_BUTTON_PRESSED) server_button_reset();
    }
#endif
#ifdef BOARD_LED_GPIO_Port
    uint32_t now = HAL_GetTick();
    uint8_t on = 0;
    if (server_status() == IN_PROGRESS) on = 1;
    else if (server_status() == GAME_OVER) on = ((now/250u)%2u)==0u;
    HAL_GPIO_WritePin(BOARD_LED_GPIO_Port, BOARD_LED_Pin,
       (on == BOARD_LED_ACTIVE_HIGH) ? GPIO_PIN_SET : GPIO_PIN_RESET);
#endif
}
