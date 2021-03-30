#include <avr/io.h>
#include <util/delay.h>
#include <util/twi.h>
#include <avr/interrupt.h>
#include <stdio.h>

#define BAUD 57600    // baud rate for serial connection
#define MPU_6050 0xd0 // I2C address of chip for writing
volatile unsigned char buffer[128];
volatile unsigned char second_buffer[128];
volatile int in = 0;
volatile int out = 0;

volatile int secondIn = 0;
volatile int secondOut = 0;

/**
 *    container for the data retrieved from the IMU
 */
typedef struct {
    int16_t accel_x, accel_y, accel_z;
    int16_t gyro_x, gyro_y, gyro_z;
} IMU_Data;

/**
 *    contains the data for the self-test
 */
typedef struct {
    uint8_t XA, YA, ZA;
    uint8_t XG, YG, ZG;
} SelfTestData;


void USART_init(void) {
    // set baud rate
#include <util/setbaud.h>
    UBRR0H = UBRRH_VALUE;
    UBRR0L = UBRRL_VALUE;
#if USE_2X
    UCSR0A |= (1 << U2X0);
#else
    UCSR0A &= ~(1 << U2X0);
#endif
    UCSR0B = (1<<RXEN0)|(1<<TXEN0);
    // enable TxD pin output
    DDRD |= 2;
}

void setupBuffer(void){
    UCSR0B |= (1<<UDRIE0 | 1<<RXCIE0);
}

void writeToBuffer(char data){
    buffer[out] = data;
    out = (out + 1) % 128;
    setupBuffer();
}

char getFromBuffer(void){
    char result = buffer[in];
    in = (in + 1) % 128;
    return result;
}

int isBufferEmpty(void){
    return (in == out);
}

// output character on serial line
void put_c( unsigned char data ) {
    while ( !( UCSR0A & (1<<UDRE0)) ) {}
    /* Put data into buffer, sends the data */
    UDR0 = data;
}

// output decimal number on serial line
void putDec(int16_t x) {
    unsigned char buf[8];

    if (x<0) {
        writeToBuffer('-');
        x = -x;
    }
    if (x==0) {
        writeToBuffer('0');
    } else {
        int i=0;
        while (i<8 && x>0) {
            buf[i++] = '0' + (x%10);
            x = x/10;
        }
        i=i-1;
        while (i>= 0) writeToBuffer(buf[i--]);
    }
}

// output decimal number on serial line
void putHex(int16_t x) {
    char* map = "0123456789abcdef";
    char buf[4] = "0000";
    if (x==0) {
        writeToBuffer('0');
    } else {
        int i=0;
        while (i<4 && x>0) {
            buf[i++] = map[x%16];
            x = x/16;
        }
        i=i-1;
        while (i>= 0) writeToBuffer(buf[i--]);
    }
}


/**
 *    writes IMU data to the buffer with a leading D(ata)
 *    @param d contains the IMU data
 */
void putIMUData(IMU_Data *d){
    writeToBuffer('D');
    writeToBuffer(' ');
    putDec(d->accel_x);
    writeToBuffer(' ');
    putDec(d->accel_y);
    writeToBuffer(' ');
    putDec(d->accel_z);
    writeToBuffer(' ');
    putDec(d->gyro_x);
    writeToBuffer(' ');
    putDec(d->gyro_y);
    writeToBuffer(' ');
    putDec(d->gyro_z);
    writeToBuffer('\n');
}


/**
 *    writes IMU data to the buffer with a leading S(elf-test)
 *    @param d contains the self-test data
 */
void putSelfTestData(SelfTestData *d){
    writeToBuffer('S');
    writeToBuffer(' ');
    putDec(d->XA);
    writeToBuffer(' ');
    putDec(d->YA);
    writeToBuffer(' ');
    putDec(d->ZA);
    writeToBuffer(' ');
    putDec(d->XG);
    writeToBuffer(' ');
    putDec(d->YG);
    writeToBuffer(' ');
    putDec(d->ZG);
    writeToBuffer('\n');
}

