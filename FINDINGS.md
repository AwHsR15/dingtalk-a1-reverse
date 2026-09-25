# DingTalk A1 / TALIX A1 逆向笔记

> 历史研究记录：当前结论和修订以 [2026-09-25研究总览](docs/RESEARCH_SUMMARY.md) 为准。旧条目中的“完全/全部解出”、密钥来源时机、跨设备、Wi-Fi或固件能力等措辞不代表当前全功能验收。

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

## 5. 连接方式(已验证，修正早期误判)

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
[0]     类型      0x13 = 请求 / 0x31 = 响应(见下方修正)
[1:3]   命令 ID   16 位大端
[3]     序列号    逐包递增
[4:8]   长度      payload 字节数(32 位大端)
[8:]    payload   明文 JSON,或二进制数据
```

> **修正(2026-08-11,第三方客户端实测)**:`[0]` **不是方向标记,是请求/响应标记**。
> 对 bugreport3_enc 全量统计:
>
> | 谁写的 | type | 命令 |
> |---|---|---|
> | App | 0x13 | 0x0008/0x0100/0x0110/0x0111/0x0132/0x0133/0x0137/0x013F(自己发起) |
> | App | **0x31** | 0x0114/0x0115/0x0116/0x0100(**对设备推送的 ACK**) |
> | 设备 | 0x13 | 0x0114/0x0115/0x0116/0x0117(**设备自己发起的推送**) |
> | 设备 | 0x31 | 对 App 命令的应答 |
>
> 即"谁发起谁写 0x13,谁应答谁写 0x31",与传输方向无关。
> **ACK 用 0x13 会被设备当成新命令,直接回 `{"code":405}` 并中断文件传输。**
> 这个坑卡了很久:文件属性能收到、数据永远不来,而且我方无条件 ACK 还会和
> 设备的 405 形成每秒数十次的死循环。ACK 还必须**沿用推送帧的 seq**。

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

**工具状态(2026-08-11 解析器修订)**:`tools/protocol_analyze.py` 已按
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

内部代号 **"Dinger"**。Java 为薄壳,协议栈/加密/Opus 编解码全在 native 库里,
经 `DingerAudioTools`(JNI)桥接。关键 native 方法:

> **更正(2026-08-11)**:原生库是 **`libDingerSdk.so`**(7.3 MB),不是 `libDtSync.so`。
> `DingerAudioTools` 的静态块写得很清楚:`System.loadLibrary("DingerSdk")`。
> `libDtSync.so`(1.1 MB)是另一个子系统,依赖 `libdatabase_sqlcrypto` /
> `libdmojo_support` 等钉钉内部库,与 A1 协议无关。
>
> `libDingerSdk.so` 的依赖非常干净:只有 `libc++_shared.so` + 系统库,
> 因此**可以整个搬进第三方 App 直接用**。
>
> 另外 `DingerAudioTools` 里有两个常量:
> ```java
> public static int MAGIC_SEND = 19;   // 0x13
> public static int MAGIC_RESP = 49;   // 0x31
> ```
> 官方源码独立印证了第 7.2 节靠抓包统计得出的"请求/响应标记"结论 ——
> 命名是 SEND/RESP 而不是 TO_DEVICE/FROM_DEVICE,语义确凿。

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

## 11. 第三方客户端实测(2026-08-11,已全程跑通)

客户端实现在独立客户端安卓端:`<workspace>/example-client\android\app\src\main\java\com\example-client\recorder\a1\`
(`A1Protocol` 纯协议 / `A1Auth` 鉴权 / `A1Client` BLE 传输 / `A1Session` 业务
/ `A1Store` 落盘 / `OggOpusWriter` 容器)。协议层 17 个 JVM 单测,向量取自真实抓包。

**PC 不能当宿主**:本机所有蓝牙适配器状态均为 `Unknown`(不在线),
BLE 客户端只能跑在安卓上。实测机 Android 16测试终端。

### 11.1 已在真机验证通过

| 环节 | 结果 |
|---|---|
| BLE 扫描 / 连接 | ✅ MTU 协商到 **512** |
| 离线鉴权 | ✅ `0x0008`→AES token→`0x0133` 返回 `code:200` + 全部 cap 位 |
| 设备状态 `0x0132` | ✅ 电量 100%、存储 58GB/59630MB、固件 `V1.6.88-202601291628` |
| 灰度开关 `0x0137` | ✅ `code:200` |
| 参数设置 `0x0100` | ✅ `code:200` |
| 文件列表 `0x0110` | ✅ 返回 9 条真实录音 |
| 文件下载 `0x0111`→`0x0114`→`0x0115` | ✅ **53252 字节,与属性里的 size 分毫不差** |

**离线第三方客户端已完全成立** —— 不装官方 App、不联网、不改固件。

### 11.2 命令表补充与更正

| cmd | 说明 |
|---|---|
| `0x0111` | **文件下载请求**(原命令表遗漏)`{did, fid, offset, progress:65537}` → `{code, fid}` |
| `0x0101` | 声纹 `{action:start/stop, did, type:"voice_print"}` |
| `0x013F` | 系统控制/电量 `{did, key:"battery_key"}` ——**不是** `0x0136` |

下载时序:`0x0111` → 设备推 `0x0114`(属性) → **ACK** → 设备推 `0x0115`(数据,可多块)
→ **每块都要 ACK**。ACK = `{"code":200}`,type **0x31**,seq 沿用推送帧。

### 11.3 二进制布局(真机解出)

**`0x0110` 文件列表**:`[0:2]code [2:4]条数`,之后每条 **8 字节**:
`[0:2]标志 [2:6]fid(大端) [6:8]状态`,尾部 0x5A 填充。

> 早先按 12 字节步长解会**每隔一条错一次**,读出 786432 / 196608 这类假 fid。
> 加一道"fid 必须像 Unix 时间戳"的校验能兜住布局变化。

**`0x0115` 文件数据块**:`[2:6]fid [8:12]块序号(从1起) [12:16]**本块**长度 [16:]数据`。

> `[12:16]` 是**本块**长度不是文件总长:53252 字节的文件分两块,
> 该字段分别为 48000 和 5252,相加才等于总长。按总长截会丢掉第二块。

**下载下来的文件是钉钉私有容器 `BABA/DTYJ`**,不是裸 Opus。

> 本节 2026-09-16 用一台测试机上的 **33 个真机容器**逐一验证后重写
> (工具:`tools/dtyj_parse.py`,回归测试:`tools/test_dtyj_parse.py`)。
> 此前版本里"记录长固定 84""@56 是 extr 块长"两处说法是错的,已更正。

#### 头部:固定 80 字节,长得像 RIFF 但不能按 RIFF 读

```
偏移  类型  内容
  0         "BABA"
  4   u32   从偏移 8 到文件末尾的字节数
  8         "DTYJ"
 12         "ver "          ← 不标准①:没有长度字段
 16         "v1.7" / "v1.6"
 20         "fmt "
 24   u32   写的是 0         ← 不标准②:实际块体固定 24 字节
 32   u32   码率(bps)
 36   u32   采样率(Hz)
 41   u8    帧长(ms)
 42   u8    声道数
 43   u8    位深
 44   u16   记录长(每条记录的字节数)
 46   u8    每条记录的前缀长度
 48   u32   时长(ms)
 52         "extr"
 56   u8    含义未知(实测 0 / 1 / 2)
 58   u8    加密标志(1 = 包体是 AES 密文,见下)
 60         8 字节,实测全 0
 68         "data"
 72   u32   载荷字节数
 76   u32   CRC32           ← 不标准③:长度之后多插了一个 CRC
 80         载荷
