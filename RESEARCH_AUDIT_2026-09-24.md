# A1 协议复核：ADB 现场与仍缺的实验（2026-09-24）

> 最新原生层复核见 [官方客户端原生控制流程](NATIVE_CLIENT_FLOW_2026-09-24.md)：已解出 `0x000C` 结构化诊断日志与事件名称。下文历史记录中的未知周期事件现已确认包含 `SYSTEM_UPTIME`，不能作为按键证据；旧字段猜测以新报告为准。原生发送序号会回绕到 0，设备主动录音也存在两条处理路径。

> 后续更新见 [设备研究缺口与获取方案](DEVICE_RESEARCH_PLAN_2026-09-24.md)。1001 模式已完成两次长按的开始/停止对照，卡内列表出现对应文件；新抓包纠正了“主动事件仅 seq=0”的假设。此报告聚焦设备协议和能力边界，客户端集成需另行验收。

## 证据范围

- 当前 ADB 在线设备：Android测试终端（`REDACTED_ADB_SERIAL`）；另一台 ADB 设备处于 `offline`。
- Android测试终端 安装了 `com.example.recorder` 0.1.0 和 `com.alibaba.dingtalk.global`。独立版 App 起初显示 **A1 已连接、电量 2%**；这是未刷新的界面值。重新建立 GATT 连接后，设备通过 `0x0132` 实报 **27%**，固件 `V1.6.88-202601291628`，录音状态 `idle`。
- 系统蓝牙状态显示 `DingTalk A1` 为已连接的 LE 设备；连接记录在 17:34 左右出现成功事件。最近的连接参数日志为 `interval=12, latency=1, timeout=600, status=0`。这些是 Android 蓝牙栈日志，不是 A1 应用层应答。
- 当前 `logcat` 中出现 `A1Client: 收 cmd=0x000C ... len=30 binary`。原生 SDK 同时高频打印 `readAudioFrames` 日志，256 KiB 的 main 日志缓冲很快被覆盖，早于数秒的应用层调用难以保留。
- 随后在平板开发者选项启用完整蓝牙 HCI 记录并重启蓝牙。平板有 root，已从 `/data/misc/bluetooth/logs/btsnoop_hci.log` 只读导出实时原始包到被 Git 忽略的 `capture/btsnoop_2026-09-24_live.log` 与 `capture/btsnoop_2026-09-24_left_short.log`。原始包包含设备标识、鉴权及录音数据，不能公开上传。未做 opcode 扫描。
- 蓝牙重启后，App 一度仍显示“已连接”，实际 `BluetoothGatt.writeCharacteristic` 报 `DeadObjectException`；强制结束并重开 App、在界面重新连接后才重新建立有效 GATT 通道。这说明界面的连接标志不能单独证明底层连接可用。
- 09:02:41–09:03:08 UTC 的实时 HCI 含 3477 个 A1 ATT 片段、93 条完整 A1 消息，实测 FE1C `0x8002` 写入、FE1B `0x8005` 通知及 MTU 517。观察到鉴权 `0x0008`、状态 `0x0132`、能力 `0x0133`、选项 `0x0100`、文件同步 `0x0110/0x0111/0x0114/0x0115` 等双向交互。
- 历史抓包仍在 `capture/bugreport.zip`、`bugreport2.zip`、`bugreport3_enc.zip`。它们分别包含 4.1 MB、6.9 MB、9.2 MB 的 `btsnoop_hci.log`，可用 `tools/protocol_analyze.py` 复核。原始抓包包含设备标识和鉴权资料，不应直接上传或贴到公开 issue。

## 已确认的底层路径

