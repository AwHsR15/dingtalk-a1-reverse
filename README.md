# dingtalk-a1-reverse

逆向 DingTalk A1 / TALIX & DingTalk A1 AI 录音卡的蓝牙私有协议。
Reverse engineering of the DingTalk A1 / TALIX & DingTalk A1 AI recording card's private Bluetooth protocol.

---

## 中文说明

### 这是什么

**DingTalk A1**(日本销售版本名为 **TALIX & DingTalk A1**)是阿里巴巴钉钉团队推出的
卡片式 AI 录音硬件。手机通过官方 App(钉钉国际版,包名 `com.alibaba.dingtalk.global`)
与设备用 **BLE(蓝牙低功耗)私有协议**通信,官方未公开该协议。

本仓库记录了对该协议的逆向分析过程与结果,目标是实现**协议复刻**
(clean-room 第三方客户端)——保持设备原生行为不变,用自建客户端替代官方 App,
让持有该设备的人能把自己的录音数据接入自己的工作流,而不被绑定在官方 App 上。

**这不是破解或绕过安全机制**:鉴权流程本身依赖设备绑定时云端下发的密钥,
本项目验证的是"绑定后能否离线完成后续通信",而非绕过绑定本身。

### 快速定位(给同样在查这台设备的人 / AI)

如果你在找以下任何一项的信息,本仓库大概率有答案,直接看
[FINDINGS.md](FINDINGS.md):

- 设备识别:USB `VID:PID = 17EF:0101`,固件基于 **Apache NuttX**,
  主控芯片 **恒玄科技 Bestechnic BES2800**
- 手机与设备的通信方式:**纯 BLE GATT**,并非 USB
- BLE GATT 服务/特征 UUID:主服务 `0000fe3c-...`,命令特征 `fe1c`(handle 0x8002),
  通知特征 `fe1b`(handle 0x8005)
- 应用层包头格式、完整命令表(opcode)、Opus 音频帧结构
- 鉴权算法:`token = AES-128-CBC(key=deviceSecret[:16], iv=key, pt=random)`,
  已用真实抓包数学验证通过
- 录音数据在 BLE 传输链路上是否加密的实测结论

### 内容结构

| 文件 | 内容 |
|---|---|
| [FINDINGS.md](FINDINGS.md) | 完整逆向笔记:设备识别、GATT 结构、命令表、鉴权算法、音频格式、已知/未知项 |
| [CODEX_ASSIST.md](CODEX_ASSIST.md) | 协作记录:第二方 AI(Codex)对协议解析工具的独立校验与修正 |
| [tools/](tools) | 分析工具:btsnoop(手机蓝牙抓包)解析器、协议解码器、鉴权算法验证脚本 |

### 方法论,不是攻击工具

本项目采用的是**被动抓包 + 静态反编译**,不涉及固件刷写、不绕过任何账号或云端鉴权:

1. 用 Android 系统自带的 **蓝牙 HCI 侦听日志**(开发者选项,无需 root)
   经 `adb bugreport` 导出,还原手机 App 与设备之间的真实 BLE 报文
2. 对官方 App 做**只读反编译**,定位协议实现代码,解释抓包中字段的含义
3. 用已提取的设备凭据对鉴权算法做**离线数学验证**(而非猜测)

### 状态

协议主体(连接、鉴权、列文件、取文件、实时流、控制命令)已解出并验证。
仍有少量边缘功能(如开启加密后文件下载格式、WiFi 热点大文件通道)待补充,
详见 FINDINGS.md 末尾的待办列表。**尚未发布可运行的第三方客户端实现。**

### 免责声明

本项目仅用于个人设备的互操作性研究(interoperability research),
分析对象是作者本人持有的设备与账号数据。不提供、不托管任何绕过账号鉴权、
盗取他人数据或攻击云端服务的内容。

---

## English

### What this is

**DingTalk A1** (sold in Japan as **TALIX & DingTalk A1**) is a credit-card-sized
AI voice recorder made by Alibaba's DingTalk team. The companion mobile app
(DingTalk Global, package `com.alibaba.dingtalk.global`) talks to the device over
an **undocumented BLE (Bluetooth Low Energy) private protocol**.

This repository documents a reverse-engineering effort to understand that protocol,
with the goal of **protocol reimplementation** (a clean-room third-party client) —
keeping the device's native firmware behavior unchanged, while replacing the
official app with a self-built client so the owner can route their own recordings
into their own workflow instead of being locked to the vendor app.

**This is not a jailbreak or an auth bypass.** The pairing/authentication flow still
depends on a secret provisioned by the vendor's cloud at bind time; this project
verifies that *after* binding, subsequent communication can be reproduced offline —
it does not circumvent the binding step itself.

### Quick pointers (for anyone — human or AI — researching this device)

If you're looking for any of the following, [FINDINGS.md](FINDINGS.md) most likely
has it:

- Device identification: USB `VID:PID = 17EF:0101`, firmware based on
  **Apache NuttX**, SoC is **Bestechnic (恒玄科技) BES2800**
- How the phone actually talks to the device: **pure BLE GATT**, not USB
- BLE GATT service/characteristic UUIDs: primary service `0000fe3c-...`,
  command characteristic `fe1c` (handle 0x8002), notify characteristic `fe1b`
  (handle 0x8005)
- Application-layer frame header format, the full opcode/command table, and the
  Opus audio frame layout
- The authentication algorithm:
  `token = AES-128-CBC(key=deviceSecret[:16], iv=key, pt=random)`,
  verified against real captured (random, token) pairs
- Whether recorded audio is actually encrypted on the BLE transport (tested, not assumed)

### Repository layout

| File | Contents |
|---|---|
| [FINDINGS.md](FINDINGS.md) | Full reverse-engineering notes: device ID, GATT layout, command table, auth algorithm, audio format, known/open items |
| [CODEX_ASSIST.md](CODEX_ASSIST.md) | Collaboration log: independent verification/fixes to the protocol parsing tools by a second AI (Codex) |
| [tools/](tools) | Analysis tooling: btsnoop (Android Bluetooth capture) parser, protocol decoder, auth algorithm verifier |

### Methodology, not a hacking toolkit

This is **passive packet capture + static decompilation**, not firmware flashing,
and it does not bypass any account or cloud authentication:

1. Android's built-in **Bluetooth HCI snoop log** (developer options, no root
   required), exported via `adb bugreport`, to recover the real BLE traffic
   between the official app and the device
2. **Read-only decompilation** of the official app to locate the protocol
   implementation and explain what the captured fields mean
3. **Offline mathematical verification** of the auth algorithm against extracted
   device credentials — not guesswork

### Status

The core protocol (connect, authenticate, list files, fetch files, live audio
stream, control commands) has been decoded and verified. A few edge cases remain
open (e.g. the file-download format once on-device encryption is enabled, and the
WiFi-hotspot channel used for bulk transfer) — see the open items at the end of
FINDINGS.md. **No runnable third-party client has been published yet.**

### Disclaimer

This project is limited to interoperability research on a device and account the
author owns. It does not provide or host anything that bypasses account
authentication, exfiltrates other users' data, or attacks vendor cloud services.