```

三处不标准各有各的坑:

- **① `ver ` 没有长度字段**:按"tag + size + body"走,后面每块都会被推后 4 字节。
- **② `fmt ` 的长度写 0**:通用 RIFF 遍历会在这里读到 size=0,再把紧随其后的
  码率字节(`00 7d 00 00`)当成下一个 tag,解析当场跑飞。
- **③ `data` 长度后面还有 CRC32**:把 CRC 当成载荷,之后**每条记录都错位 4 字节**,
  切出来的 TOC 全乱 —— 看起来会非常像"包体被加密了"。

所以必须认死偏移,再用四个 tag 的位置自检:`ver `@12、`fmt `@20、`extr`@52、`data`@68。

#### 三种真机变体:记录长不是常数

| 版本 | 码率 / 采样率 | @46 前缀 | Opus 包 | @44 记录长 | 样本数 |
|---|---|---|---|---|---|
| v1.7 | 32 kbps / 16 kHz | 4 | 80 | **84** | 28 |
| v1.7 | 64 kbps / **48 kHz** | 4 | 160 | **164** | 1 |
| v1.6 | 32 kbps / 16 kHz | **0** | 80 | **80** | 4 |

33 个样本全部满足:**`记录长 = 码率 × 帧长 / 8000 + 前缀长`**。
官方 native SDK 打印的 `Frame size: 80` 指的是 **Opus 包**,不是记录;
`FRAME_HEADER_SIZE` 就是 @46 的前缀长(v1.6 为 0)。

48 kHz / 64 kbps 那一份应是设备的高音质录音模式。v1.6 的样本反而出现在较新的录音上,
版本号由什么决定目前不清楚。

#### 载荷的两种形态

1. **原始记录**:设备写出的原件,定长记录数组。每条记录 `[0:前缀长]` 是前缀
   (v1.7 实测全为 0),其后是一个 Opus 包。
2. **官方已转换**:`OpusConvertToOgg` 保留 80 字节头,把载荷换成标准 Ogg 流
   (`OpusHead` / `OpusTags` / 音频页)。这一步**只重新封装、不解密**。
   转换后头里的载荷长仍是原件的,所以磁盘上的文件会比头里声明的大。

测试机上 33 个容器:31 个是已转换形态,2 个是原始记录。

#### 加密:按文件而定,头里有标志位

判据是 Opus 包首字节(TOC)的**高 5 位 config**:同一路录音 config 恒定,
明文时集中度接近 100%;密文首字节均匀分布,集中度约 1/32 ≈ 3%(小样本下 4~7%)。
不能按整字节比,因为真实 Opus 的低 2 位帧数码会合法地变化(实测 `0x4B` 与 `0x48` 交替)。

33 个样本的实测结果:

| @58 | 判定 | 数量 | 版本 |
|---|---|---|---|
| 1 | 密文(config 集中度 4~7%) | 32 | v1.7 ×28、v1.6 ×4 |
| 0 | **明文**(config 9 = SILK-WB 20ms,100%) | 1 | v1.7 |

- **@58 与实测判定 33/33 一致**,几乎可以确定就是 SDK 打印里的 `AES flag`。
  但明文样本只有 1 个,这个结论仍需要更多明文样本确认。
- **加密与版本号无关**(v1.7 两种都有)。
- 唯一的明文样本是一条 1 小时 26 分的长录音,按客户端代码,它是走 **WiFi 快传**
  拉下来的设备原件,其余 32 个走的是 BLE 同步。
  "WiFi 快传拿到的是明文"目前只是**假设**(n=1),尚未证实。

#### 与 Shawn-TKD/dingtalk-a1-pc-tools 的分歧,结论:两边都对

公开项目 [Shawn-TKD/dingtalk-a1-pc-tools](https://github.com/Shawn-TKD/dingtalk-a1-pc-tools)
的 `dtyj_to_ogg.py` 给出了"定长记录 = 4 字节前缀 + Opus 包"的思路,这正是本节解开 data 块的起点。
但它不做解密,而本项目早先实测包体是密文 —— 两边看起来互相矛盾。

真机数据的回答是:**取决于文件**。
他们的转换器对 `@58 = 0` 的 v1.7 原件完全正确;对 `@58 = 1` 的文件
(测试机上占绝大多数)转出来的 Ogg 框架合规,但只能解出噪声。
另外它按固定 4 字节前缀切,遇到 v1.6(前缀 0)会整体错位。

`dtyj_parse.py` 会同时给出**加密标志**和**按 TOC 实测的判定**,两者矛盾时会提示,
遇到这种样本请记下来。

#### 截断文件

头里的长度能直接用来发现半截文件:`80 + 载荷长` 大于磁盘大小即为截断。
客户端正是靠这一点发现了一批"永远解不开"的录音 —— BLE 同步中途断开,
半截文件被当成完整文件落了盘。测试机上的 v1.6 原件 `…090232` 就只传下来 58%。

客户端因此把设备文件原样存为私有容器,不改后缀成 `.opus`(会让人以为能直接播)。

### 11.4 连接行为(踩坑记录)

- **A1 在连接态下不广播**。被官方 App(或另一台设备)占着时扫不到,
  `dumpsys bluetooth_manager` 里能看到 `[Packages]: [com.alibaba.dingtalk.global]`。
  设备同一时刻只接受一个连接。
- `connectGatt(autoConnect=false)` 只在设备**当下正在广播**时成功,否则约 30 秒后
  `status=147`。客户端的做法是:先直连快速试一次,失败转 `autoConnect=true` 挂后台等。
- **`extract/CREDENTIALS.md` 里记的 MAC 是错的 —— 字节序被整个颠倒了**。
  形如 `D4:3A:65:…:…:…` 的那个读出来是反的,真实地址是把它**逐字节倒过来**
  的 `0B:3B:25:…:…:…`(实测扫描 + `dumpsys` 里的 `RE_OUI` 字段双重印证)。

  > 这里只保留 OUI 前缀 —— 后三段是本机的唯一标识,对复现毫无用处,
  > 就不往公开仓库里放了。自己排查时对着 `dumpsys` 的 `RE_OUI` 比一下即可。
  >
  > 教训本身才是重点:**别直接信 App 缓存里那个 MAC 字段**,先确认字节序。
  错的那个看形态是字节序读反了的产物,前四字节正好是真实值的倒序。
- 每次连接必须 `gatt.close()` 释放:安卓每进程只有 32 个 GATT 客户端槽位,漏一次少一个。

## 11.5 官方 SDK 已内嵌进独立客户端(2026-08-11)

把官方件原样搬进 `<workspace>/example-client\android`:

| 内容 | 去处 |
|---|---|
| `libDingerSdk.so` + `libc++_shared.so`(自设备 `/data/app/.../lib/arm64/`) | `app/src/main/jniLibs/arm64-v8a/` |
| `com.android.dingersdk.nativeInterface` 全部 15 个类 | `app/src/main/java/com/android/dingersdk/` |

**包名必须保持 `com.android.dingersdk.nativeInterface`** —— JNI 按全限定类名
解析 native 方法,改包名会直接 `UnsatisfiedLinkError`。

反编译产物只依赖两个钉钉内部类,且都只用到一个常量。做法是**在外面补桩类**
而不是改官方源码,这样以后从新版 APK 重新拉一份可以直接覆盖:

- `com.taobao.weex.el.parse.Operators` — 只用了 `BLOCK_END` / `SINGLE_QUOTE`
- `com.alibaba.wukong.im.message.MessageContentImpl` — 只用了 `KEY_RICH_TEXT_PAYLOAD`(= `"payload"`)

桥接方式(`A1Native.kt`):原生 SDK 不碰蓝牙,要发的字节从 `OnSendData` 回调吐出来,
收到的字节由宿主调 `PushBleRecvData` 喂回去 —— 正好接到独立客户端已有的 BLE 传输上。

内嵌后拿到的、自己实现不了的能力:

- `OpusConvertToOgg` —— **`.dtyj` 容器里 data 块的结构我们没解出来,这是官方正解**
- `ExportAudioWithProgress` / `MergeFilesWithProgress` / `AudioClipWithProgress` / `SmartClipWithProgress`
- `AESDecrypt` —— 解密加密录音
- `openAudioFile` / `readAudioFrames` / `seekToSecond` —— 音频解码与定位
- `StartAsr` / `StopAsr` / `PauseAsr` —— SDK 自带 ASR
- `StartOta` / `StopOta`

> **闭源库,来自用户自己设备,仅供本机互操作,不可再分发。**
> 独立客户端的纯 Kotlin 实现保留着并且能独立工作(鉴权/列表/下载都已验证),
> 原生 SDK 加载不上时自动回落,不是硬依赖。

服务提供商相关的东西(corpId、自报 SDK 版本/机型、`InitConfig`)抽到了
`A1Provider`,可在界面里改或整份替换,协议层不用动。

## 11.5 官方 H5 前端源码(已获取)

官方录音卡界面是**在线加载的钉钉小程序**,但**离线包在设备上有完整前端源码**:

```
/data/data/com.alibaba.dingtalk.global/files/dingTalkTheOne/ariverPackages/
    installed/992025081915501485/<hash>/992025081915501485.tar
