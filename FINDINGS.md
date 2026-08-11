# DingTalk A1 / TALIX A1 逆向笔记

设备:TALIX & DingTalk A1(日本版),USB 连接 Windows 11
记录时间:2026-08-11

---

## 1. 设备识别(已确认)

用 `LastArrivalDate` 属性锁定 —— 全系统唯一在插入时间点出现的 USB 设备:

| 项目 | 值 |
|---|---|
| 插入时间 | 2026/8/11 11:15:55(其余 USB 设备均为前一日开机枚举) |
| VID:PID | `17EF:0101` |
| bcdDevice | `1010` |
| iManufacturer | **`NuttX`** |
| iProduct | `Composite device` |
| iSerial | `8SSA81U51391SG00235S` |
| 设备类 | 复合设备(Composite),2 个接口 |

**关于 VID `17EF`**:该 VID 注册在 Lenovo 名下,但设备并非联想制造。
复用现成 VID:PID 以规避 USB-IF 年费(约 5000 USD)是小厂常见做法。
序列号采用联想的 `8S` 前缀 SN 格式,说明固件的 USB 描述符是从某个
联想方案模板复制而来 —— 这本身是固件溯源的线索。

## 2. 接口结构

### MI_00 — 伪 ADB 接口(死端)

- 特征码 `Class_ff & SubClass_42 & Prot_01`,即 Android ADB 的标准三元组
- Windows 因此自动挂载 `android_winusb.inf` / WinUSB 驱动
- `adb devices` **能识别**:`8SSA81U51391SG00235S`,但状态恒为 `offline`

握手失败的确切位置(ADB_TRACE=all 抓取):

```
packet --> CNXN
to remote: [CNXN] arg0=0x1000001 arg1=0x100000 (len=302) host::features=...
usb_write 24                                     <- 24 字节包头发出
AdbWriteEndpointSync failed: 信号灯超时 (121)     <- 写 payload 超时
Kicking device due to error in usb_write
```

**结论**:bulk OUT 端点无人消费。注意状态是 `offline` 而非 `unauthorized`,
说明并非授权问题,而是固件侧根本没有 adbd 在服务该端点。
接口描述符存在但功能未启用 —— 编译进来了没跑,或需特定条件激活。

### MI_01 — 厂商私有 HID 通道(主目标)

| 项目 | 值 |
|---|---|
| UsagePage / Usage | `0xFF00` / `0x0001`(厂商自定义) |
| Input report | 128 字节 |
| Output report | 128 字节 |
| Feature report | 0 |

被动监听 20 秒:**0 个报告**。设备不主动上报,是请求-响应式协议
(主机发 Output report,设备回 Input report)。

这是设备的实际控制通道,协议格式未知。

## 3. 硬件平台

- **SoC:恒玄科技 BES2800**(6nm 低功耗 AI 音频芯片)
- 本地存储 64GB
- 6 麦克风阵列(5 全向 + 1 骨传导),660mAh 电池
- 尺寸 60×91.6×3.8mm,正面 0.95 英寸彩色屏

### 交叉验证:为什么 `NuttX` 这条线很关键

1. USB 描述符自报 manufacturer = `NuttX`
2. 恒玄 BES26xx/28xx 平台支持已合并进 Apache NuttX 上游主线
3. atc1441 对小米手环 9/10(BES2700iMP / BEST1503)的逆向确认其固件是
   **Vela/NuttX-based** —— 小米 Vela 正是基于 Apache NuttX 的 IoT OS

三点互相印证:该设备的 OS 层是 Apache NuttX,**源码公开可读**。
USB 栈(`drivers/usbdev/`)、composite 驱动、以及 NuttX 自带的
microADB 实现(`apps/system/adb`,恰好解释了那个空壳 ADB 接口的来源)
都可以直接对照源码分析。

## 4. 同平台参考资料

**atc1441/MiBand10-BES2700iMP-BEST1503-Hacking** —— 同代恒玄芯片的完整逆向 + 定制固件。

关键方法论:
- **UART 是主接口**,921600 baud,通过设备上的测试点
- SecondStage bootloader 的 `.bin`(覆盖所有 BEST 变体)来自泄露的烧录工具
- 作者用 Python 写了走 UART 的 flasher 与自动化测试脚本
- 未使用 SWD/JTAG

## 5. 连接方式(已由用户确认 —— 修正早期误判)