| 功能 | 已知调用 | 证据等级 | 仍缺什么 |
| --- | --- | --- | --- |
| BLE 传输 | FE3C 服务；FE1C 命令写入、FE1B 通知；A1 头部 `type(1)+cmd(2,BE)+seq(1)+len(4,BE)` | 历史及本次 HCI；见 `FINDINGS.md` 7、11 节 | 后续按键事件的语义 |
| 定时任务下发 | 官方 `a9n` 从云端查询任务，过滤无效与过期项，转为秒，按开始时间排序；`m62.a0` 用 `0x011A` 发送 `{did,action:"set",current,params:[{sid,start,end}]}` | 官方 APK 静态代码 | 设备收到后的应答语义、断线/重启后的执行、取消/覆盖规则、容量和冲突处理 |
| 定时能力门槛 | `iy7` 将 `cap_schedule >= 2` 作为启用条件；本机当前固件在 `0x0133` 实报 `cap_schedule=1` | APK 静态代码 + 本次 HCI | 是否存在新固件支持等级 2；等级 1 设备收到 `0x011A` 是否接受及执行，尚未冒险强发 |
| 语音键预设 | `0x0100` 的 `aikey_option` 可 get/set；本机读回 `1000`。官方 H5 提供 `1` 语音备忘、`2` 开始/停止录音，功能开关打开时还可见 `4` 发给自己、`5` 发给悟空。官方桥接先保存云端 `voice_button_function_mode`，再将 `1→1000`、`2→1001`、其它值默认 `1000` 下发设备 | 8.3.48.3 APK + 官方 H5 静态代码 + 本次 HCI 读取 | `4/5` 的云端后续处理、本机逐项设置/回读、实体键行为与掉电保存 |
| 录音／电源键 | 未发现可重映射接口 | 仅为现有资料范围内的否定发现 | 不可据此断言固件层绝对无法重映射 |

静态证据入口：`decompiled/base/sources/defpackage/a9n.java:68-99,157-184`、`m62.java:2021-2052,1510-1542,2055-2079`、`iy7.java:2369-2381`、`decompiled/research/dex18-fallback/com/alibaba/dingtalk/dingerimpl/DingerInterfaceImpl.java:8932-8987`。历史能力值见 `FINDINGS.md:903-907`。三份历史 HCI 和本次 HCI 中 `0x011A` 均为 **0 次**，所以不能把下发格式称为真机验证成功。

定时同步的调用链进一步核对为：官方 App 回前台（`o62.a.onEnterForeground`）或收到设备任务推送且 `taskType=6`（`e5m`）→ `iy7.P0` 检查能力开关 → `a9n.g/h/j` 检查设备 ID、网络、BLE、OTA 和解绑状态 → `zg7.l` 带 `deviceId/accountType/accountId/scheduleTaskType=0/requestId` 查询云端进行中的任务 → `a9n.b` 过滤、排序并组包 → `m62.a0` 发 `0x011A`。同一时间的重复触发有原子标志合并；失败时最多按 `5` 秒间隔重试约 3 次。这里掌握的是**官方 App 的调度流程**，不是设备本身的离线计时、持久化或冲突策略。

独立版 App 原先在 `webview/DingerApi.kt` 将语音键界面值 `1/2` 原样写给设备，也将设备值 `1000/1001` 原样回给界面，与官方转换不一致。同日晚间已在 `<workspace>/a1app` 修正为 `1↔1000`、`2↔1001`，并明确拒绝尚无本地路由实现的 `4/5`，`compileDebugKotlin` 成功。该修正尚未在独立 App 连接 A1 时回归；`a1app` 工作区还有多处其他未提交改动。

## 官方原包再次核对与此前结论更正

从该版本原包可逐字段复核以下**客户端请求参数**：

| 步骤 | 请求参数 | 来源 | 验证程度 |
| --- | --- | --- | --- |
| 查询进行中的定时任务 | `deviceId`、`accountType`、`accountId`、`scheduleTaskType=0`、随机 `requestId` | 8.3.48.3 `DeviceTaskIService.queryOngoingScheduleDeviceTask` 调用链（`uso`） | APK 静态；未取得一条本账号的任务返回 |
| 下发到 A1 | `0x011A`：`{did,action:"set",current:<Unix秒>,params:[{sid:<整数>,start:<Unix秒>,end:<Unix秒>}]}`；无任务时 `params=[]` | 8.3.48.3 `qg2.d0`、`uso`、`ScheduleItemObject` | APK 静态；当前固件未出现实际应答 |
| 读取语音键设备值 | `0x0100`：`{did,action:"get",params:{key:"aikey_option"}}` | 8.3.48.3 `qg2.F` | APK 静态；本机读回值为 `1000`，但读取请求来自独立版 App |
| 设置语音键设备值 | `0x0100`：`{did,action:"set",params:[{key:"aikey_option",val:1000或1001}]}` | 8.3.48.3 `qg2.e0` | APK 静态；本机未逐档设置验证 |
| 保存语音键界面选项 | 云端 `voice_button_function_mode`：`accountType`、`accountId`、`belongingId`、`belongingType=2`、`settingKey`、`settingValue`、随机 `requestId` | 8.3.48.3 `DingerInterfaceImpl` → `t08.c` | APK 静态；没有官方账户的成功回包 |