```

解包后是 `smart-hardware-ai-assistant/0.181.1/` 完整应用(mobile-recording 主 bundle
1.1MB + vendor chunk 3.2MB + 21 种语言 i18n)。webpack 压缩但可提取行为契约。
解析工具:`tools/h5_extract.py`(按类别抽取)、`tools/h5_context.py`(看调用上下文)。

### 官方 H5 调用的设备能力 JSAPI(完整清单)

| JSAPI | 用途 |
|---|---|
| `internal.dinger.recordOperation` | 录音 start/stop |
| `internal.dinger.realStreamOperation` | **实时流 + ASR 开关** |
| `internal.dinger.getDeviceStatus` | 设备状态 |
| `internal.dinger.getFileList` / `fileOperation` / `dingerFileOperation` | 文件 |
| `internal.dinger.sendBleCommand` | 直接下发 BLE 命令 |
| `internal.dinger.audio` / `otaOperation` | 音频 / OTA |
| `internal.channel.subscribe/publish` | 事件通道 |
| `internal.request.lwp` | 钉钉云长连接(外部服务走这里) |

### 外部 ASR/翻译的参数契约

```js
realStreamOperation { deviceId, operationName:"set", operationParam:{
    needAsr: "start"|"stop",
    sourceLanguage: "multilingual" | <语言码>,
    targetLanguages: [...], languageHints: [...],
    attributes: { scene: "transcription"                 // 纯转写
                       | "simultaneous_interpretation"   // 同传(单向)
                       | "real_time_translation" }       // 实时翻译(双向)
}}
```

## 11.6 实时流的真正开关(踩坑记录,已实测修正)

**`0x0137` 灰度开关里的 `stream_record` 不是实时流开关。**发它设备会回 `code:200`,
但根本不推流,极具误导性。

真正的开关来自反编译 `m62.Y(boolean)`:

```
0x0100  {"action":"set","params":[{"key":"upload_stream","val":1}]}
```

实测:发 `upload_stream=1` 后设备立刻开始推 `0x0117`(15 秒收到 760 帧)。
`stream_record` 只是「允许边录边传」的配置位,两码事。

## 11.7 第三方客户端 + 自定义转写服务商(已端到端验证)

2026-08-12 在 Android测试终端上全链路跑通,**完全不经阿里云**:

```
A1 硬件 --BLE--> 独立客户端(离线鉴权) --流式 Ogg 封装--> Soniox --> 实时字幕
```

- 离线鉴权在**一台全新设备**上验证成功(用提取的 deviceSecret 现场算 token,
  设备回 `code:200` + 全部 cap 位)
- 实时流 760+ 帧稳定推送
- Soniox 输出中文转写 + **说话人分离**生效

**音频格式的关键处理**:Soniox 的 raw 格式只收 PCM 不收裸 Opus,而 A1 吐的是裸 Opus。
解法是复用 `OggOpusWriter` 做**流式 Ogg 封装**(把输出接到 WebSocket),再用
`audio_format:"auto"` 让服务端识别 ogg —— 手机端全程不碰编解码。
实时场景要把每页包数从 50 调到 10(50 包≈1 秒,会原样变成字幕延迟)。

客户端实现见 `<workspace>/example-client\android\app\src\main\java\com\example-client\recorder\a1\transcribe\`
(`Transcription.kt` 服务商抽象 / `SonioxProvider.kt` / `A1LiveTranscriber.kt`)。

## 12. 仍未掌握

- [ ] `0x0115` 容器内 data 块的结构(Opus 帧如何排布 / 是否加密)
- [ ] 加密开启后新录音的 `0x0115` 是否变密文(仍是原第 7.5 节留的问题)
- [ ] WiFi 热点通道 `0x0120`/`0x0121` 的实际传输协议
- [ ] `0x000C` 设备主动推的二进制(每次连接都有,内含 fid,疑似状态广播)
- [ ] OTA `0x0135` / 定时 `cap_schedule` / AI 按键 `cap_aikey_option`

## 13. 处理架构:转写/声纹在哪跑,以及完整运作模式清单

用户提问驱动的补充调查(2026-08-11),证据均来自反编译代码里**未混淆的类名/方法名
/日志字符串**(这些是最强的取证线索,因为混淆器不会替换字符串常量)。

### 13.1 转写(ASR)——完全不在设备上,是阿里云通义听悟

完整调用链(`iy7.java` = 内部类名 `DingerManger`,日志 tag 也是这个):

```
H5 页面(如 dinger.dingtalk.com 的会议页)
  → JS 桥接 realStreamOperation({operationName:"set", operationParam:{needAsr:"start", scene:...}})
  → DingerInterfaceImpl.V()
      m62.C().Y(true)              // 打开设备 BLE 实时流(即 cmd 0x0117 开始持续推送)
      iy7.C2() [内部日志名 "startAsr"]
        → k8r.b()  [日志 tag "TingwuGeneral"]
            → zg7.e(...)  网络请求,问阿里后端要一个 audioStreamWssUrl
        → 拿到 wss:// URL 后:
            DingerAudioTools.StartAsr(wssUrl)   // native(libDtSync.so)
