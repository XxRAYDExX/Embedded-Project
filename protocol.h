#ifndef PROTOCOL_H
#define PROTOCOL_H
#include "game.h"
#include <stddef.h>
/* Returns a single response without newline, into output of at least 32 bytes. */
void protocol_handle(Game *g, const char *command, char *output, size_t capacity);
#endif
