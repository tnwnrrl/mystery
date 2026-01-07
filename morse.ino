/*
 * ESP32 오실로스코프 X-Y 모드 - Morse Code Sequence
 * 순서: 8 → X → 3 → U (반복)
 *   8 = ---..
 *   X = -..-
 *   3 = ...--
 *   U = ..-
 * Home Assistant MQTT 연동
 *
 * 연결:
 *   X축 → GPIO 25 (DAC1)
 *   Y축 → GPIO 26 (DAC2)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h"

#define DAC_X 25
#define DAC_Y 26

#define MAX_POINTS 1000
uint8_t pointsX[MAX_POINTS];
uint8_t pointsY[MAX_POINTS];
int numPoints = 0;

// ========== Home Assistant 상태 ==========
bool deviceOn = true;
bool displayActive = false;  // 기호 출력 활성화 (PATTERN 명령 시 true, STOP 시 false)

// ========== MQTT 토픽 ==========
const char* TOPIC_STATE = "morse/state";
const char* TOPIC_COMMAND = "morse/set";
const char* TOPIC_AVAILABILITY = "morse/availability";

// ========== WiFi/MQTT 객체 ==========
WiFiClient espClient;
PubSubClient mqtt(espClient);
unsigned long lastReconnectAttempt = 0;
unsigned long lastStatePublish = 0;

// ========== 시퀀스 상태 ==========
int currentSymbol = 0;  // 0=8, 1=X, 2=3, 3=U
const int NUM_SYMBOLS = 4;

// ========== 노이즈 설정 ==========
const int NOISE_AMOUNT = 3;  // 노이즈 강도 (±3 픽셀)

// ========== 함수 선언 ==========
void setupWiFi();
void mqttCallback(char* topic, byte* payload, unsigned int length);
bool mqttReconnect();
void publishState();
void publishDiscovery();
void drawCurrentSymbol();
void drawMorse8();
void drawMorseX();
void drawMorse3();
void drawMorseU();
void processSerialCommand();

// 포인트 추가 (Y축 반전)
void addPoint(float x, float y) {
  if (numPoints >= MAX_POINTS) return;
  pointsX[numPoints] = constrain((int)x, 0, 255);
  pointsY[numPoints] = 255 - constrain((int)y, 0, 255);
  numPoints++;
}

// 선 그리기 (대시용)
void addLine(float x1, float y1, float x2, float y2, int segments) {
  for (int i = 0; i <= segments; i++) {
    float t = (float)i / segments;
    addPoint(x1 + t * (x2 - x1), y1 + t * (y2 - y1));
  }
}

// 원 그리기 (점용)
void addCircle(float cx, float cy, float r, int segments) {
  for (int i = 0; i <= segments; i++) {
    float angle = 2 * PI * i / segments;
    addPoint(cx + r * cos(angle), cy + r * sin(angle));
  }
}

// ========== 공통 파라미터 ==========
const float MORSE_Y = 128;        // Y 중앙
const float DASH_LEN = 30;        // 대시 길이
const float DOT_RADIUS = 8;       // 점 반지름
const float GAP = 15;             // 요소 간격

// 대시 그리기 헬퍼
float addDash(float x) {
  addLine(x, MORSE_Y, x + DASH_LEN, MORSE_Y, 20);
  return x + DASH_LEN + GAP;
}

// 점 그리기 헬퍼
float addDot(float x) {
  addCircle(x + DOT_RADIUS, MORSE_Y, DOT_RADIUS, 24);
  return x + DOT_RADIUS * 2 + GAP;
}

// ========== 모스부호 8 (---.. ) ==========
void drawMorse8() {
  numPoints = 0;
  float x = 37;  // 중앙 정렬
  x = addDash(x);  // -
  x = addDash(x);  // -
  x = addDash(x);  // -
  x = addDot(x);   // .
  addDot(x);       // .
}

// ========== 모스부호 X (-..- ) ==========
void drawMorseX() {
  numPoints = 0;
  float x = 52;  // 중앙 정렬
  x = addDash(x);  // -
  x = addDot(x);   // .
  x = addDot(x);   // .
  addDash(x);      // -
}

// ========== 모스부호 3 (...-- ) ==========
void drawMorse3() {
  numPoints = 0;
  float x = 37;  // 중앙 정렬
  x = addDot(x);   // .
  x = addDot(x);   // .
  x = addDot(x);   // .
  x = addDash(x);  // -
  addDash(x);      // -
}

// ========== 모스부호 U (..- ) ==========
void drawMorseU() {
  numPoints = 0;
  float x = 75;  // 중앙 정렬
  x = addDot(x);   // .
  x = addDot(x);   // .
  addDash(x);      // -
}

// ========== 시리얼 명령 처리 ==========
void processSerialCommand() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.startsWith("PATTERN:")) {
      int pattern = cmd.substring(8).toInt();
      if (pattern >= 0 && pattern < NUM_SYMBOLS) {
        currentSymbol = pattern;
        displayActive = true;  // 패턴 명령 오면 출력 활성화
        drawCurrentSymbol();
        const char* symbols[] = {"8", "X", "3", "U"};
        Serial.printf("OK:PATTERN:%s\n", symbols[currentSymbol]);
      } else {
        Serial.println("ERROR:INVALID_PATTERN");
      }
    }
    else if (cmd == "STOP") {
      displayActive = false;  // 출력 중지 → 화면 비움
      Serial.println("OK:STOP");
    }
    else if (cmd == "STATUS") {
      Serial.printf("STATUS:displayActive=%d,pattern=%d,deviceOn=%d\n",
                    displayActive, currentSymbol, deviceOn);
    }
    else {
      Serial.println("ERROR:UNKNOWN_CMD");
    }
  }
}

// ========== 현재 심볼 그리기 ==========
void drawCurrentSymbol() {
  switch (currentSymbol) {
    case 0: drawMorse8(); break;
    case 1: drawMorseX(); break;
    case 2: drawMorse3(); break;
    case 3: drawMorseU(); break;
  }
}

// ========== WiFi 설정 ==========
void setupWiFi() {
  Serial.print("WiFi 연결 중: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("연결됨! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi 연결 실패 - 오프라인 모드");
  }
}

// ========== MQTT 콜백 ==========
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.printf("MQTT 수신 [%s]: %s\n", topic, message.c_str());

  if (String(topic) == TOPIC_COMMAND) {
    if (message == "ON") {
      deviceOn = true;
    } else if (message == "OFF") {
      deviceOn = false;
    }
    publishState();
  }
}

// ========== MQTT 연결 ==========
bool mqttReconnect() {
  Serial.print("MQTT 연결 시도...");

  String clientId = "ESP32_" + String(DEVICE_NAME);

  if (mqtt.connect(clientId.c_str(), MQTT_USER, MQTT_PASSWORD,
                   TOPIC_AVAILABILITY, 0, true, "offline")) {
    Serial.println("연결됨!");

    // 구독
    mqtt.subscribe(TOPIC_COMMAND);

    // 온라인 상태 발행
    mqtt.publish(TOPIC_AVAILABILITY, "online", true);

    // HA 자동 발견 발행
    publishDiscovery();

    // 현재 상태 발행
    publishState();

    return true;
  }

  Serial.print("실패, rc=");
  Serial.println(mqtt.state());
  return false;
}

// ========== Home Assistant 자동 발견 ==========
void publishDiscovery() {
  // 메인 스위치 (ON/OFF)
  StaticJsonDocument<512> doc;
  doc["name"] = DEVICE_FRIENDLY_NAME;
  doc["unique_id"] = String(DEVICE_NAME) + "_switch";
  doc["command_topic"] = TOPIC_COMMAND;
  doc["state_topic"] = TOPIC_STATE;
  doc["value_template"] = "{{ value_json.state }}";
  doc["payload_on"] = "ON";
  doc["payload_off"] = "OFF";
  doc["availability_topic"] = TOPIC_AVAILABILITY;
  doc["icon"] = "mdi:circle-outline";

  JsonObject device = doc.createNestedObject("device");
  device["identifiers"][0] = DEVICE_NAME;
  device["name"] = DEVICE_FRIENDLY_NAME;
  device["model"] = "ESP32 Oscilloscope Art";
  device["manufacturer"] = "DIY";

  char buffer[512];
  serializeJson(doc, buffer);
  mqtt.publish("homeassistant/switch/morse/config", buffer, true);

  Serial.println("HA Discovery 발행 완료");
}

// ========== 상태 발행 ==========
void publishState() {
  StaticJsonDocument<100> doc;
  doc["state"] = deviceOn ? "ON" : "OFF";

  char buffer[100];
  serializeJson(doc, buffer);
  mqtt.publish(TOPIC_STATE, buffer, true);
}

// ========== Setup ==========
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Morse Code Display (Waiting for PATTERN command) ===");
  Serial.println("Commands: PATTERN:0~3, STOP, STATUS");

  setupWiFi();

  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  mqtt.setBufferSize(1024);
}

// ========== Loop ==========
void loop() {
  unsigned long now = millis();

  // 시리얼 명령 처리
  processSerialCommand();

  // MQTT 연결 유지
  if (WiFi.status() == WL_CONNECTED) {
    if (!mqtt.connected()) {
      if (now - lastReconnectAttempt > 5000) {
        lastReconnectAttempt = now;
        mqttReconnect();
      }
    } else {
      mqtt.loop();

      // 주기적 상태 발행 (30초)
      if (now - lastStatePublish > 30000) {
        lastStatePublish = now;
        publishState();
      }
    }
  }

  // OFF 상태 또는 displayActive가 false면 DAC 출력 정지 (화면 비움)
  if (!deviceOn || !displayActive) {
    dacWrite(DAC_X, 128);
    dacWrite(DAC_Y, 128);
    delay(10);
    return;
  }

  // DAC 출력 - 현재 모스부호 (노이즈 추가)
  static int idx = 0;

  if (numPoints > 0) {
    for (int i = 0; i < 5; i++) {
      int px = pointsX[idx] + random(-NOISE_AMOUNT, NOISE_AMOUNT + 1);
      int py = pointsY[idx] + random(-NOISE_AMOUNT, NOISE_AMOUNT + 1);

      dacWrite(DAC_X, constrain(px, 0, 255));
      dacWrite(DAC_Y, constrain(py, 0, 255));

      idx = (idx + 1) % numPoints;
      delayMicroseconds(20);
    }
  }
}