`did` 由 `qg2.k` 从官方鉴权服务取出。这里列出的是**请求格式**，并不证明固件接受全部参数取值，也不提供云端创建/取消任务的完整服务端规则。

本地有 `apks/8.3.48.3/` 的 14 个官方 split 原包、较早的 `apk/base.apk`、`official_h5/` 的 `smart-hardware-ai-assistant/0.181.1` 前端和反编译材料。已核对 `decompiled/research/dex18/classes18.dex` SHA-256 前 16 位 `663aecbc221cfe29`，与 8.3.48.3 原包的 `classes18.dex` 一致；较早的 `apk/base.apk` 相应 dex 为 `67241002705c6f87`，不能把两个版本的混淆类名直接混用。8.3.48.3 的 `defpackage/qg2.java` 再次确认 `0x011A` 与 `{action:"set",current,params}`；`uso.java` 再次确认云端查询、过滤、排序；`jk8.java` 再次确认 `cap_schedule>=2` 门槛。

此前只说“语音键两档”遗漏了 H5 的两项条件选项。H5 `dd3fc05eaf0a1ed1801e.js` 的枚举实际有 `VOICE_MEMO="1"`、`START_AND_STOP_RECORD="2"`、`SEND_TO_ME="4"`、`SEND_TO_WUKONG="5"`；后两项分别受 `voiceKeyAddMe` / `voiceKeyAddWukong` 功能开关控制。8.3.48.3 的 `DingerInterfaceImpl` 设置路径先调用设备设置云服务保存 `voice_button_function_mode`（含设备 ID、账号类型/ID、`belongingType=2`、设置键值及随机 requestId），云端成功后才通过 `qg2.e0` 发送 `0x0100` 的 `aikey_option`。其字节码 fallback `W1` 只把界面 `2` 映射为 `1001`，`1/3/4/5` 均走默认 `1000`。由此可以确认**界面最多列四种预设，不等于固件支持四种直接键码**；`4/5` 的服务端实际结果仍未验证。

8.5.8.3 客户端还给出了 `4/5` 的本地分流：`pt8.g3` 收到 native 流处理结果 `body.source="device"`、`process="start"/"stop"` 时，读取本地缓存的 `voice_button_function_mode`。值 `4`（“发给我”）或 `5`（“发给悟空”）走各自的界面/流处理分支；`3` 还留有旧的 Aone 分支；其它值走普通语音备忘录分支。`body.source="device_chat"` 的音频块会送到当前语音输入或悟空会话。代码位置为 `apks/8.5.8.3/work/src/sources/defpackage/pt8.java:4423-4495,2947-2956,3409-3434,4052-4064`。这是**手机侧分流逻辑**；它解释了为什么 `1/4` 可共用设备值 `1000`，但仍不能证明“发给我”的服务器交付或悟空会话实际成功。

对现有 HCI 再按帧头复核：单独右键长按触发的 `0x0100 start/stop` 均为设备发出的 `type=0x31, seq=0`；官方 App 发起的语音键设置为 `type=0x13, seq=40`，设备应答回显 `seq=40`。同一版本的普通设置查询也逐一回显请求序号。历史抓包里官方 App 的初始 `0x0132` 请求曾用 `seq=0`，所以不能笼统规定“序号 0 一律是主动事件”。独立版应答等待者须至少同时核对命令号与序号，并针对 `0x0100` 区分带 `action=start/stop` 的设备主动状态与对应请求的应答；只按命令号完成等待者会误关联。

原包包含手机侧 `split_demand1.apk` 中的 `libDingerSdk.so`，但在 14 个 split 中未找到 A1 固件镜像。官方客户端代码能给出它如何发指令，不能直接给出设备固件如何在断网、断电、任务冲突或长短按阈值下执行。

## 本机 USB 与固件获取检查

