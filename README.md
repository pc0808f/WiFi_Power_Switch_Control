# WiFi_Power_Switch_Control
這是用來控制IPC電源的控制版

一共有控制了
一個按鍵
一組電源MOS。5V和12V 各二個控制腳
一個WS2812LED

### 有以下功能
1. 連接WIFI
2. 可被設定WIFI
3. 連接MQTT
4. 可以由MQTT進行OTA指令
5. 可以由MQTT進行上電指令
6. 可以由MQTT進行斷電指令
7. 預設系統在電供上電後3秒才送電
8. 按鍵可以開關電。
9. 開機後，長按按鍵開機可以重設WIFI


### 燈號說明
|  燈號   | 說明  |
|  ----  | ----  |
|  綠燈0.5秒閃  | 開機上電  |
| 綠燈常亮  | 正常連到WIFI |
| 紅燈  | 連線WIFI失敗 |
| 黃燈0.5秒內  | 進入配WIFI模式 |
| 黃燈1秒閃  | 進入設完WIFI但要試著連WIFI中 |
| 黃燈常亮  | 進入OTA中 |



### 參考程式
```python
from machine import Pin
import machine
import neopixel
import time

# 定義IO口
IO_SW1_PIN = 0   # 輕觸按鍵
IO_5V_EN_PIN = 16  # 控制5V輸出的IO
IO_12V_EN_PIN = 2  # 控制12V輸出的IO

# 初始化IO
IO_SW1 = Pin(IO_SW1_PIN, Pin.IN)
IO_5V_EN = Pin(IO_5V_EN_PIN, Pin.OUT)
IO_12V_EN = Pin(IO_12V_EN_PIN, Pin.OUT)

# 初始狀態設定
IO_5V_EN.value(0)
IO_12V_EN.value(0)
Power_EN = 0

# 定義WS2812的參數
NUM_LEDS = 1
PIN = 5  # 這是WS2812數據輸入的引腳

# 初始化WS2812
np = neopixel.NeoPixel(machine.Pin(PIN), NUM_LEDS)

# 定義彩虹顏色
rainbow_colors = [
    (255, 0, 0),    # 紅色
    (255, 127, 0),  # 橙色
    (255, 255, 0),  # 黃色
    (0, 255, 0),    # 綠色
    (0, 0, 255),    # 藍色
    (75, 0, 130),   # 靛色
    (148, 0, 211),   # 紫色
    (0, 0, 0),       # 黑色
    (255, 255, 255) # 白色
]
rainbow_colors_count = len(rainbow_colors)
color = rainbow_colors_count-1

while True:
   
    if IO_SW1.value() == 0: # 按鍵按下
        # 按一次，Power_EN反轉
        Power_EN = 1-Power_EN
        IO_5V_EN.value(Power_EN)
        IO_12V_EN.value(Power_EN)
        # 等待按鍵釋放
        while IO_SW1.value() == 0:    
            # 持續一段時間，這裡是0.1秒
            time.sleep(0.1)

    else:    # 按鍵放開 
 
        color = color + 1
        if color == rainbow_colors_count:
            color = 0
            
        # 依次設置每個LED的顏色
        np[0] = rainbow_colors[color]
        np.write()

        # 持續一段時間，這裡是0.5秒
        time.sleep(0.5)
```


### MQTT指令
### 重開小卡 API格式表

#### 定義

在SQL的小卡表中，每張小卡在初始化時會寫入一個token，利用這個token做為mqtt的id

1. 確定設備ID：每個設備都有一個唯一的ID，以確保每個設備都可以被識別和管理。
2. 安全性：使用安全性協議（如TLS / SSL）以保護設備和資料的安全。
3. 適當的資料結構：使用結構化資料，如JSON格式，以方便資料的處理和存儲。
4. 主題（Topic）：

在自動販賣機的營業狀況收集，設計以下TOPIC：

電源小卡專用 16byte powerID: 03ac6a6316d8fd2c7401249b6ca30a06 

