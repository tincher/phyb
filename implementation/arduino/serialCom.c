#include <avr/io.h>
#include <stdio.h>


void USART_Init(unsigned int ubrr){
    UBRR0H = (unsigned char)(ubrr>>8);
    UBRR0L = (unsigned char)ubrr;

    UCSR0B = (1<<RXEN0) | (1<<TXEN0);

    UCSR0C = 3<<UCSZ00;
}


void putChar(unsigned char data){
    while (!(UCSR0A & (1<<UDRE0)));
    UDR0 = data;
}

void putString(char *stringToBeSent){
    while (*stringToBeSent) putChar(*stringToBeSent++);
}

void putDec(long longToBeSent){
    for (int i = 3; i >= 0; i--){
        while (!(UCSR0A & (1<<UDRE0)));
        UDR0 = longToBeSent>>(i*8);
    }
}


void putHex(long hexToBeSent){
    char str[9];
    sprintf(str, "%08lx", hexToBeSent);
    for (int i=0; i<8; i++){
        putChar(str[i]);
    }
    // for (int i = 7; i >= 0; i--){
    //     while (!(UCSR0A & (1<<UDRE0)));
    //     UDR0 = hexToBeSent>>(i*8);
    // }
}

char getChar(void){
    while (!(UCSR0A & (1<<RXC0)));

    return UDR0;
}
