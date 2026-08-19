#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 名字: yuci
"""
kitctl.py — Freenove 套件聊天控制入口（供 DSH 代理通过 bash 调用）

用法：
  python3 kitctl.py led on                     # 点亮 LED（状态保持）
  python3 kitctl.py led off                    # 熄灭 LED
  python3 kitctl.py led status                 # 只读查询引脚真实状态（不改动硬件）
  python3 kitctl.py led blink --times 5        # 闪烁 5 次
  python3 kitctl.py led blink --forever        # 一直闪（应以后台任务运行，用 job_kill 停止）
  python3 kitctl.py led blink --interval 0.2   # 自定义闪烁间隔(秒)

默认引脚 GPIO17（Freenove 教程第 1 课 Blink：LED 阳极经 220Ω 电阻接 GPIO17，
阴极接 GND）。其他引脚用 --pin N 指定（BCM 编号）。
"""
import argparse
import mmap
import os
import struct
import sys
import time

try:
    import RPi.GPIO as GPIO
except Exception as e:  # pragma: no cover
    print(f"ERROR: 无法加载 RPi.GPIO: {e}", file=sys.stderr)
    sys.exit(1)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# BCM2711 (Raspberry Pi 400) GPIO 寄存器偏移（/dev/gpiomem 从 0 开始映射）
GPFSEL0_OFF = 0x00
GPFSEL1_OFF = 0x04
GPLEV0_OFF = 0x34

FUNC_NAMES = {0b000: "输入", 0b001: "输出", 0b100: "复用功能0",
              0b101: "复用功能1", 0b110: "复用功能2", 0b111: "复用功能3",
              0b010: "复用功能4", 0b011: "复用功能5"}


def read_gpio_state(pin: int):
    """通过 /dev/gpiomem 只读 GPIO 功能与电平，不改变任何引脚状态。"""
    fd = os.open("/dev/gpiomem", os.O_RDONLY)
    try:
        m = mmap.mmap(fd, 4096, prot=mmap.PROT_READ)
        try:
            fsel = (struct.unpack("<I", m[GPFSEL0_OFF:GPFSEL0_OFF + 4])[0],
                    struct.unpack("<I", m[GPFSEL1_OFF:GPFSEL1_OFF + 4])[0])
            lev = struct.unpack("<I", m[GPLEV0_OFF:GPLEV0_OFF + 4])[0]
        finally:
            m.close()
    finally:
        os.close(fd)

    if pin < 32:
        func = (fsel[pin // 10] >> ((pin % 10) * 3)) & 0b111
        level = (lev >> pin) & 1
    else:
        raise ValueError(f"引脚 {pin} 超出可读范围(0-31)")
    return func, level


def led_on(pin: int):
    # 注意：不调用 cleanup，进程退出后引脚保持输出高电平，LED 持续点亮
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
    print(f"OK: LED(GPIO{pin}) 已点亮，输出高电平，状态保持")


def led_off(pin: int):
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    time.sleep(0.05)
    GPIO.cleanup(pin)  # 释放引脚回输入态
    print(f"OK: LED(GPIO{pin}) 已熄灭")


def led_status(pin: int):
    func, level = read_gpio_state(pin)
    fname = FUNC_NAMES.get(func, f"未知({func:#05b})")
    if func == 0b001:
        state = "亮" if level else "灭"
        print(f"OK: GPIO{pin} 功能={fname}, 电平={'高' if level else '低'} → LED {state}")
    else:
        print(f"OK: GPIO{pin} 功能={fname}, 电平={'高' if level else '低'}（当前未配置为 LED 输出）")


def led_blink(pin: int, times: int, interval: float, forever: bool):
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    n = 0
    try:
        while forever or n < times:
            GPIO.output(pin, GPIO.HIGH)
            print(f"[{time.strftime('%H:%M:%S')}] LED ON  (第 {n + 1} 次)", flush=True)
            time.sleep(interval)
            GPIO.output(pin, GPIO.LOW)
            print(f"[{time.strftime('%H:%M:%S')}] LED OFF", flush=True)
            if not forever:
                n += 1
            time.sleep(interval)
        print(f"OK: 闪烁 {times} 次完成，LED 已熄灭")
    except KeyboardInterrupt:
        print("OK: 闪烁已停止，LED 已熄灭")
    finally:
        GPIO.cleanup(pin)


def main():
    p = argparse.ArgumentParser(description="Freenove 套件聊天控制")
    p.add_argument("device", choices=["led"], help="要控制的器件")
    p.add_argument("action", choices=["on", "off", "status", "blink"], help="动作")
    p.add_argument("--pin", type=int, default=17, help="GPIO 引脚（BCM 编号，默认 17）")
    p.add_argument("--times", type=int, default=5, help="blink 次数（默认 5）")
    p.add_argument("--interval", type=float, default=0.5, help="blink 间隔秒数（默认 0.5）")
    p.add_argument("--forever", action="store_true", help="blink 无限循环（配合后台任务使用）")
    args = p.parse_args()

    if not (0 <= args.pin <= 53):
        print(f"ERROR: 无效引脚 {args.pin}（应为 0-53 的 BCM 编号）", file=sys.stderr)
        sys.exit(2)
    if args.interval <= 0:
        print("ERROR: --interval 必须大于 0", file=sys.stderr)
        sys.exit(2)

    if args.action == "on":
        led_on(args.pin)
    elif args.action == "off":
        led_off(args.pin)
    elif args.action == "status":
        led_status(args.pin)
    elif args.action == "blink":
        led_blink(args.pin, args.times, args.interval, args.forever)


if __name__ == "__main__":
    main()