1. powerID/cardid/token/status：設備狀態主題。此主題用於通報自動販賣機的狀態，例如：正在運行中，停止運行，庫存不足等。
2. ~~(無使用)cardid/token/sales：銷售統計主題。此主題用於收集自動販賣機的銷售統計數據，例如：每個產品的銷售量，銷售總額等。~~
3. powerID/cardid/token/commands：命令主題。此主題用於向自動販賣機發送命令，例如：開啟或關閉自動販賣機，啟動或停止維護模式等。
4. powerID/cardid/token/commandack：回覆命令主題。此主題用於回覆指令執行結果。
5. powerID/cardid/token/fota：fota主題。此主題用於要求小卡執行更新動作。
6. ~~(無使用)cardid/token/getsetting：取得娃娃機參數。~~



## 細部內容

cardid/token/status
pub:card
sub:serv
content

```json
{
"status":"error code",
"mode":"on" or "off"
"time":15XXXX000
}
```

cardid/token/commands
pub:serv
sub:card
content

```json
{
"commands":"cmd code",
"parameter1":"",   //預留
"parameter2":"",   //預留
"parameter3":"",   //預留
“time”:15XXXX000
}
```

cardid/token/commandack

pub:card
sub:serv
content

```json
{
"ack":"ack code",
"parameter1":"",   //預留
"parameter2":"",   //預留
"parameter3":"",   //預留
"time":15XXXX000
}
```
---
### Fota 使用說明:要求
powerID/cardid/token/fota
pub:serv
sub:card
#####　content說明
file_list要更新的列表 ex: "otatest1.py, otatest2.py"
password : 專用密碼
time : 時間
state : 代表本次通訊的必token, 回傳同token表示同指令

```json
{
  "file_list": "otatest1.py, otatest2.py, Data_Collection_Main_0525v4RX_task.py",
  "password": "90eef838-9b5b-47ae-9111-b2b1063376a9",
  "state" : "21f27b7f-d741-414e-8fc3-bcee395463f6",
  "time": 15000
}
```

### Fota 使用說明:回應
powerID/cardid/token/fotaack
pub:card
sub:serv
#####　content說明
ack: "OK"  OK表接受
time : 卡片上的時間
state : 代表本次通訊的必token, 回傳同token表示同指令

```json
{
  "ack": "OK",
  "state" : "21f27b7f-d741-414e-8fc3-bcee395463f6",
  "time": 15000
}
```
---
       

測試用指令

**ping-pong**
cardid/token/commands
11223344556677/9E53A146-6335-4FD3-82EA-37B6C423EFD3/commands

```json
{
"commands":"ping",
"time":15000
}
```

回覆

cardid/token/commandack
11223344556677/9E53A146-6335-4FD3-82EA-37B6C423EFD3/commandack
{"commands":"ping",
"time":15000
}

```json
{
"ack":"pong",
"time":15XXXX000
}
```

**要求狀態**

cardid/token/commands
11223344556677/9E53A146-6335-4FD3-82EA-37B6C423EFD3/commands

```json
{
"commands":"getstatus",
"time":15XXXX000
}
```

回覆

cardid/token/status
11223344556677/9E53A146-6335-4FD3-82EA-37B6C423EFD3/status
content

```json
{
"status":"error code",
"mode":"on" or "off",
"time":15XXXX000
}
```

打開IPC
cardid/token/commands
11223344556677/9E53A146-6335-4FD3-82EA-37B6C423EFD3/commands

```json
{
"commands":"on",
"state":"UUID",
"time":15XXXX000
}
```

回覆
cardid/token/commandsack
11223344556677/9E53A146-6335-4FD3-82EA-37B6C423EFD3/status

content

```json
{
"ack":"on",
"state":"UUID",
"time":15XXXX000
}
```

關閉IPC
cardid/token/commands
11223344556677/9E53A146-6335-4FD3-82EA-37B6C423EFD3/commands

```json
{
"commands":"off",
"state":"UUID",
"time":15XXXX000
}
```

回覆

cardid/token/commandsack
11223344556677/9E53A146-6335-4FD3-82EA-37B6C423EFD3/status

content

```json
{
"ack":"off",
"state":"UUID",
"time":15XXXX000
}
```

重開IPC，關3秒，再打開IPC

cardid/token/commands
11223344556677/9E53A146-6335-4FD3-82EA-37B6C423EFD3/commands

```json
{
"commands":"restart",
"state":"UUID",
"seconds": 3,
"time":15XXXX000
}
```

回覆

cardid/token/commandsack
11223344556677/9E53A146-6335-4FD3-82EA-37B6C423EFD3/status

content