| 链路 | 介质 | 用途 |
|---|---|---|
| 手机 ↔ A1 | **蓝牙** | **主数据通道**,配合 DingTalk App 工作 |
| PC ↔ A1 | USB-C | 充电 + 那条私有 HID 通道 |

**早期误判修正**:最初假设手机也经 USB 与设备通信,错误。
设备主控 BES2800 本就是蓝牙音频 SoC,主通道走蓝牙才符合设计。

因此 **USB 上的 `MI_01` HID 通道并非手机所用的通道**,其真实用途推测为
固件升级(DFU)或工厂测试。它仍有逆向价值(可能是刷写/取数的后门),
但**不是复刻"手机运作模式"的目标**。

**目标通道 = 蓝牙。**

### PC 侧蓝牙能力:不可用
本机所有蓝牙适配器(RZ616 `0489:E0D9`、MediaTek `04CA:3804`)状态均为
`Unknown`,即当前不在线;`bthserv` / `BTAGService` 服务在运行但无硬件。
PC 侧无法参与蓝牙抓包,除非外接 USB 蓝牙适配器。

## 6. 目标与路线

**目标(用户定义)**:保持设备原生行为不变,复刻手机 App 与设备之间的
蓝牙协议,用自建客户端替换官方上位机,把数据接入自有流程。
即 **协议复刻 / 第三方客户端**(clean-room client),不改固件、不刷写。

### 路线 A — 手机侧抓蓝牙 HCI 日志(首选,零风险,无需 root)
Android 开发者选项自带「蓝牙 HCI 侦听日志」。开启后用 App 正常操作设备,
再经 `adb bugreport` 导出(bugreport 内含 btsnoop 日志,**不需要 root**),
用 Wireshark 分析完整 GATT/SPP 报文。

这是复刻蓝牙协议的标准做法,信息完整度最高,且完全被动。

### 路线 B — 反编译 DingTalk App
用于解释路线 A 抓到的报文语义、定位加密密钥。
风险:钉钉是阿里系大型商业 App,大概率有加固,可能需脱壳。
定位为**路线 A 的辅助**,而非主攻。

### 路线 C — 盲探测 USB HID 通道
向 Output report 发探测包观察响应。**有风险** —— 未知命令可能触发擦除、
恢复出厂或固件写入。且该通道并非目标通道,优先级低。

### 路线 D — 硬件侧 UART(需拆机,用户已表示暂不拆)
按 atc1441 的路径找测试点接 UART,可取启动日志、可能进 bootloader。
信息量最大但需拆机。**暂缓。**

## 7. BLE 协议(已由 btsnoop 抓包实证)

抓包来源:手机侧 btsnoop HCI 日志,经 `adb bugreport` 导出(无需 root)。
解析工具见 `tools/btsnoop_gatt.py`、`tools/protocol_analyze.py`。

### 7.1 GATT 结构

| | UUID | handle | 属性 |
|---|---|---|---|
| 主服务 | `0000fe3c-0000-1000-8000-00805f9b34fb` | 0x8000-0x80ff | — |
| 命令通道 | `0000fe1c-...` | **0x8002** | read / write / write-no-rsp |
| 通知通道 | `0000fe1b-...` | **0x8005** | read / notify |

协商 MTU = **517**(BLE 上限)。单次 ATT 负载上限实测 507 字节。

### 7.2 包头格式

```
[0]     类型      0x13 = 主机→设备 / 0x31 = 设备→主机
[1]     版本      恒为 0x01
[2]     命令 ID
[3]     序列号    逐包递增
[4:7]   保留      0x000000
[7]     长度      payload 字节数
[8:]    payload   明文 JSON,或二进制数据
```

超过单包容量的数据由后续**分片续包**承载(续包不带上述包头)。

### 7.3 完整命令表(来自 APK 反编译 `DingerCommandHelper`,未混淆)

命令 ID 为 **16 位大端**,占包头 byte[1:3](早期误判为"版本"字段,已修正:
`13 01 32` = cmd 0x0132 = 306 = SyncDevStatus)。下表 cmd 值为完整 16 位。

