# A1 官方客户端原生控制流程复核

日期：2026-09-24。目标是还原官方客户端对本机 A1 的控制契约，不以获得固件源码为前提。本轮仅分析本地 APK、原生库及已有抓包，没有改动独立客户端、下发未知指令或刷写设备。

## 结论

按照官方客户端的完整流程，可以实现其对设备的已有控制功能，无需先理解卡片内部的硬件驱动。但“命令格式已知”只覆盖其中一部分：官方还处理双向请求、录音事件、同步抢占、音频缺包及停止后的收尾。这些代码确实在本地原包中，本轮已进一步定位和解析。

当前不宜宣称全部掌握。剩余重点应是补齐客户端状态转换和恢复流程，再对本机验证；固件逆向主要用于客户端没有展示的能力、离线行为及可修改范围。

## 证据与复现

- 官方 App：8.5.8.3，原包 `apks/8.5.8.3/split_demand1.apk`。
- 原生库：`apks/8.5.8.3/work/libDingerSdk.so`，ARM64。
- SHA-256：`61572524ea708221e99fe8d1c7ab977b84c20050103b97a0fceb01db69fc2c41`。
- 下文地址均是该 ELF 的虚拟地址，不能直接当文件偏移或运行时绝对地址。
- 静态证据：ELF 导出符号、ARM64 反汇编和调用分支；并未得到原始 C++ 源码。
- 动态证据：本地已有 HCI 抓包。不同文件有重叠时间段，不能相加当独立实验次数。
- 离线仿真：仅执行该库两个纯事件名称查询函数，无 JNI 初始化、网络或设备操作。

```powershell
python tools/native_event_names.py apks/8.5.8.3/work/libDingerSdk.so native_event_names_8.5.8.3.json --runtime apks/8.5.8.3/work/python
python tools/ut_report.py capture/official_mode1001_stop.log
python -m unittest discover -s tools -p test_ut_report.py -v
```

名称提取需 pyelftools、capstone 分析环境中的 Unicorn；脚本实际依赖见脚本 import。原包、反编译材料、反汇编和原始抓包均保留在忽略目录，不作为公开研究代码提交。

## 1. 客户端从界面到设备的调用链

```text
界面 recordOperation(operationName)
  → DingerInterfaceImpl.c0：检查条件、读取参数和扩展信息
  → pt8.q3：检查 BLE 已连接、当前没有 OTA
  → lj2.P：action 原样写入 JSON，命令号 0x0100
  → 原生 SendCmdToDevice：分配序号、封包、发送
  → 蓝牙
  ← 应答或设备主动请求
  → 原生分别分派，更新录音/同步处理对象
  → Java 回调、界面及云端后续处理
```

8.5.8.3 Java 证据位于 `apks/8.5.8.3/work/src/sources/`：

- `com/alibaba/dingtalk/dingerimpl/DingerInterfaceImpl.java:4577` 起，`c0`。
- `defpackage/pt8.java:5104`，`q3`。
- `defpackage/lj2.java:1759`，`P`。直接 `map.put("action", str)`，然后 `R(256, k(map))`，按返回消息 ID 注册回调。
- `defpackage/pt8.java:1533` 附近分别处理 `pause/resume` 和 `hold/unhold`；`unhold` 的条件分支还恢复文件同步触发。

因此不能未经验证把 `hold/unhold` 当作 `pause/resume` 的同义词。所查 BLE 发送链没有这种自动转换。另有 4G 设备 RPC 分支，但其代码存在不代表本机 A1 具备 4G 能力。

## 2. 消息序号与双向请求

`DingerProtocolAna::SendCmdToDevice`（`0x231ac8`）：

- 发送类型为 `0x13`。
- 序号以单字节保存并递增，回绕包含 0；没有通用的“0 专用于主动事件”规则。
- 发送 `0x0112` 或 `0x014C` 前，调用 `AbortFileTransfer`。

`ParseRequest`（`0x22c0a8`）和 `ParseResponse`（`0x22a910`）有独立分派路径；两者都有 `0x0100` 录音处理函数：

| 原生入口 | ELF 地址 | 已复核行为 |
| --- | --- | --- |
| `ParseRequestAudioOpt` | `0x230780` | 解析录音动作，停止分支处理录音对象与缺包状态 |
| `ParseResponseAudioOpt` | `0x22ab6c` | 另一条录音动作处理路径，也包含开始、停止和 hold/unhold 分支 |
| `ResponseDevice` | `0x233a28` | 设备请求应答入口；各命令的完整应答策略仍需逐项整理 |

实机对应：1001 模式的开始/停止是设备发送 `type=0x13, cmd=0x0100`，官方用 `type=0x31`、相同命令和序号应答。较早抓包还出现设备发来的 `type=0x31, seq=0` 录音事件。因此请求匹配需要类型、命令、序号和业务内容一起判断。

不能对每个音频包机械套用相同 ACK：`ParseRequest` 的 `0x0117` 路径存在特殊分支，普通路径不走通用逐包应答。该分支条件尚未完整恢复。

## 3. 开始录音会影响文件同步

`ParseRequestStreamHeader`（`0x22e340`）读取 `attrs`、`fid`、`fsync`、`stream_type`、`file_ver`、`aes`、`alg_mode`、`incognitomode`、`sid` 等字段。

- `stream_type == 2` 的分支记录 `voice memo stream started` 并调用 `AbortFileTransfer`。
- 通过功能开关及状态选择 `DingerStreamRecord` 或 `DingerStreamRecordV2`，不能只按命令号决定如何接收音频。
- V2 已打开同一 fid 时存在更新音频参数的路径，不能把每个流头都当作全新录音。
- 停止路径检查 `IsFsync` / `HasPendingGaps`，调用 `StopAndNotify`、统计等处理。

