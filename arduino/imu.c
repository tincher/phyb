#include <avr/io.h>
#include <util/delay.h>
#include <util/twi.h>

#define BAUD 57600    // baud rate for serial connection
#define MPU_6050 0xd0 // I2C address of chip for writing

//
// simple serial communication
//

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
        put_c('-');
        x = -x;
    }
    if (x==0) {
        put_c('0');
    } else {
        int i=0;
        while (i<8 && x>0) {
            buf[i++] = '0' + (x%10);
            x = x/10;
        }
        i=i-1;
        while (i>= 0) put_c(buf[i--]);
    }
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
typedef struct {
    int16_t accel_x, accel_y, accel_z;
    int16_t gyro_x, gyro_y, gyro_z;
} IMU_Data;

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
    I2C_poke(MPU_6050, 0x1b, config & ~0xe0); // disable self-test
    I2C_poke(MPU_6050, 0x1b, config & ~0x18); // clear AFS
    I2C_poke(MPU_6050, 0x1b, config |(g_scale << 3)); // set gyro range

    I2C_read_registers(MPU_6050, 0x1C, &config, 1);
    I2C_poke(MPU_6050, 0x1C, config & ~0xe0); // disable self-test
    I2C_poke(MPU_6050, 0x1C, config & ~0x18); // clear AFS
    I2C_poke(MPU_6050, 0x1C, config | (a_scale << 3)); // set accelerometer range
}

// simple test program to print IMU data
int __attribute__((OS_main)) main(void) {
    USART_init();   // initialize serial
    put_c('R');     // signal reset
    put_c('\n');

    I2C_init();     // initialize I2C interface for IMU
    imu_init(0, 0); // 0: 2g full range; 0: 250 degrees per second full range

    IMU_Data d;
    while (1) {
        if(imu_has_new_data()) {
            imu_get_data(&d);
            putDec(d.accel_x);
            put_c(' ');
            putDec(d.accel_y);
            put_c(' ');
            putDec(d.accel_z);
            put_c(' ');
            putDec(d.gyro_x);
            put_c(' ');
            putDec(d.gyro_y);
            put_c(' ');
            putDec(d.gyro_z);
            put_c('\n');
            _delay_ms(250);
        }
    }
}