| cmd(hex) | 方法 | 功能 | 参数 |
|---|---|---|---|
| `0x0004` | sendResetDevice | **恢复出厂/重置** | did |
| `0x0008` | sendGetRandom | 取 challenge | corpId, did → `{"random":"<32hex>"}` |
| `0x0009` | sendAuth | **鉴权应答** | timestamp, **payload**, did |
| `0x0100` | sendAudioRecordOpt | 录音控制 | did, action(start/stop), params |
| `0x0110` | sendGetFileList | 列文件 | did, s_fid, e_fid, recently |
| `0x0112` | sendFileSyncCancel | 取消文件同步 | did |
| `0x0113` | sendFileDelete | **删除文件** | did, fid |
| `0x0120` | sendOpenAp | **开 WiFi 热点** | did, type |
| `0x0121` | sendCloseAp | 关 WiFi 热点 | did |
| `0x0130` | sendGetTransInfo | 获取传输信息 | corpId |
| `0x0132` | sendSyncDevStatus | 同步设备状态 | did |
| `0x0133` | sendConnectDevice | 连接设备 | corpId, did, **token**, model, timestamp, sdk_ver |
| `0x0134` | sendDisconnectDevice | 断开 | corpId, did |
| `0x0135` | sendQueryFwVersion | **查固件版本/OTA** | did, new_ver |
| `0x0136` | sendSysControl | 系统控制 | did, key, val |
| `0x0137` | sendGraySwitch | 灰度开关 get/set/control | did, action, params |

文件/流相关的响应侧 opcode(抓包实证):`0x14` 文件属性、`0x15` 文件数据、
`0x16` 流属性、`0x17` 实时流数据。

**`fid` = Unix 时间戳**,即录音起始时刻(如 `1786416245`)。

### 7.3.1 重大发现:双传输通道

`sendOpenAp`/`sendCloseAp` 表明设备内置 **WiFi 热点**。推测大文件(64GB 存储)
走 WiFi 传输,BLE 仅用于控制与实时流(BLE 带宽不可能搬完整录音库)。
这是之前完全未预料到的第二条数据通道,值得单独调查。

### 7.4 音频帧格式(cmd 0x17,固定 124 字节)

```
[0:8]     13 01 17 <seq> 00 00 00 74     通用头,0x74 = 116 = payload 长度
[12:16]   6a 7a 8d 7d                    fid(大端 Unix 时间戳)
[24:28]   00 00 00 01                    块序号
[28:32]   00 00 00 54                    音频数据长度 = 84
[36:120]  4b 41 01 1b ...                Opus 数据(84 字节)
[120:124] 5a 5a 5a 5a                    填充
```

首字节为 **Opus TOC**:`0x4b`/`0x48` → `config=9`(SILK 宽带,20ms 帧),多包一致。

### 7.5 关于加密 —— 已用对照实验证实

做了两轮抓包:**加密关闭**(bugreport.zip)与 **App 内开启加密**
(bugreport3_enc.zip)。修正应用层分片重组后,需把实时流与累计日志中的历史
文件下载分开判断:

| 通道 | 加密关闭 | 加密开启 |
|---|---|---|
| `0x0117` 实时流 | 熵 6.912 | 熵 6.952 |
| `0x0115` 文件数据 | 71040B,熵 7.920 | 71040B,熵 7.920 |

`0x0117` 在开启加密后仍能直接看到稳定的 Opus TOC 与帧结构,因此**实时流
仍是明文 Opus**。但 `0x0115` 不能用上表证明:两份 bugreport 中的三条文件
payload 长度均为 14124/14972/41944 字节,SHA-256 指纹也逐条完全相同
(`16189b7b...` / `57df8624...` / `dc12e813...`)。这是 Android 累计 btsnoop
重复包含了同一批历史传输,并非独立的开关前/后样本。

> **当前可证实:App 端加密开关不影响 `0x0117` 实时流。**
> **尚不能断言 `0x0115` 文件下载始终为明文。**需要在开启加密后新建录音、
> 清空/截断旧 btsnoop 后单独下载该新文件,再检查新 fid 的 payload。

**工具状态(2026-08-11 Codex 协助修复)**:`tools/protocol_analyze.py` 已按
8 字节头中的 32 位大端长度重组跨 ATT 的 507 字节续片,不再把续片误列为
伪命令(如 `0x082B`)。真实抓包由 2942 个 ATT 片段重组为 2804 条完整消息,
长度校验 2804/2804 全部通过;离线回归测试见 `tools/test_protocol_reassembly.py`。

### 7.6 补充命令与字段(来自 bugreport3_enc.zip)

- 电量查询:`sysControl`(0x136)`{"did":..,"key":"battery_key"}`
- 完整能力位:`cap_aikey_option` / `cap_incognitomode` / `cap_remark`
  / `cap_schedule` / `cap_voiceprint`