2026-09-24，A1 接在本机 USB。Windows 即时列举到 `VID:PID 17EF:0101`、设备版本 `1010` 的 USB 复合设备，字符串为 `NuttX` / `Composite device`。`MI_00` 被绑定为 Android Composite ADB Interface，但 `adb devices -l` 中该设备为 `offline`；`MI_01` 是厂商自定义 HID，Usage Page/Usage 为 `FF00/0001`，输入、输出报告均为 128 字节，Feature 报告为 0。磁盘与串口枚举没有 A1 项，因此不存在可按 U 盘方式直接复制的固件分区。`NuttX` 是设备描述符线索，不能仅凭该字符串断言固件系统架构。

现成的 `tools/HidProbe.exe` 只读取 USB/HID 描述信息；`tools/HidListen.exe` 只打开输入方向被动监听。本次连续监听 10 秒收到 **0 条 HID 输入报告**。这仅说明当前状态下没有主动上报，不能说明 HID 接口没有功能，也不能证明它支持读回闪存。未向未知 HID 指令写入数据，未触发 USB 引导/升级模式，未刷机。

官方 8.3.48.3 客户端的 `OTAUpgradeManage.G` 从服务端给出的 `packageDownloadUrl` 下载以版本命名的 `.zip` 到 App 私有 `files/DingerRecord`；`OTAUpgradeManage.x` 随后以 `attrs:"ota@bin"`、`cur_version`、`new_version`、`offset`、`verify_code`、`filePath` 组装参数，交给手机侧 `DingerAudioTools.StartOta`。这提供了**将来取得合法 OTA 包后分析固件**的明确入口，并不等于当前原包内已有固件。已连接平板上该私有目录未能只读列出（root 进程遭系统权限拒绝），也未取得当前设备适配的 OTA 下载包。当前只能确认 USB 枚举与客户端升级路径，**尚未提取设备固件，也未完成固件逆向**。

## 官方 8.5.8.3 现场复核（同日晚间）

用户在平板打开官方钉钉后，`dumpsys activity` 显示前台为 `com.alibaba.dingtalk.global` 的 `CommonWebViewActivity`，蓝牙连接的关联包也是 `com.alibaba.dingtalk.global`。平板已安装版本为 **8.5.8.3**（此前本地分析的是 8.3.48.3）。已从平板安装目录只读复制 `base.apk` 和 `split_demand1.apk` 到 Git 忽略的 `apks/8.5.8.3/`；主包 `classes19.dex` 包含 A1 代码，反编译产物位于同一忽略目录的 `work/src/`。

当前官方设备页显示型号 `TALIX & DingTalk…`、固件 **V1.6.88**、电量 **89%**、录音加密为关闭、语音键定制当前为“语音备忘录”。页面中的序列号未记入报告或公开文件。用户称其为日本版；目前只确认这台设备的界面和固件值，不能据此推断日本版与中国版的硬件、云端区域或全部能力相同。

官方前台期间的私有 HCI 快照保存在被忽略的 `capture/btsnoop_2026-09-24_official_live.log`。该段实测 `0x0100` 多次读取 `aes`、`mode`，回包含 `aikey_option=1000`；随后出现 `aes=0` 的设置并获 `code=200`，再次读取返回 `aes=0`。同时有大量 `0x0115` 文件传输包。无法从包本身判断 `aes=0` 是用户点击开关、页面流程还是其它触发，因此不归因。原始文件含设备 ID 与录音数据，不上传。

8.5.8.3 静态代码中，`defpackage/pt8.java:5586-5594` 仍以 `cap_schedule>=2` 启用定时能力；`defpackage/ga8.java:613-625` 仍以 `scheduleTaskType=0` 查询；`defpackage/lj2.java:2186-2217` 仍向命令 `282`（`0x011A`）下发 `{did,action:"set",current,params}`。`DingerInterfaceImpl.k2` 的 fallback 字节码显示界面值 `2→1001`，`1/3` 及其它值默认 `1000`；`lj2.i0` 向命令 `256`（`0x0100`）设置 `aikey_option`。这印证核心客户端格式跨版本未变；仍不能代替本机的定时执行及按键模式逐项实测。

