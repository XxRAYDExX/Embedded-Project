#include "protocol.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>
static void reply(char *out,size_t cap,const char *s){snprintf(out,cap,"%s",s);}
void protocol_handle(Game *g,const char *cmd,char *out,size_t cap){
    if(strcmp(cmd,"CONNECT")==0){reply(out,cap,"OK");return;}
    if(strcmp(cmd,"NEW")==0){
        if(g->status==IN_PROGRESS){reply(out,cap,"NACK:BADSTATE");return;}
        game_new(g);snprintf(out,cap,"OK:BOARD:%s",g->board);return;
    }
    if(strcmp(cmd,"STATE")==0){
        if(g->status==IDLE){reply(out,cap,"NACK:NOGAME");return;}
        snprintf(out,cap,"BOARD:%s",g->board);return;
    }
    if(strcmp(cmd,"RESIGN")==0){
        if(g->status!=IN_PROGRESS){reply(out,cap,"NACK:NOGAME");return;}
        g->status=GAME_OVER;reply(out,cap,"OK:GAMEOVER");return;
    }
    if(strcmp(cmd,"DISCONNECT")==0){
        if(g->status==IN_PROGRESS){reply(out,cap,"NACK:BADSTATE");return;}
        game_init(g);reply(out,cap,"OK");return;
    }
    if(strncmp(cmd,"MOVE:",5)==0){
        if(g->status!=IN_PROGRESS){reply(out,cap,"NACK:NOGAME");return;}
        /* Strict syntax MOVE:<decimal integer>:<X|O> */
        const char *p=cmd+5;
        if(!isdigit((unsigned char)*p)){reply(out,cap,"NACK:BADCMD");return;}
        unsigned value=0;
        while(isdigit((unsigned char)*p)){
            if(value<=1000) value=value*10u+(unsigned)(*p-'0');
            else value=10000;
            p++;
        }
        if(*p!=':' || (p[1]!='X' && p[1]!='O') || p[2]!='\0'){
            reply(out,cap,"NACK:BADCMD");return;
        }
        if(value>8){reply(out,cap,"NACK:RANGE");return;}
        if(g->board[value]!='.'){reply(out,cap,"NACK:OCCUPIED");return;}
        if(p[1]!=g->turn){reply(out,cap,"NACK:NOTURN");return;}
        g->board[value]=g->turn;
        char winner=game_winner(g);
        if(winner!='.'){
            g->status=GAME_OVER;
            snprintf(out,cap,"WIN:%c:%s",winner,g->board);
        }else if(game_full(g)){
            g->status=GAME_OVER;
            snprintf(out,cap,"DRAW:%s",g->board);
        }else{
            g->turn=(g->turn=='X')?'O':'X';
            snprintf(out,cap,"OK:BOARD:%s",g->board);
        }
        return;
    }
    reply(out,cap,"NACK:BADCMD");
}