- 新命令 `0x013F`(用途待定)
- 流/文件属性新字段:`alg_mode`、`sid`、`fsync`、`stream_type`(0/3/4)
- 声纹:`{"action":"start/stop","type":"voice_print"}`(经 0x0100/0x0101)

## 8. 尚未掌握的功能

设备能力位声明存在、但本轮抓包未触发,因而协议未知:

- [ ] `cap_voiceprint` 声纹
- [ ] `cap_aikey_option` AI 按键
- [ ] `cap_sched*` 定时相关
- [ ] 删除文件
- [ ] OTA 固件升级
- [ ] 时间同步
- [ ] 电量查询
- [ ] **加密开启后新录音的 `0x0115` 文件下载格式**

## 9. 鉴权流程与离线可行性(已解决)

反编译 `m62.java`(业务层)得到完整鉴权链:

```java
// 1. 取 deviceSecret(本地缓存,见下)
String secret = if7.q().o(deviceId);          // if7.java:215

// 2. 发 getRandom(cmd 0x08),设备回 challenge
//    从 response.body.random 取出 32 位 hex 字符串

// 3. 用 deviceSecret 作 AES 密钥,加密 random 得到 payload
String payload = DingerAudioTools.AESEncrypt(secret, random);   // m62.java:775

// 4. 发 auth(cmd 0x09):{timestamp, payload, sdk_ver}
```

### deviceSecret 的来源与持久化(关键判断)

- `deviceSecret` 是 `DeviceModel` 的 `@FieldId(19)` 字段,`DeviceModel` 用
  `com.laiwang.idl.Marshal` 序列化 —— 即**钉钉云端 RPC 返回结构**。
  该字段在设备**绑定**时由云端下发。
- 绑定后,`DeviceModel` 被缓存在本地(`if7.l()` 日志明写
  `read from cache` / `from cache`)。鉴权时 `if7.q().o(deviceId)` **同步从
  本地缓存取**,无网络调用。

### 结论(已从 root 设备提取凭据 + 数学验证)

**离线鉴权已 100% 验证可行。** 实际鉴权走 `0x0133 connectDevice`(非 `0x09`):

```
token = AES-128-CBC(key=deviceSecret[:16] ascii, iv=key, pt=random ascii).hex()
```

- deviceSecret 从 root 手机 `PreferenceUtils.xml` 的 `device_list_id` 提取
  (完整凭据见 `extract/CREDENTIALS.md`,该文件已被 .gitignore 排除)
- 用两组真实抓包的 (random, token) 交叉验证,`tools/verify_auth.py` 全部匹配
- 关键细节:key/iv 取 deviceSecret **hex 字符串的前 16 个 ASCII 字符**
  (不做 hex 解码),random 也是当 ASCII 明文,正好 32 字节 2 块无 padding

**离线第三方客户端的鉴权障碍已完全清除。** deviceSecret 一次性绑定时由云端下发、
之后本地缓存;导出后即可离线复现 token。

## 10. SDK 架构(反编译确认)

内部代号 **"Dinger"**。Java 为薄壳,协议栈/加密/Opus 编解码全在 native
`libDtSync.so`,经 `DingerAudioTools`(JNI)桥接。关键 native 方法:

| 方法 | 作用 |
|---|---|
| `SendCmdToDevice(int cmd, String json)` | 发命令(收明文 JSON,native 负责封包) |
| `PushBleRecvData(byte[], int)` | BLE 收到的数据喂给 native |
| `OnSendData(int, byte[], int)` | 回调:native 算好的待发字节(Java 实际写 BLE) |
| `AESEncrypt/AESDecrypt(String, String)` | 鉴权与文件加解密 |
| `OpusConvertToOgg(String)` | Opus 转 Ogg(自带) |
| `ExportAudioWithProgress(...)` | 导出音频 |
| `StartOta/StopOta` | 固件升级 |

**关键**:`SendCmdToDevice` 接收的是**明文 JSON**,说明业务语义在 Java 侧构造,
native 只做封包/加密/传输 —— 对复刻客户端非常有利。

---

## 工具

`tools/HidProbe.cs` — 枚举 HID 设备,读取 VID/PID/厂商/产品/序列号/report 能力
`tools/HidListen.cs` — 被动监听 HID Input 报告(只读,不向设备写入)

编译:
```
%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe /out:tools\HidProbe.exe tools\HidProbe.cs
```
