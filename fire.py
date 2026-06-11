from ultralytics import YOLO
import cvzone
import cv2
import time
import requests
import serial

TELEGRAM_TOKEN = "8444362394:AAES5NXrdWyDckK4I_Ezdp8jWS1JIvfWeEk"
CHAT_ID = "7830763313"

MODEL_PATH = "fire.pt"
ARDUINO_PORT = "COM4"
ARDUINO_BAUD = 9600

FIRE_CONFIRM_FRAMES = 10
MIN_CONFIDENCE = 50
ALERT_COOLDOWN = 15

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(0)

fire_frame_count = 0
last_alert_time = 0
arduino_state = "SAFE"
gas_percent = 0

try:
    arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
    time.sleep(2)
except:
    arduino = None

def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def send_tg_photo(path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (640, 480))
    results = model(frame, stream=True)

    fire_detected = False

    for info in results:
        for box in info.boxes:
            confidence = float(box.conf[0]) * 100
            if confidence >= MIN_CONFIDENCE:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 3)
                cvzone.putTextRect(frame, f"Fire {int(confidence)}%", [x1+8, y1+30], scale=1, thickness=2)
                fire_detected = True

    if fire_detected:
        fire_frame_count += 1
    else:
        fire_frame_count = 0

    if fire_frame_count >= FIRE_CONFIRM_FRAMES:
        img_path = "fire_alert.jpg"
        cv2.imwrite(img_path, frame)

        if arduino:
            arduino.reset_input_buffer()
            arduino.write(b'1')
            start_time = time.time()
            while time.time() - start_time < 1:
                if arduino.in_waiting:
                    line = arduino.readline().decode(errors='ignore').strip()
                    if line.startswith("STATE:"):
                        parts = line.split(", GAS LEVEL: ")
                        if len(parts) == 2:
                            arduino_state = parts[0].split(": ")[1]
                            try:
                                gas_percent = float(parts[1])
                            except:
                                gas_percent = 0
                    if "FIRE_DETECTED" in line:
                        if time.time() - last_alert_time > ALERT_COOLDOWN:
                            send_tg_photo(img_path, "🔥 FIRE CONFIRMED!")
                            send_tg_message("⚠️ Emergency! Fire verified!")
                            last_alert_time = time.time()
                        break
                    elif "NO_FIRE" in line:
                        break
    else:
        if arduino:
            arduino.write(b'0')
            arduino_state = "SAFE"

    cv2.putText(frame, f"Fire frames: {fire_frame_count}/{FIRE_CONFIRM_FRAMES}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
    cv2.putText(frame, f"Gas: {gas_percent:.1f}%", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
    cv2.putText(frame, f"State: {arduino_state}", (10,90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255) if arduino_state=="DANGER" else (0,255,0), 2)
    cv2.imshow("🔥 Fire Detection System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()