本机 8.5.8.3 官方“语音键定制”页实际只显示三项：“语音备忘录”“开始和停止听记”“发给我”（缓存旧 H5 曾列出的“发给悟空”在此账号/地区未显示）。打开页面时，HCI 未出现专门的 `aikey_option` get；但通用 `0x0100` 设置读取的完整回包带 `aikey_option=1000`。用户点第二项后，10:19:26 UTC 官方 App 发 `0x0100 {action:"set",params:[{key:"aikey_option",val:1001}]}`，设备回 `code=200`，界面勾选第二项。恢复第一项后，10:20:46 UTC 同一路径下发 `val:1000` 并成功。随后短暂选择第三项“发给我”，10:22:03 UTC 下发的仍是 `val:1000`，设备回 `code=200`；这说明第一、三项在设备端共享键值，差别至少部分在客户端/云端处理，不能凭 BLE 判断“发给我”的云端具体动作。10:22:42 UTC 再次恢复第一项，界面勾选和 `val:1000` 成功应答均确认。原始包和截图仅存 Git 忽略的 `capture/`。

8.5.8.3 的手机侧 `libDingerSdk.so` 与旧 8.3.48.3 不同（长度分别 7,481,128 / 7,415,480 字节，SHA-256 前 16 位分别 `61572524ea708221` / `b36f14782679bbd0`），所以涉及 native 行为时不能只引用旧包。官方“固件升级”页实际显示 **“当前已是最新版本”，当前版本 V1.6.88**；本次没有可供下载的新 OTA 包，也未开始升级。

### 独立 App 接下来要补的闭环

1. **实体键主动录音**：`A1Client` 会把所有帧发到 `frames`，但应用层没有订阅 `0x0100` 的设备主动 `start/stop`。`MainActivity` 和 `OfficialUiActivity` 虽收 `session.audio`，转写器仅在已启动时接受音频，`A1Store.accept` 也只是按 fid 缓存在内存；没有按键停止时自动定稿、封装和入库的路径。需要把“按键开始→音频→按键结束→文件/转写入库”做成一条会处理断线与重复事件的生命周期，并在真机上验证。
2. **命令应答关联**：`A1Client.request` 目前按 `cmd` 存单个等待者，`onIncoming` 也按 `cmd` 完成，不核对帧类型与 `seq`。设备主动 `0x0100` 可以与设置查询的应答撞在同一个命令号；应按实际抓包验证 `seq` 匹配规则后收紧，避免误把按键事件当设置成功。
3. **定时策略**：独立 App 没有 `0x011A` 的本机任务下发闭环；本机固件 `cap_schedule=1` 低于新版官方门槛 `2`。若目标是手机/平板在旁执行，应由 App 自己调度并处理 Android 后台限制、断线重连、重启恢复；若目标是卡片单独离线执行，仍需支持该能力的固件及实测。
4. **云端预设和版本差异**：“发给我”与“语音备忘录”都下发 `1000`，独立 App 可自定收到音频后的本地动作，但需要单独的动作设置和路由。现有独立 App 打包的 `libDingerSdk.so` 仍与 8.3.48.3 相同；升级至 8.5.8.3 原生库前要做文件同步/音频兼容性测试，不应仅因版本新就替换。

## `0x000C` 的新观察

对历史 HCI 的 `0x000C` 通知做离线重组后，常见 30 字节负载有以下结构：

```text
5A 5A | 00 14 | 2 字节内部序号 | 2 字节保留/状态 |
20 字节事件记录 | 5A 5A
```

`00 14` 对应 20 字节事件记录；250 字节负载相应包含 12 条记录。记录开头 4 字节按大端 Unix 秒可解释为合理的发生时间，第 5 字节在历史样本中出现 `01/05/0B/0C`，本次重连样本有 `03`。这是**结构观察**，各事件码的含义、后续 15 字节的布局仍待实测。历史录音动作附近出现 `0C → 05 → 0B` 或 `0B → 0C → 05`，并伴随 `0x0100` 录音状态、`0x0116` 流属性；只能证明相关，不能把某一事件码直接命名为“左键短按”或“右键长按”。

## 现场左键短按：同步过程干扰

用户短按左键时，卡片提示一直在同步文件。紧随其后的 HCI 快照（09:02:41–09:05:19 UTC）累计有 20471 个私有 ATT 片段、448 条完整消息，其中 `0x0115` 文件传输请求和应答各 213 条。相对先前快照，新出现一条 `0x000C`，时间 09:04:25 UTC，事件字节 `01`；没有新的 `0x0100` 录音控制。此前抓包中 `01` 也在充电过程中出现，且本次按键没有精确主机时间戳，因此**不能认定 `01` 是左键短按事件**。要在同步结束、设备空闲时重新做单动作差分。