```

`DingerAudioTools.StartAsr(String wssUrl)` 是 native 方法,传入的是一个
**WebSocket 地址**。也就是说:手机原生 SDK 把从设备 BLE 收到的实时 Opus 音频,
通过 WebSocket **转发给阿里云"通义听悟"(Tingwu)服务**做实时语音识别。

**结论:转写不在 BES2800 芯片上跑,也不在手机本地跑,是纯云端服务
(通义听悟),且依赖网络连接。** `libDtSync.so` 只是个转发管道,不含 ASR 模型。
`stopAsr`(`iy7.G2()`)同样调用 native `DingerAudioTools.StopAsr()` 来关闭这条转发。

### 13.2 声纹(voiceprint)——设备只负责"录",处理疑似云端/App侧

BLE 层声纹命令 `0x0101 {action:start/stop, type:"voice_print"}`(第 11.2 节)
只是让设备进入某种采集模式,不代表设备做了声纹比对。反编译中找到的唯一
处理逻辑在 `iy7.f2()`:

```java
if (TextUtils.equals(source, "device_voiceprint") || sg7.b()) {
    if (body.has("oggPath")) {
        j4t.e(body.optString("oggPath"), body.optLong("duration"), null);
    }
}
```

这是**手机 App 侧**对一条"设备来源标记为 device_voiceprint"的**本地事件**
(带 `oggPath`,即已经转码好的本地 ogg 文件路径)做后续处理,不是设备把声纹
特征值传回来。BES2800 是音频编解码/降噪芯片,没有迹象表明它跑声纹比对模型。
**声纹的实际匹配逻辑大概率在 App/云端,设备只负责按声纹触发的录音片段。**
(这条是合理推断,未追到 `j4t.e()` 内部实现,不算 100% 证实。)

### 13.3 长会议的实时协同:需要三条链路同时在线

实时转写+摘要要求同时满足:

```
设备 --BLE(0x0117 持续推流)--> 手机 --WebSocket(需联网)--> 通义听悟云端
```

- **BLE 连接必须全程保持**:设备同一时刻只接受一个连接(第 11.4 节已验证),
  断开或超出范围,实时流立即中断
- **手机必须联网**:WSS 连接走的是运营商/WiFi 网络,不是 BLE
- 转写结果回传后,摘要/可视化大概率也在 H5 页面里调云端 LLM 生成
  (未直接追证据,但架构上 H5+云 API 是唯一合理路径 —— App 原生代码里
  没有找到本地摘要生成逻辑)

**如果 BLE 断开或没网:实时功能全部不可用,但设备本身不受影响** ——
它按第 13.4 节的模式继续本地录音存文件(64GB 本地存储独立于连接状态),
之后重新连接时用 `0x0110`/`0x0111`/`0x0115` 把文件同步下来,再补跑一次
转写/摘要(这也是官方 App 里"离线转写/云端转写"两种模式并存的原因)。

**即:设备不是"一直在实时传输"** —— 实时流(0x0117)只在 App 明确发起
`realStreamOperation start` 时才打开(对应"正在看实时转写"这类场景);
平时录音是设备自己写本地文件,事后批量同步,不占用持续 BLE 带宽。

### 13.4 完整运作模式清单

**A. 录音场景模式**(`DtiotAudioMode`,决定 mic 阵列的拾音策略):

| 值 | 常量 | 含义 |
|---|---|---|
| 0 | AUDIO_MODE_STANDARD | 标准模式 |
| 1 | AUDIO_MODE_HIFI | 高保真 |
| 2 | AUDIO_MODE_VISUAL_REC | 可视化录制(声明存在,但未在反编译代码中找到实际调用点,未确认具体行为) |
| 3 | AUDIO_MODE_CONFERENCE | 会议模式 |
| 4 | AUDIO_MODE_FACE_TO_FACE | 面对面模式 |
| 5 | AUDIO_MODE_INTERVIEW | 采访模式 |

与实测协议**交叉验证**:抓包里 `0x0116`(流属性)的 `stream_type` 字段
出现过 `0`/`3`/`4`,与 STANDARD/CONFERENCE/FACE_TO_FACE 完全对应。

**B. 传输/连接事件**(`DtIotEvent`,双通道各自独立开关):

| 值 | 事件 |
|---|---|
| 1~4 | BleOpen / BleClose / BleConnect / BleDisconnect |
| 11~14 | WiFiOpen / WiFiClose / WiFiConnect / WiFiDisconnect |

印证第 7.3.1 节的"双通道"猜想:BLE 与 WiFi 是两条独立管理的传输链路。

**C. 能力开关**(连接时通过 `0x0132` 状态位协商,决定 App 展示哪些功能入口):

`cap_remark`(备注/场景标记 ≥2 解锁)、`cap_voiceprint`(声纹)、
`cap_incognitomode`(隐身/免打扰录音,不参与云同步,推断)、
`cap_schedule`(定时任务)、`cap_aikey_option`(AI 按键)。

**D. 独立的实时双向语音通道(`device_chat`)**:与 ASR 转写通道不同的另一条
路径 ——`source:"device_chat"` 事件带 `data`(字节数组)+`len`,疑似对应
`cap_aikey_option`(AI 按键):按一下设备物理键,触发设备到手机的实时语音
数据流,大概率用于唤醒式 AI 语音助手交互(如问答),而非会议转写。
未追到具体 BLE opcode 来源,推测是本文档第 12 节里仍未解出的 `0x000C`
主动推送。

---

# 14. 官方能力全量测绘（2026-08-27，基于 8.3.48.3）

来源：`apks/8.3.48.3/`（这台机器上实际在跑的 14 个 split，全量提取）、
既有 `decompiled/base/sources`、以及独立客户端已内嵌的
`app/src/main/java/com/android/dingersdk` + `libDingerSdk.so`。

本节把第 8 节和第 12 节里"尚未掌握"的条目**大部分结清**，并补齐了
WiFi 快传、文件加密、设备侧命令表三块。

## 14.1 完整命令表（`DingerCommandHelper`，未混淆）

方法名和 JSON 字段名逐字来自反编译，**字段名一个字母都不能改**。

| cmd | hex | 方法 | body 字段 |
|---|---|---|---|
| 4 | `0x0004` | `sendResetDevice` | `did` |
| 8 | `0x0008` | `sendGetRandom` | `corpId`, `did` |
| 9 | `0x0009` | `sendAuth` | `timestamp`, `payload`, `did` |
| 256 | `0x0100` | `sendAudioRecordOpt` | `did`, `action`, `params[]` |
| 257 | `0x0101` | 声纹（见 14.4） | `did`, `action`, `type="voice_print"` |
| 272 | `0x0110` | `sendGetFileList` | `did`, `s_fid`, `e_fid`, `recently` |
| 274 | `0x0112` | `sendFileSyncCancel` | `did` |
| 275 | `0x0113` | `sendFileDelete` | `did`, `fid` |
| 288 | `0x0120` | `sendOpenAp` | `did`, `type` |
| 289 | `0x0121` | `sendCloseAp` | `did` |
| 304 | `0x0130` | `sendGetTransInfo` | `corpId` |
| 306 | `0x0132` | `sendSyncDevStatus` | `did` |
| 307 | `0x0133` | `sendConnectDevice` | `corpId`, `did`, `token`, `model`, `timestamp`, `sdk_ver` |
| 308 | `0x0134` | `sendDisconnectDevice` | `corpId`, `did` |
| 309 | `0x0135` | `sendQueryFwVersion` | `did`, `new_ver` |
| 310 | `0x0136` | `sendSysControl` | `did`, `key`, `val` |
| 311 | `0x0137` | `sendGraySwitchGet/Set/Control` | `did`, `action`(`get`/`set`), `key`, `val`, `params` |

第 8 节的「删除文件」「OTA 固件升级」「电量查询」到此**全部解出**：
删除是 `0x0113`，OTA 版本查询是 `0x0135`，电量走 `0x0136 sysControl`
的 `battery_key`。

> 注意 `sendConnectDevice` 用的字段名是 **`corpId`**（驼峰），而
> `sendGetRandom` 也是 `corpId`。独立客户端里 `A1Session` 发的是 `corp_id`
> （下划线）且实测能通过鉴权 —— 说明固件对这个字段名是宽容的，
> 或者两种都认。**不要据此推断其它字段也宽容。**

## 14.2 WiFi 快传（第 12 节遗留项，已解出）

BLE 只有几十 KB/s（实测 4.8~37 KB/s），一条几小时的录音传不动。
官方的解法是**让设备开一个 WiFi 热点，手机连上去走 HTTP 下载**。

完整流程：

```
1. BLE 发 0x0120 openAp {did, type}
2. 设备回 body: {ssid, passwd, url, ip, port}
      ip/port 只在灰度开关 qx7.c2() 打开时才读
