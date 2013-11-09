#include <avr/io.h>
#include <avr/interrupt.h>
#include "build/minimal.interface.h"

int main()
{
    robonet_init();
    sei(); // bzzzzzzzzz........

    while(1)
        layer2_communicate();
}