## 现场右键组合动作：录音可确认，单键语义待拆分

用户随后连续做右键短按两次、长按一次。`capture/btsnoop_2026-09-24_right_keys_2.log` 在 09:24:58 UTC 捕到设备主动 `0x0100` `action=start,code=200`，随后 `0x0116` 流属性、`0x0117` 音频帧，约 0.66 秒后又有 `0x0100` `action=stop,code=200`，期间 `0x000C` 事件字节为 `0C/05/0B/0B/0C/05`。这证明按键组合触发了设备录音与实时音频流；三次动作靠得太近，无法把某个事件字节或开始/停止分别指派给短按或长按。

之后单独短按右键一次，用户报告没有明显提示。`capture/btsnoop_2026-09-24_right_single.log` 在该动作后没有新的 A1 ATT 消息，最后消息仍为 09:24:58 UTC；`dumpsys bluetooth_manager` 同时仍显示 A1 的 GATT 通道打开。这一观察只说明**该次单击没有产生可见 BLE 协议消息**，不能推出它在设备本机没有任何作用。

再单独长按右键约 2 秒，用户观察到录音/亮灯。`capture/btsnoop_2026-09-24_right_long.log` 在 09:30:25–09:30:27 UTC 再次出现设备主动 `0x0100 start(code=200)` → `0x0116` → 多个 `0x0117` 音频帧 → `0x0100 stop(code=200)`。`0x000C` 在开始阶段为 `0C/05/0B`，结束阶段为 `0B/0C/05`。**右键长按触发按住期间的实时音频流**已有单动作实测依据；是否同时在卡内保存独立文件、固件是否提供其它模式，仍需另外验证。

最后一次原拟做左键单独短按，但用户实际先短按右键唤醒，又短按右键与左键。`capture/btsnoop_2026-09-24_mixed_buttons.log` 在这些动作后没有新增 A1 应用层消息；只能记录为混合动作，不足以判断左键短按的独立行为。已进一步询问卡片的灯光、语音与当前录音状态。

## 借鉴公开项目后的实验顺序

[Daedalus FW920 研究](https://github.com/DaedalusApps/daedalus-notetaker/blob/main/reverse/WIFI_DISCOVERY.md) 的有效方法是把 APK 静态分析、单一动作 HCI 抓包、差分和实机回放分开记证据。FW920 的 `B0B0` 服务及命令格式与 A1 的 `FE3C/FE1C/FE1B` 不同，不能直接套用其 opcode。其仓库里用过的盲扫与伪造 OTA 响应，不适合作为 A1 第一轮实验：A1 已知有恢复出厂 `0x0004`、删除文件 `0x0113` 等有副作用的命令。

[PLAUD NOTE NB-100 逆向记录](https://github.com/Kurikara-dev/plaud-note-nb100-re) 的可借鉴点是逐项标记哪些结论经过真机端到端验证、哪些只来自静态分析，并把连接、鉴权、文件传输、音频格式、设置和未验证的 Wi-Fi 分开记录。它针对的是另一台设备；其命令编号、鉴权和数据格式均不能移植到 A1。其全范围设置探测也不适合直接对 A1 实施，因为 A1 存在已知有副作用命令。

完整 HCI 记录现已生效。下一步在同步结束、设备空闲时每次只做一个动作：左键短/长按 → 右键短/长按 → 官方语音键设置读取与两种预设的设置/恢复 → 若将来固件能力值达到 2，再做短时定时任务的创建、触发和删除。每一步保存动作时间、App 日志、HCI 片段、设备屏幕/声音结果，并在断线与重启后复查持久性。当前能力值为 1，不主动强发 `0x011A`。

## 当前结论

连接、鉴权、状态/能力读取和文件传输已有本次实机 HCI 证据。定时任务目前是**下发接口已解、当前固件能力值低于官方门槛、执行行为未验证**。右侧语音键的**长按实时音频、松开停止**已有单动作实测；官方界面有两种基本预设及条件性的云端预设，独立版映射代码已修但未真机回归。左键独立长按、两枚物理键任意自定义、云端后续处理以及 `0x000C` 的完整事件语义都尚未掌握。
