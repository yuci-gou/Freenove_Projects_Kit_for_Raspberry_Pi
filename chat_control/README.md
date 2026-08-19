# Freenove 套件聊天控制（chat_control）

通过 DSH 聊天调用 `kitctl.py` 控制面包板上的器件。

## 当前支持

### LED（默认 GPIO17）
```bash
python3 chat_control/kitctl.py led on       # 点亮（状态保持）
python3 chat_control/kitctl.py led off      # 熄灭
python3 chat_control/kitctl.py led status   # 只读查询（不改变硬件状态）
python3 chat_control/kitctl.py led blink --times 3 --interval 0.3   # 闪 3 次
python3 chat_control/kitctl.py led blink --forever                    # 常闪（后台任务，随时可停）
```

接线（Freenove 教程第 1 课 Blink）：
LED 阳极 → 220Ω 电阻 → GPIO17，LED 阴极 → GND。

其他引脚：`--pin N`（BCM 编号）。

## 常见课程默认引脚（供扩展参考）
| 器件 | 引脚 | 课程 |
|------|------|------|
| LED | GPIO17 | 01 Blink |
| RGB LED | GPIO17/18/27 | 04 RGBLED |
| 按键 | GPIO18/26 | 03 ButtonLED |
| 蜂鸣器 | GPIO18 | 06 Buzzer |
| 舵机 | GPIO12 | 08 Servo |

> 上表待与套件代码逐一核对后再扩充命令。
