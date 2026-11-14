/*
  PathogenBreak - live soil sensor node (Arduino Uno / Nano)

  What it does
    1. Reads the soil moisture probe every few seconds
    2. Shows moisture % on the 16x2 I2C LCD
    3. Beeps the buzzer once when soil turns waterlogged (soil-borne fungi risk)
    4. Sends each reading over Bluetooth (HC-05) AND USB as one text line:
         PB,<raw>,<percent>
    5. Listens for the advisory coming back from the laptop and shows it on the LCD:
         L1:<16 chars>   -> LCD row 1
         L2:<16 chars>   -> LCD row 2

  Libraries (Arduino IDE -> Tools -> Manage Libraries)
    - "LiquidCrystal I2C" by Frank de Brabander
    (SoftwareSerial and Wire come with the IDE)

  WIRING (Arduino Uno / Nano)
    I2C LCD backpack : GND->GND  VCC->5V  SDA->A4  SCL->A5
    Soil sensor board: VCC->D7 (powered only while reading, slows probe corrosion)
                       GND->GND  AO->A0   DO->not used
                       2 small pins -> the fork probe (any way round)
    HC-05            : VCC->5V  GND->GND
                       TXD -> D2
                       RXD <- D3 through a voltage divider (D3 -> 1k -> RXD -> 2k -> GND)
                       EN, STATE -> not connected
    Buzzer (low-level trigger): VCC->5V  GND->GND  I/O->D6   (LOW = beep)
*/

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <SoftwareSerial.h>

// ---------- pins ----------
const uint8_t PIN_SOIL_AO    = A0;
const uint8_t PIN_SOIL_POWER = 7;
const uint8_t PIN_BUZZER     = 6;
const uint8_t PIN_BT_RX      = 2;   // Arduino receives on D2  (connect to HC-05 TXD)
const uint8_t PIN_BT_TX      = 3;   // Arduino sends on D3     (to HC-05 RXD via divider)

// ---------- calibration: CHANGE THESE after the calibration step ----------
// Hold the probe in dry air -> note the raw value -> put it in DRY_RAW.
// Put the probe in a glass of water (only the forks) -> note raw -> WET_RAW.
const int DRY_RAW = 1015;
const int WET_RAW = 320;

const int  WATERLOG_PCT    = 80;     // above this = waterlogged, alert
const unsigned long READ_EVERY_MS = 5000;

// LCD address is usually 0x27; if the screen stays blank try 0x3F
LiquidCrystal_I2C lcd(0x27, 16, 2);
SoftwareSerial bt(PIN_BT_RX, PIN_BT_TX);

unsigned long lastRead = 0;
bool wasWaterlogged = false;
String inLine = "";
String advisory1 = "";
String advisory2 = "";

int readSoilRaw() {
  digitalWrite(PIN_SOIL_POWER, HIGH);   // switch the probe on
  delay(20);                            // let it settle
  long sum = 0;
  for (int i = 0; i < 10; i++) {        // average 10 samples
    sum += analogRead(PIN_SOIL_AO);
    delay(5);
  }
  digitalWrite(PIN_SOIL_POWER, LOW);    // switch it off again
  return (int)(sum / 10);
}

int rawToPercent(int raw) {
  // These boards give a HIGH number when DRY and a LOW number when WET
  long pct = map(raw, DRY_RAW, WET_RAW, 0, 100);
  return (int)constrain(pct, 0L, 100L);
}

void beep(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(PIN_BUZZER, LOW);      // low-level trigger: LOW = ON
    delay(120);
    digitalWrite(PIN_BUZZER, HIGH);
    delay(120);
  }
}

void showReading(int pct) {
  lcd.setCursor(0, 0);
  if (advisory1.length() > 0) {
    lcd.print(advisory1);
  } else {
    lcd.print("Soil moist: ");
    lcd.print(pct);
    lcd.print("%   ");
  }
  lcd.setCursor(0, 1);
  if (advisory2.length() > 0) {
    lcd.print(advisory2);
  } else if (pct >= WATERLOG_PCT) {
    lcd.print("WATERLOGGED!    ");
  } else if (pct < 25) {
    lcd.print("Dry - low Rabi  ");
  } else {
    lcd.print("Moisture OK     ");
  }
}

void handleLine(Stream &src, String line) {
  line.trim();
  // pad / cut to exactly 16 characters for the LCD
  if (line.startsWith("L1:") || line.startsWith("L2:")) {
    String text = line.substring(3);
    while (text.length() < 16) text += ' ';
    text = text.substring(0, 16);
    if (line.startsWith("L1:")) advisory1 = text; else advisory2 = text;
    beep(1);
  } else if (line == "CLEAR") {
    advisory1 = "";
    advisory2 = "";
  }
}

void pollSerial(Stream &src) {
  while (src.available()) {
    char c = src.read();
    if (c == '\n') {
      handleLine(src, inLine);
      inLine = "";
    } else if (c != '\r' && inLine.length() < 40) {
      inLine += c;
    }
  }
}

void setup() {
  pinMode(PIN_SOIL_POWER, OUTPUT);
  digitalWrite(PIN_SOIL_POWER, LOW);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, HIGH);       // silent at start (LOW would beep)

  Serial.begin(9600);                   // USB
  bt.begin(9600);                       // HC-05 default baud rate

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("PathogenBreak");
  lcd.setCursor(0, 1);
  lcd.print("Soil node ready");
  beep(2);
  delay(1500);
  lcd.clear();
}

void loop() {
  pollSerial(Serial);
  pollSerial(bt);

  if (millis() - lastRead >= READ_EVERY_MS) {
    lastRead = millis();
    int raw = readSoilRaw();
    int pct = rawToPercent(raw);

    // one line, same on USB and Bluetooth
    String msg = "PB," + String(raw) + "," + String(pct);
    Serial.println(msg);
    bt.println(msg);

    bool waterlogged = pct >= WATERLOG_PCT;
    if (waterlogged && !wasWaterlogged) beep(3);   // beep only when it CHANGES to waterlogged
    wasWaterlogged = waterlogged;

    showReading(pct);
  }
}