3. 手机连上这个热点（ssid + passwd）
4. 逐条 HTTP GET： <url>/<fid 按 %014d 左补零>
      例：fid=1787720326 -> GET <url>/00001787720326
      本地落盘文件名：00001787720326.opus
5. 传完 BLE 发 0x0121 closeAp {did}
```

证据：
- `dingerimpl/wifi/WifiLinkData.java` —— `(ssid, password, url, ip, port)`
- `defpackage/m62.java:1110-1124` —— openAp 响应解析，字段名是 `passwd` 不是 `password`
- `dingerimpl/wifi/WifiTransferDialog.java:492-506` —— URL 拼接与 `%014d` 格式化
- `libDingerSdk.so` 字符串：`WIFI create AP failed` / `WIFI TCP start error`
  / `WIFI webserver start error` / `WIFI_CREATE_AP` / `WIFI_DESTROY_AP`

**下载下来的仍然是 `.opus` 私有容器**（不是 Ogg）。WiFi 传完之后官方会把
BLE 同步留下的那份 `.opus` 删掉（`DingerDownloader` 的
`[insertOrUpdateToDB] delete ble file`）—— 两条通道落的是同一种文件，
只是快慢不同。

相关事件码（`DingerEvent`）：
`DINGER_EVENT_KEY_WIFI_OPEN=11` / `CLOSE=12` / `CONNECT=13` / `DISCONNECT=14`。

`0x0130 getTransInfo(corpId)` 的用途尚未追到调用点，名字看像是取传输配置。

## 14.3 文件加密（第 7.5 / 第 8 / 第 12 节遗留项，已解出）

**结论：加密用的密钥就是 `deviceSecret` —— 和 BLE 鉴权是同一个值。**

铁证在 `dingerimpl/clip/DingerAudioHandler.java:117`：

```java
DingerAudioTools.openAudioFile(
    path,
    if7.q().o(Long.parseLong(deviceId)),   // ← 与第 9 节鉴权取密钥的调用完全一致
    attr);