// initialize I2C communication
static inline void I2C_init(void) {
    TWSR = 0;  // no prescaler
    TWBR = 72; // set clock to 100kHz
}

// wait for I2C transition to finish
static inline void I2C_wait(void) {
    while  (!(TWCR & (1<<TWINT))); // wait until start is sent
}

// send I2C stop condition and wait
static inline void I2C_stop(void) {
    TWCR = (1<<TWINT) | (1<<TWEN) | (1<<TWSTO);
    while(TWCR & (1<<TWSTO));
}

static inline void I2C_start(void) {
    TWCR = (1<<TWINT) | (1<<TWSTA) | (1<<TWEN); // send start condition
    I2C_wait(); // wait until start is sent
}

// send a sequence of byte
void I2C_send(uint8_t address, unsigned char *data, uint8_t bytes_to_write) {
    I2C_start();
    TWDR = address;
    TWCR = (1<<TWINT) | (1<<TWEN);
    I2C_wait();
    for (uint8_t i = bytes_to_write; i>0; i--) {
        TWDR = *data++;
        TWCR = (1<<TWINT) | (1<<TWEN);
        I2C_wait();
    }
    I2C_stop();
}

// convenience method for writing data to a single register in an I2C device
void I2C_poke(uint8_t address, uint8_t reg, uint8_t value) {
    uint8_t data[2];
    data[0] = reg;
    data[1] = value;
    I2C_send(address, data, 2);
}

// retrieve a sequence of bytes from an I2C device
void I2C_read_registers(uint8_t address, uint8_t start_register, uint8_t *data, uint8_t bytes_to_read) {
    // send start
    I2C_start();
    // address chip for writing
    TWDR = address;
    TWCR = (1<<TWINT) | (1<<TWEN);
    I2C_wait(); // wait until start is sent
    // send register
    TWDR = start_register;
    TWCR = (1<<TWINT) | (1<<TWEN);
    I2C_wait();

    // send restart
    I2C_start();

    // address chip for reading
    TWDR = address | 1 ; // master read
    TWCR = (1<<TWINT) | (1<<TWEN);
    I2C_wait(); // wait until start is sent
    // read data
    for (uint8_t i = bytes_to_read-1; i>0; i--) {
        TWCR = (1<<TWINT) | (1<<TWEN) | (1<<TWEA);
        I2C_wait();
        *data++ = TWDR;
    }
    TWCR = (1<<TWINT) | (1<<TWEN);
    I2C_wait();
    *data = TWDR;
    I2C_stop();
}

//
// communication with IMU sensor (type MPU-6050) by reading/setting its registerss
//


// simple data type of IMU sensor data

// read sensor data registers from MPU-6050
void imu_get_data(IMU_Data *d) {
    uint8_t raw_data[14];
    I2C_read_registers(MPU_6050, 0x3b, raw_data, 14); // get 14 bytes
    // convert data into proper signed 16 bit integers
    d->accel_x = (int16_t)((raw_data[0] << 8) | raw_data[1]);
    d->accel_y = (int16_t)((raw_data[2] << 8) | raw_data[3]);
    d->accel_z = (int16_t)((raw_data[4] << 8) | raw_data[5]);
    d->gyro_x  = (int16_t)((raw_data[8] << 8) | raw_data[9]);
    d->gyro_y  = (int16_t)((raw_data[10] << 8) | raw_data[11]);
    d->gyro_z  = (int16_t)((raw_data[12] << 8) | raw_data[13]);
}

// return non-zero value if IMU has updated its registers
// and new sensor data is available (used in polling, alternatively
// configure IMU to signal interrupts via INT pin and hook that up
// to one of Arduino's external interrupt pins)
uint8_t imu_has_new_data(void) {
    uint8_t data;
    I2C_read_registers(MPU_6050, 0x3A, &data, 1);
    return data & 1;
}