含义：收到“停止录音”不等于所有音频已收全、文件可交付。设备停止、接收完成、补传完成与文件生成是不同节点。

## 4. 丢包与补传是官方实现的重要部分

本库导出符号、字符串及相关调用显示 FsyncV2 存在以下机制：小序号缺口填静音、较大缺口登记后补传、持久化 `.gaps`、旧包丢弃、按区间补传以及在特定丢包条件下从偏移 0 重新传输，补齐后再转码。

定位入口：

| 函数 | ELF 地址 |
| --- | --- |
| `ParseRequestStreamPacket` | `0x22edc0` |
| `SendFileSyncCmd` | `0x232360` |
| `SendRawFileSyncCmd` | `0x233350` |
| `CheckFileSyncTimeout` | `0x232fa8` |
| `RequestGapFill` | `0x239758` |

这里是静态机制证据，尚未逐项恢复阈值、所有参数取值及重试条件，也没有本轮人为制造断连/丢包进行实测。不能把机制的存在写成补传已验证成功。

## 5. 0x000C 已确认是结构化诊断日志

原生入口 `ParseNotifyUtReport`（`0x231408`），不再仅凭时间相关性猜测二进制内容。

### 外层格式

| 字节偏移 | 含义 |
| --- | --- |
| 0..1 | `5A 5A` |
| 2..3 | 大端 uint16，记录区域字节数 N |
| 4..4+N-1 | 记录区域 |
| 4+N..7+N | 4 字节元数据，最低字节为记录数 |
| 8+N..9+N | `5A 5A` |

步长为 N / 记录数；当前解析器要求整除且步长至少 20。每条记录前 20 字节：

| 记录内偏移 | 含义 |
| --- | --- |
| 0..1 | 序号，大端 uint16 |
| 2..7 | 设备时间，大端 uint48；已见样本符合 Unix 秒 |
| 8..11 | 完整事件编号，大端 uint32 |
| 12..19 | 大端 uint64 事件值；语义因事件而异 |

事件最高字节是模块类别，不能单独当成按键码。`DingerUtReport::Parse`（`0x247cb8`）按该模块值分派。

`dt_ut_module_to_string`（`0x24095c`）和 `dt_ut_event_to_string`（`0x240170`）离线提取出 14 个模块、108 个有名称的值，包含 MIN/MAX 边界值。扫描仅覆盖模块 0..13、低位 0..255 与 65535，**不是穷尽枚举，也不是 108 个已验证功能**。完整表见 `native_event_names_8.5.8.3.json`。

### 用官方名称重新解释已有实验

1000 相关旧抓包 `btsnoop_2026-09-24_right_long.log` 的单次长按段，UTC：

| 时间 | 事件 |
| --- | --- |
| 09:30:25.690 | `AUDIO_INSTANCE_START` |
| 09:30:25.933 | `AUDIO_RECORD_START` |
| 09:30:26.189 | `AUDIO_CONTROL_CHAT_STREAM_START` |
| 09:30:27.227 | `AUDIO_CONTROL_CHAT_STREAM_STOP` |
| 09:30:27.228 | `AUDIO_INSTANCE_STOP`、`AUDIO_RECORD_STOP` |

官方 1001 抓包 `official_mode1001_stop.log`，UTC：

| 时间 | 事件 |
| --- | --- |
| 12:02:23.075 | `AUDIO_INSTANCE_START` |
| 12:02:23.581 | `AUDIO_RECORD_START` |
| 12:02:23.583 | `AUDIO_CONTROL_START_TRANSLATE_STREAM` |
| 12:03:49.002 | `AUDIO_INSTANCE_STOP` |
| 12:03:49.238 | `AUDIO_RECORD_STOP` |

这些是 SDK 内部名称，不能据 `CHAT/TRANSLATE` 推断实际调用了聊天/翻译云服务。两组实验使用过不同客户端，也不能把全部差异都归因于 1000/1001。

**更正旧推测：** 09:14:25、09:24:25 等周期性事件的完整 ID 是 `0x01000003`，官方名称为 `SYSTEM_UPTIME`。它们不是按键事件。此前把其中某个字节单独当作事件码或采用较短时间字段的解释应废弃。

## 6. 本轮验证与下一步缺口

- 解析器 3 个测试通过：字段边界、多记录和非法报文拒绝。
- 对本地文件名包含 `2026-09-24` 或 `mode1001` 的 22 份 `.log` 复核：遇到的 `0x000C` 均可解析，事件名均能匹配；部分文件无该命令，部分为累计快照，不能当作 22 次独立实验。
- 未修改独立 App；这些测试只证明诊断解析工具，不证明独立客户端功能已通过实机验收。

按对复现官方行为的重要性，接下来仍需：

1. **补传闭环：**完整恢复缺包判定阈值、补传参数、重试/超时和落盘结束条件，再验证下载文件可播放、时长正确。
2. **事件与应答表：**逐命令整理请求方向、响应条件、状态转换；厘清 hold/unhold 与 pause/resume 的实际差别。
3. **同版本同客户端对照：**1000/1001 的开始、松手、再次长按、断连重连行为，避免混用不同客户端抓包得结论。
4. **定时：**客户端 `0x011A` 格式已知，但本机 `cap_schedule=1`，官方门槛为 >=2；接受、持久化、覆盖和离线执行仍未验证。
5. **日版与云端：**具体服务、功能开关、账户和版本分支需要分别核对；能拿到音频后，自有转写/存储/自动化可以自行实现。

固件提取不是以上工作的前置条件。官方原包足以继续挖掘客户端侧行为；要回答设备未公开命令、内部按键阈值或修改固件能力，才需要进一步取得适配固件或其他设备侧证据。