```

第 9 节记的鉴权取密钥是 `if7.q().o(deviceId)`，这里一字不差。所以：

- 一个 `deviceSecret` 同时负责**BLE 鉴权**和**录音文件解密**
- 解密不是单独一步，而是 `openAudioFile` 打开时透明完成
- `AudioFileAttr.isEncrypted` 由 `openAudioFile` 回填，调用方只读不写

容器头里确实带加密标志。真机 dump 的一条（fid=1787720310）：

```
RIFF ID: BABA   Wave ID: DTYJ   Version: v1.6
Bitrate: 32000  Sample rate: 16000  Channels: 1  Bits: 16
Frame duration: 20 ms   Frame size: 80 bytes   FRAME_HEADER_SIZE: 0
Algorithm mode: 0   Algorithm gain: 0   **AES flag: 1**
Data ID: data   Data size: 18640   CRC: 0x817a932e
```

`AES flag: 1` 是**默认开着**的（设备 `0x0100` 参数里也能看到
`{"key":"aes","val":1}`），所以第 7.5 节留的"加密开启后 0x0115 是否变密文"
这个问题其实问反了 —— 它一直就是开的。

> **更正（同日实测）**：一开始据"`OpusConvertToOgg` 能解出正确时长"推断
> 转换时就解密了，**这是错的**。转换只重新封装，不解密：
>
> - 转出来的 Ogg 框架完全合规 —— 358 页、零坏同步、首页 `OpusHead`
>   （1 声道 / 16 kHz）、次页 `OpusTags` 来自 libopus、末页 granulepos
>   正好 7.120 秒；
> - 但**包体仍是密文**。ffmpeg 这个参考实现直接报
>   `Error parsing the packet header`，7.12 秒只啃出 2.65 秒噪声；
>   Android 的 `MediaCodec` 表现完全一样。
> - 时长能对上，是因为它来自 Ogg 的 granulepos 和私有头，与包体解不解得开无关。
>
> **解密发生在 `openAudioFile`**，而且它判断"要不要解密"看的是那 80 字节
> 私有头里的 AES 标志。所以：
>
> | 喂给 `openAudioFile` 的文件 | `attr.isEncrypted` | 结果 |
> |---|---|---|
> | `[BABA 头][OggS 流]`（官方原样） | `true` | 正确解出**全长** PCM，RMS 0.01~0.05（正常人声） |
> | 裸 `OggS`（私有头被切掉） | `false` | 当成明文不解密，只解出 27~37% 的噪声，RMS 0.23~0.30 |
>
> 结论：**那 80 字节私有头绝对不能切**。切了之后标准解码器读不了
> （包体是密文），官方解码器也不肯解密（标志没了）—— 两条路一起堵死。

## 14.4 设备侧命令与能力

- **声纹**：`SendCmdToDevice(257, {did, action, type:"voice_print"})`
  （`m62.java:1842`）。`action` 取 `start`/`stop`。第 8 节的 `cap_voiceprint` 到此解出。
- **隐身模式 / AI 按键**：走 `0x0100 sendAudioRecordOpt` 的 params，
  `key` 分别是 `incognitomode`、`aikey_option`（`m62.java:1429/1520/1942/2065`）。
- **一次连接后设备回报的参数**（真机实测）：
  `mode=0`、`delete_after_upload=0`、`aes=1`、`incognitomode=0`、`aikey_option=1000`
- **能力位**（`0x0133` 响应）：
  `cap_remark=2`、`cap_voiceprint=1`、`cap_incognitomode=1`、
  `cap_aikey_option=1`、`cap_schedule=1`

## 14.5 native SDK 全量接口（`DingerAudioTools`）

`libDingerSdk.so`，V2.1.0。按用途分组：

**加解密**：`AESEncrypt(key, plain)` / `AESDecrypt(key, cipher)`

**设备通信**：`InitConfig(json)`、`SendCmdToDevice(cmd, json)`、
`PushBleRecvData(bytes, len)`、`SendFileSyncCmd(fid, offset, index, count)`、
`StartSendFile(path)`、`setGraySwitches(map)`、`notifyEvent(a, b)`

**文件读取（官方唯一的解码路径）**：
`openAudioFile(path, deviceSecret, attr)` → `readAudioFrames(AudioFrameBuffer)`
→ `seekToPosition(float)` / `seekToSecond(int)` / `getCurrentPosition()`
→ `AudioFileClose()`；辅助 `getAudioFileAttributes()`、`getAudioFileInfo()`、
`GetOpusFileSize(path)`

> **这套接口是进程内单实例**：打开/读帧/关闭操作的是同一份全局状态，
> 同一时刻只能有一个文件在读。独立客户端里播放器和转写如果都要用，
> **必须共用同一把锁**。

**格式转换与编辑**：`OpusConvertToOgg(fid)`、
`ExportAudioWithProgress(param, out, ..., cb)`、
`MergeFilesWithProgress(params[], out[], cb)`、
`AudioClipWithProgress(param, cb)`、`SmartClipWithProgress(param, cb)`
（对应取消：`CancelExportAudio` / `CancelMergeFiles` / `CancelSmartClip`）

**OTA**：`StartOta(json)` / `StopOta()` / `OtaSendDataNotify(bool)`

**设备侧 ASR**：`StartAsr(json)` / `StopAsr()` / `PauseAsr(bool)`
（事件 `DINGER_EVENT_ASR_RESULT=0`）

**事件码**（`DingerEvent`）：
`ASR_RESULT=0`、`OTA_RESULT=1`、`OPUS_CONVERT_RESULT=2`、`NAME_TRANSFER_RESULT=3`；
按键类 `BLE_OPEN=1`/`BLE_CLOSE=2`/`BLE_CONNECT=3`/`BLE_DISCONNECT=4`、
`WIFI_OPEN=11`/`WIFI_CLOSE=12`/`WIFI_CONNECT=13`/`WIFI_DISCONNECT=14`

## 14.6 `OpusConvertToOgg` 的输出：合规 Ogg 框架 + 密文包体

真机实测：SDK 转换输出的 `<fid>.ogg` 结构是

```
偏移 0    42 41 42 41  "BABA"   ← 80 字节私有头原样保留
偏移 80   4f 67 67 53  "OggS"   ← Ogg 流从这里才开始
```

SDK 日志自己也写了：`initCovertToOgg ... privateHeaderOffset: 80`。

独立客户端一度把前 80 字节切掉，得到一个"看起来标准"的 Ogg —— 同步、时长解析
都正常了，但 **`MediaExtractor` + `MediaCodec` 仍然打不开**
（configure/start 之后第一次 dequeue 就报
`Pending dequeue output buffer request cancelled` /
`Invalid to call at Released state`）。

结合 14.5 可以确定原因：**官方从来不用系统解码器读这些文件**。
整个官方 App 里读录音只有一条路径 ——
`openAudioFile(path, deviceSecret, attr)` + `readAudioFrames()`。
所以那个 Ogg 大概率缺 `OpusHead`/`OpusTags` 之类的必备头，
只有 SDK 自己认。

**实验结果（已做完）**：第 1 条就通了 —— 保留 SDK 原样输出直接喂
`openAudioFile(path, deviceSecret, attr)`，`attr.isEncrypted` 回填 `true`，
解出全长 PCM，能量正常，转写正常出段。详见上面 14.3 的更正表。

独立客户端的落地：`DingerAudio.decodeToPcm()` 走官方通道并优先于
`MediaExtractor`；`A1Store.isConverted()` 只认 `[BABA][OggS]`，
裸 Ogg 判成未转换以便自动重新同步；播放器与转写共用
`DingerAudio.lock`，并在播放时暂停转写队列（官方这套文件接口是
**进程内单实例**，同时开两个文件必然互相踩）。

独立客户端侧对应代码：`A1Store.normalizeConverted` / `PcmDecode.decodeWithCodec` /
`Player.openDinger`（后者已经在用官方路径，且是能正常播放的）。

## 14.7 仍未解出

- [ ] `0x0130 getTransInfo` 的调用点与用途
- [ ] `0x000C` 设备主动推的二进制（第 12 节遗留）
- [x] `cap_schedule` 定时任务的静态下发命令：官方 APK 的 `m62.a0` 用 `0x011A` 发送 `{did,action:"set",current,params:[{sid,start,end}]}`；但 2026-09-24 真机实报 `cap_schedule=1`，官方代码要求至少 2，尚无 `0x011A` 真机应答或执行验证。详见 `RESEARCH_AUDIT_2026-09-24.md`。
- [ ] `0x013F`（第 7.6 节遗留）
- [ ] WiFi 热点那个 webserver 的完整路由（目前只确认了
      `GET <url>/<%014d fid>` 这一条）


## 工具

`tools/HidProbe.cs` — 枚举 HID 设备,读取 VID/PID/厂商/产品/序列号/report 能力
`tools/HidListen.cs` — 被动监听 HID Input 报告(只读,不向设备写入)

编译:
```
%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe /out:tools\HidProbe.exe tools\HidProbe.cs
```