// initializes the MPU-6050
// feel free to change device parameters (-> datasheet)
void imu_init(uint8_t a_scale, uint8_t g_scale) {
    I2C_poke(MPU_6050, 0x6b, 0x01); // clock source

    I2C_poke(MPU_6050, 0x1a, 0x03); // no FSYNC, 44/42 Hz bandwith
    I2C_poke(MPU_6050, 0x19, 0x04); // 200Hz gyro sample rate
    uint8_t config;
    I2C_read_registers(MPU_6050, 0x1b, &config, 1);
    I2C_poke(MPU_6050, 0x1b, config | 0xe0); // enable self-test
    // I2C_poke(MPU_6050, 0x1b, config & ~0xe0); // disable self-test
    I2C_poke(MPU_6050, 0x1b, config & ~0x18); // clear AFS
    I2C_poke(MPU_6050, 0x1b, config |(g_scale << 3)); // set gyro range

    I2C_read_registers(MPU_6050, 0x1C, &config, 1);
    I2C_poke(MPU_6050, 0x1C, config | 0xe0); // enable self-test
    // I2C_poke(MPU_6050, 0x1C, config & ~0xe0); // disable self-test
    I2C_poke(MPU_6050, 0x1C, config & ~0x18); // clear AFS
    I2C_poke(MPU_6050, 0x1C, config | (a_scale << 3)); // set accelerometer range
}

/**
 *    retrieves the self test data
 *    @param stdata contains the self test data
 */
void getSTData(SelfTestData *stdata){
    uint8_t raw_data[4];
    I2C_read_registers(MPU_6050, 0x0d, raw_data, 4);
    stdata->XA = (uint8_t)((raw_data[0] >> 2) & 0x1c) | ((raw_data[3]>>4) & 0x3);
    stdata->YA = (uint8_t)((raw_data[1] >> 2) & 0x1c) | ((raw_data[3]>>2) & 0x3);
    stdata->ZA = (uint8_t)((raw_data[2] >> 2) & 0x1c) | (raw_data[3] & 0x3);;
    stdata->XG = (uint8_t)(raw_data[0] & 0x1f);
    stdata->YG = (uint8_t)(raw_data[1] & 0x1f);
    stdata->ZG = (uint8_t)(raw_data[2] & 0x1f);
}

/**
 *    retrieve the data for the self-test and write it to buffer
 */
void selfTest(void){
    IMU_Data dataST;
    imu_get_data(&dataST);

    SelfTestData stdata;
    getSTData(&stdata);

    putIMUData(&dataST);
    putSelfTestData(&stdata);

    uint8_t config;
    I2C_read_registers(MPU_6050, 0x1b, &config, 1);
    I2C_poke(MPU_6050, 0x1b, config & ~0xe0); // disable self-test
    I2C_read_registers(MPU_6050, 0x1c, &config, 1);
    I2C_poke(MPU_6050, 0x1c, config & ~0xe0); // disable self-test

    IMU_Data data;
    imu_get_data(&data);
    putIMUData(&data);


}


int __attribute__((OS_main)) main(void) {
    USART_init();   // initialize serial
    setupBuffer();  // initialize buffer for serial communication

    I2C_init();     // initialize I2C interface for IMU
    imu_init(2, 1); // 2: 8g full range; 0: 250 degrees per second full range

    selfTest();     // conduct self-test
    sei();          // enable interrupts

    IMU_Data d;
    // whenever the IMU has new data, write it to the buffer
    while (1) {
        if(imu_has_new_data()) {
            imu_get_data(&d);
            putIMUData(&d);
            _delay_ms(20);
        }
    }
}

// interrupts whenever new data can be transmitted
ISR(USART_UDRE_vect) {
    if (isBufferEmpty()) { // noch Zeichen im Puffer zum Senden?
        UCSR0B &= (255 ^ (1<<UDRIE0));
    }else {
        //transmits the data
        char toBeTransmitted;
        if (!isBufferEmpty()){
            toBeTransmitted = getFromBuffer();
            put_c(toBeTransmitted);
        }
    }
}
