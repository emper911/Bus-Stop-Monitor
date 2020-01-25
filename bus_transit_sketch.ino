#include <TM1637Display.h>

// LED pins:
#define LED_0N 13
#define LED_1N 12
#define LED_2N 11
#define LED_3N 10
#define LED_4N 9
#define LED_0S 8
#define LED_1S 7
#define LED_2S 6
#define LED_3S 5
#define LED_4S 4
//Display Pins, clock and output
#define DIO 3
#define CLK 2

int minutes_away_1 = -1;
int minutes_away_2 = -1;

int led_array[] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
boolean newData = false;
boolean flip_display_value = true;

// Create display object of type TM1637Display:
TM1637Display display = TM1637Display(CLK, DIO);

//A Symbol:
const uint8_t train_A[] = {
  SEG_A | SEG_B | SEG_C | SEG_E | SEG_F | SEG_G  // A
};
//4 Symbol:
const uint8_t train_4[] = {
  SEG_B | SEG_C | SEG_F | SEG_G  // 4
};

void setup() {
  pinMode(LED_0N, OUTPUT);
  pinMode(LED_1N, OUTPUT);
  pinMode(LED_2N, OUTPUT);
  pinMode(LED_3N, OUTPUT);
  pinMode(LED_4N, OUTPUT);
  pinMode(LED_0S, OUTPUT);
  pinMode(LED_1S, OUTPUT);
  pinMode(LED_2S, OUTPUT);
  pinMode(LED_3S, OUTPUT);
  pinMode(LED_4S, OUTPUT);
  Serial.begin(9600);
  display.clear();
  delay(1000);

}

void displayTime() {
  // Set the brightness:
  boolean displaying = false;
  display.setBrightness(7);
  if ( flip_display_value == true) {
    //Display A, C direction time
    display.clear();
    if ( minutes_away_1 != -1){
      display.showNumberDecEx(minutes_away_1, 0b01000000, true, 2, 0);
      
    }
    display.setSegments(train_A, 1, 3);
    flip_display_value = false;
  }
  else {
    //Display 4 train direction time
    display.clear();
    if ( minutes_away_2 != -1){
      display.showNumberDecEx(minutes_away_2, 0b01000000, true, 2, 0);
      
    }
    display.setSegments(train_4, 1, 3);
    flip_display_value = true;
  }
  delay(5000);
}

void UpdateBusStopLeds(int leds[]) {
  digitalWrite(LED_0N, leds[0]);
  delay(5);
  digitalWrite(LED_1N, leds[1]);
  delay(5);
  digitalWrite(LED_2N, leds[2]);
  delay(5);
  digitalWrite(LED_3N, leds[3]);
  delay(5);
  digitalWrite(LED_4N, leds[4]);
  delay(5);
  digitalWrite(LED_0S, leds[5]);
  delay(5);
  digitalWrite(LED_1S, leds[6]);
  delay(5);
  digitalWrite(LED_2S, leds[7]);
  delay(5);
  digitalWrite(LED_3S, leds[8]);
  delay(5);
  digitalWrite(LED_4S, leds[9]);
  delay(5);
}

void UpdateBusInfo() {
  if (newData == true){
    UpdateBusStopLeds(led_array);
    
  }
  displayTime();
}

void RecieveMessage(){
    static boolean recvInProgress = false;
    static byte i = 0;
    char startMarker = '<';
    char endMarker = '>';
    byte rc;
    char rc_char;
    String min_away_char_1;
    String min_away_char_2;
 
    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();
        rc_char = rc;
        if (recvInProgress == true) {
            //data
            if (rc_char != endMarker) {
                if ( i < 2 ) { //mins away 1
                  min_away_char_1 += rc_char;
                }
                else if ( i < 4 ) { //mins away 2
                  min_away_char_2 += rc_char;
                }
                else {//led_array
                  int j = i - 4;
                  //ASCII 0: 48, ASCII 1: 49, ... e.g 49 - 48 = 1, 50 - 48 = 2, ...
                  led_array[j] = rc_char - '0';
                }
                i++;
            }
            //once end marker is reached
            else {
                //Adds \0 to end string, and converts times to int
                min_away_char_1 += '\0';
                min_away_char_2 += '\0';
                minutes_away_1 = min_away_char_1.toInt();
                minutes_away_2 = min_away_char_2.toInt();
                //reset variables for next message
                min_away_char_1 = "";
                min_away_char_2 = "";
                recvInProgress = false;
                i = 0;
                newData = true;
            }
        }
        else if (rc_char == startMarker) {
            recvInProgress = true;
        }
    }   
}

void loop() {
  //Reads bluetooth serial information
  RecieveMessage();
  //Updates the Outputs
  UpdateBusInfo();
  newData = false;
  
}
