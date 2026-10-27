#ifndef SERIAL_SERVER_H
#define SERIAL_SERVER_H
#include "stm32f0xx_hal.h"
#include "game.h"
void server_init(UART_HandleTypeDef *huart);
void server_poll(void);
void server_button_reset(void);
GameStatus server_status(void);
#endif
