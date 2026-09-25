# 日本版 A1：官方 8.5.8.3 客户端调用链研究

日期：2026-09-25。范围：除固件更新之外的客户端可见功能。只读分析本地官方包、反编译结果、ELF与已有现场记录；本轮未改独立App代码、未调用设备命令、未改变设置、未执行云请求。

## 1. 结论与覆盖率口径

已覆盖所要求的 **6/6功能域**，建立下方 **28项研究矩阵**，为18份重点Java源码与15个原生符号建立可复查索引。它们是研究清单的覆盖，**不是设备功能完成率**。没有当前日版账号所有动态页面的清单，不能给出“官方功能已掌握百分之多少”的可靠百分比。

- APK主体控制入口、录音参数、下载/取消/删除、状态、定时下发、设置云同步均已找到具体调用位置。
- 本次深入恢复了原生补传参数构造、30秒同步超时，以及Java层定时过滤/排序/重试、WiFi有条件重试、语音键云设置与设备设置的先后顺序。
- 所有28项均有定位或明确的缺口；并非28项都已恢复完整调用链。新绑定凭据、云端业务执行、完整FsyncV2状态机、日版动态UI及硬件行为仍有缺口。
- **本次新增功能级日本版实机验收：0项。** 另一次只读基线确认官方8.5.8.3运行并持有GATT连接，仅证明连接，不证明录音/同步/云任务成功。此前1000/1001抓包为历史证据。

## 2. 原包、源码与原生库可追溯性

| 文件（相对apks/8.5.8.3） | 字节数 | SHA-256 |
| --- | ---: | --- |
| base.apk | 398237826 | f2bacad38dde7159ac36c5550fc181b6c56c2f142252c9c9ef942bebb907fe7f |
| split_demand1.apk | 7689145 | d4c0d3815debc17866bce292c4aa6b7d84200b56a00b6f3dae69f6a5cb73b569 |
| work/classes19.dex | 6067044 | 47a37ba0caf77daed57dcfcd2f13007627f1c6bb4a74ef71b8f4c894e491d87e |
| work/libDingerSdk.so | 7481128 | 61572524ea708221e99fe8d1c7ab977b84c20050103b97a0fceb01db69fc2c41 |

本次直接从ZIP成员重新计算并确认：base.apk内classes19.dex等于研究DEX；split_demand1.apk内arm64-v8a/libDingerSdk.so等于研究ELF。源码目录共有1798个Java文件，来自已取得的局部反编译，不是整个官方应用所有DEX的完美源码。

- 源码根 `apks/8.5.8.3/work/src/sources/`，下文行号以当前文件为准。
- `I` = `com/alibaba/dingtalk/dingerimpl/DingerInterfaceImpl.java`。
- `L` = `defpackage/lj2.java`；`P` = `defpackage/pt8.java`。
- 其他短类名也位于defpackage；数据、wifi类位于com/alibaba/dingtalk/dingerimpl对应子目录。
- 定位索引：[CLIENT_EVIDENCE_INDEX_8.5.8.3_2026-09-25.json](CLIENT_EVIDENCE_INDEX_8.5.8.3_2026-09-25.json)，含源码SHA、方法行号、原生符号VA/大小。
- ELF地址为虚拟地址，不是文件偏移/运行时地址。原生两个函数的本次反汇编留在忽略目录 `apks/8.5.8.3/work/client_timeout_gap_disassembly_2026-09-25.txt`。
- 独立App仍打包旧8.3.48.3 SDK。不能将本报告8.5.8.3原生行为直接当作独立App现有能力。

证据标记：**S** APK静态源码/DEX fallback；**N** 原生符号或反汇编（逐项注明）；**H** 历史抓包/现场记录；**J** 本次日版实机。证据类型不是可相互替代的“分数”。本轮矩阵没有新增J功能证据。

## 3. 28项功能调用链矩阵

“未定位”表示仍需挖掘，不能理解为不存在。UI列所列为实际业务桥入口，不保证当前日版账号一定显示该页面；旧H5与当前服务器页面存在版本差异。

### A. 录音与按键

| ID | 入口 → 业务 → JNI/设备 | 云端、回调、状态/持久化 | 证据与缺口 |
| --- | --- | --- | --- |
| R01 App录音控制 | recordOperation → I.c0:4577 → P.q3:5104 → L.P:1759 → R:1814 → SendCmdToDevice；0x0100，did/action | P.q3先拒绝未连接/升级占用；P.c0回调；录音状态经DeviceSyncStatus及push传播 | S；N ParseRequestAudioOpt 0x230780/ParseResponseAudioOpt 0x22ab6c为历史分析。App开始/暂停/恢复的新独立版闭环未验 |
| R02 右键实体事件 | 设备主动0x0100 → 原生请求/响应分派 → P录音事件处理；不能只认seq0 | start/stop与流头/收尾分开；get/set不是录音事件 | S/N/H；历史1001是type13、官方同seq/type31应答；当前客户端仍需单次动作回归 |
| R03 语音键设置 | I.handleSetSettings:3544 → s98.c → I.u.onSuccess:2555 → L.i0:2225；0x0100 action=set，params数组含aikey_option | 先云更新voice_button_function_mode，再更新q98缓存，再写设备；BLE失败可留下云/卡不一致。读入口I:3381、i0:1160优先云设置，缺值才L.G查卡 | S/H；历史设备1000/1001读写成立，重连一致性待验；不是任意自定义固件按键脚本 |
| R04 音频后续动作路由 | P.g3:4423按source/process分派；q98.n:395读取voice_button_function_mode | device_chat/voiceprint/device分流；开始/结束决定备忘、助手、发给我等后续；DeviceSyncStatus voice_memos_start/finish | S；选项与原生1000/1001不一一对应。云投递执行体和日本账号可用性未全恢复 |
| R05 左键与声纹 | 左键未找到独立重映射入口；声纹L.X:1929 → 0x0101，action/type=voice_print | P.g3:4428可将device_voiceprint的oggPath/duration送sjw.e；身份服务未完整追踪 | S；左键旧动作混杂，不能归因；声纹与普通按键不是同一事务 |

### B. 音频格式、实时流与补传

| ID | 入口 → 业务 → JNI/设备 | 状态、落盘与错误 | 证据与缺口 |
| --- | --- | --- | --- |
| A01 流头 | 0x0116 → ParseRequestStreamHeader 0x22e340 | attrs/fid/fsync/stream_type/file_ver/aes/alg_mode/incognitomode/sid决定录音对象；stream_type2会中断文件传输 | N/H（机制见旧原生报告）；版本/组合帧适配必须按头信息，不能固定84字节切所有流 |
| A02 实时包 | 0x0117 → ParseRequestStreamPacket 0x22edc0，DingerStreamRecord/V2 → Java流观察者 | 停止后仍可能存在缺口；旧包、重传及补静音处理不是普通顺序拼接 | N符号本次复核，状态机制历史反汇编；阈值、乱序边界未完全恢复 |
| A03 补缺包请求 | RequestGapFill 0x239758 → SendCmdToDevice(0x0111) | fid/s_off/b_size/did/progress/gap_mode/gap；具体公式见第4节；持久化.gaps机制见旧报告 | N本次反汇编；gap分配、重试次数上限、文件版本差异仍缺 |
| A04 同步超时 | CheckFileSyncTimeout 0x232fa8 | 检查有效传输状态和时间戳；>=30000ms清相关对象/标志，回调file_sync_abort，reason=timeout，fid | N本次；并非所有请求统一30秒，也未证明设备自身超时。时间戳所有刷新点未全恢复 |
| A05 转换/解密 | WiFi DingerDownloader.AnonymousClass1.o:131 → OpusConvertToOgg；JNI 0x1c1e48 →实现0x2f8e0c | 转换返回0才进入后续；OggDecryptUtil::DecryptOggFile 0x28c354存在；DingerEntryObject保存isEncrypt/filePath/size | S/N符号；密钥生命周期与每种容器版本的认证/完整性规则未全恢复；不能直接当裸Opus |

### C. 文件索引、传输与管理

| ID | 入口 → 业务 → JNI/设备 | 云端、持久化及错误 | 证据与缺口 |
| --- | --- | --- | --- |
| F01 文件索引 | 列表业务 → L.A:1440/B:1466/z:2723 → 0x0110 | s_fid/e_fid/recently；B/z存在向后续fid推进的分支；DingerFileListResult、hr8/DBManager存档 | S；分页边界、录制中列表一致性需要测试文件核对 |
| F02 BLE下载 | I.k:5307 dingerFileOperation → 文件队列 → L.n0:2375/y:2703 → SendFileSyncCmd | fid、偏移/模式参数、fileIndex/fileCount；返回消息ID并注册P.w3；原生处理文件头/块，不等于调用返回就完成 | S（n0需看fallback控制流）/N JNI0x1c5924、实现0x232360；独立版完整音频仍待验 |
| F03 取消与重试 | I.k:5327 cancelSyncFile → k1；L.l:2285 → 0x0112 | 原生SendCmdToDevice发送0x0112前AbortFileTransfer（旧分析）；L.n0有重试参数和BLE连接检查 | S/N历史；取消应答与最后块竞争、重新下载起点未逐场景验 |
| F04 WiFi快传 | I:3178/p:5597能力门 → L.I:1626 0x0120 → WifiTransferDialog:509 | 返回WiFi信息；URL追加14位零填充fid；DingerDownloader → 转换 → 入库 → onSuccess；L.q:2540以0x0121关AP | S；408/503有条件最多5次重试，等待1到5秒（见第6节）；热点掉线恢复需实测 |
| F05 删除/回收站/恢复 | I.s:5755分支 → P.E1:3146/state1删除、3回收、0恢复；deleteAudioFiles → P.C1:3073 | 按fileId区分云/本地；fs8.a/b→DeviceFileIService.deleteFiles/recoverFiles；部分开关允许L.t:2584发送0x0113删除卡原件 | S；本地删下载缓存、回收站和卡删除不能共用语义。只允许专用测试文件另批验收 |
| F06 导出/合并/分组 | I.s:5811/5832/5835 → P.P2/S1/v4；hr8管理DingerEntryObject | fid、deviceId、fileId、account、groupId、minutesId、isEncrypt等分开保存；导出/转换有独立进度push | S入口/数据层；格式列表、全部导出/合并原生分支及云分组事务未追到底 |

### D. 设备状态与设置

| ID | 入口 → 业务 → JNI/设备 | 回调、持久化与约束 | 证据与缺口 |
| --- | --- | --- | --- |
| D01 鉴权/初始化 | 蓝牙连接 → L的connect/auth分支:1189 → 0x0133；更早0x0009握手:1013 | corp_id/token/model/timestamp/sdk_ver；L.k:2260补did；P:5582读取能力，f4再查状态 | S/H；凭据取得及新绑定完整流程还未恢复；不记录真实token或密钥 |
| D02 电量/空间/录音状态 | I syncStatus → P.f4:4382 → L.w:2638/0x0132；L.p0:2517/0x0004电量 | DingerDeviceStatus audio_status/fid/duration/battery_percent/storage_remain等；P.h1:4510还可由云DeviceModel构建状态 | S/H；云缓存和BLE实时值必须区分；本次只确认连接未读到有效状态日志 |
| D03 模式/音源 | I handleGet/SetSettings:3378/3411 → L.F/f0、Y/l0 → 0x0100 get/set | mode、audio_source、audio_source_switch；一般params数组key/val；callback错误必须向UI传播 | S；枚举、模式适用条件及重连持久性需本机验证 |
| D04 加密/隐身/流开关 | I:3389/3421 → L.x/Z、C/b0/c0/d0、e0 | aes、incognitomode、one_shot_incognito、force_sync_incognito、upload_stream；与云enable_incognito_transcribe分离 | S；不能把云转写隐私开关当设备加密；重连初始化是否覆盖用户设置需核对 |
| D05 默认参数与能力门 | L.S/T:1820/1851 → 0x0137 action=get/set；P:5583能力开关；I:3735灰度入口 | remark/stream_record/ble_conn_param_auto；cap_schedule>=2、cap_aikey_option>=1等；WiFi另查机型/版本/灰度 | S；params可为对象，不应全局强制数组；其他耳机/4G字段不得套入A1 |

### E. 定时任务

| ID | 入口 → 业务 → JNI/设备 | 云端、状态、重试 | 证据与缺口 |
| --- | --- | --- | --- |
| T01 查询与触发 | P.s1:5210能力门 → hsp.g/h/i → ga8.k:611 | DeviceTaskIService.queryOngoingScheduleDeviceTask：deviceId/accountType/accountId/scheduleTaskType0/requestId；返回scheduleTasks | S；定时创建/编辑UI及服务器生成sid规则未全恢复。当前历史cap1会被官方门槛挡住 |
| T02 整理与下发 | hsp.b.onSuccess:74 → ScheduleObject → L.g0:2186 → 0x011A | current和start/end统一秒；params为sid/start/end列表；过滤无效/已结束任务并排序，空结果仍发空数组 | S；是否覆盖/清空、最大数量、离线执行和断电持久性只能靠卡响应与实测确认，不能盲发空数组 |
| T03 环境与重试 | hsp.j:164验证网络/BLE、非升级、非解绑；a.onException:44 | 初次失败后最多追加3次，间隔5秒；AtomicBoolean合并检查，避免并发查询/下发 | S；原生通用发送层已知，固件定时执行内部不可由客户端包推出 |

### F. 账号、云同步与关联功能

| ID | 入口 → 业务 → 服务 | 返回、持久化与错误 | 证据与缺口 |
| --- | --- | --- | --- |
| C01 设备列表/账户/解绑 | I queryDeviceList:4297 → o98.a:137 queryUserBindDevices；解绑o98.c:169 → DeviceIService.unbindV3 | accountType/accountId/deviceId/devServId；x78保存当前设备、账号映射；解绑不是清本地BLE地址 | S；新绑定链、组织策略、日版权限仍缺；不做解绑试验 |
| C02 云连接占用 | I:4268/6283 → j78.c/d/e → DeviceConnectionIService | query/request/update连接；requestId/appDeviceId/appDeviceName/state；j78有重复状态比较 | S；“被另一客户端占用”的判定需要服务响应，不能用本地蓝牙已连接代替 |
| C03 云设置/自动纪要 | I设置 → s98.b/c queryDeviceSettings/updateDeviceSetting；q98.s/t缓存 | 写belongingId/type2、settingKey/value；查询settingList；q98.f:220映射语言/LLM/模板/说话人分离参数 | S；缓存不是服务端永久保存证明，服务认证/组织权限未知；真实云写另确认 |
| C04 转写、翻译、纪要和上传 | ga8内DeviceTaskIService createRecordTask/createTranslateTask/createGenerateMinutesTask/createUploadFileTask；P.g3实时源路由 | Translate返回audioStreamWssUrl；纪要检查minutesId/mobileMinutesUrl或async，空结果有失败分支；DingerEntryObject记录fileId/minutesStatus等 | S部分链；WSS消息体/任务续接/上传签名、投递到人/组织/知识库、模板市场/权益需继续分析其他DEX与动态服务，不宣称与本地AI等价 |

## 4. 原生新发现：补传参数与超时

### 4.1 RequestGapFill，VA 0x239758，980字节

本次检查ARM64指令、相关只读字符串和PLT重定位，确认：

- `GetFrameSize()`返回非零优先使用；为0时用对象内候选帧尺寸，候选<=0则回落80。**这是此补传分支的帧步长，不能解释成所有音频帧固定80字节。**
- 读取GapInfo两个32位值s/e；`s_off = 80 + s * frameSize`。
- `b_size = e == 0 ? 0 : (e - s) * frameSize`。e=0走特殊分支，不在未实测前保证所有固件都把长度0理解为传到EOF。
- JSON字段：fid（字符串）、s_off、b_size、did、progress=0、gap_mode=true、gap。
- gap在该处打包为“递增计数低16位放高半字 + 另一状态值低16位”；这两字段的业务名称/上限仍需恢复，不凭日志标签猜测。
- 0x239a30设置命令号0x0111；0x239a38经PLT调用SendCmdToDevice。
- 写入当前fid/偏移/缺口状态、标记传输活动、记录steady_clock时间后才发送。

证据地址：0x2397b0读取s/e；0x2397c0计算长度；0x239808—0x239810计算偏移；0x239908—0x23990c打包gap；0x239a30命令号。字符串地址0x5fdbd3=s_off、0x5fdbd9=b_size、0x5fdbe0=gap_mode、0x614e70=gap。

仍未知：缺口收集阈值、静音替代与补传边界、超大gap/倒序区间防护、.gaps持久化恢复、重试终止与完整性条件；未调用该函数或发送报文。

### 4.2 CheckFileSyncTimeout，VA 0x232fa8，528字节

- 先检查活动标志与有效时间戳，再用steady_clock计算经过毫秒数。
- 0x233004加载0x7530=30000，0x233008比较；小于门槛返回。
- 达门槛清相关对象/活动标志，构造type=file_sync_abort、reason=timeout、fid，经回调事件号5发给上层。
- 日志字符串0x60025e明确单位为ms。不是“30秒内整个大文件必须下载完”，是该状态的时间差检查；尚需追完更新时间戳的所有位置才能精确定义其全部触发条件。

## 5. 语音键设置：两层状态，不能只看一个参数

顺序已明确：UI选择 → 云voice_button_function_mode写成功 → q98缓存 → 映射 → 卡aikey_option写入 → UI成功/失败。

普通反编译 `I.k2:5391` 出现空switch，不能信它“永远返回1000”。已核对现有DEX fallback `work/DingerInterfaceImpl_fallback.java:13073`：选项"2"走1001，"1"、"3"及默认走1000；与历史官方设置抓包相符。更多服务器选项可能仍沿默认1000，随后由客户端路由音频。不能因此声称固件认识全部UI选项。

读设置先看云缓存，有值时不一定读卡；所以界面选中不证明设备真实已写入。设备写失败时，云值可能已更新。独立实现需明确自己的状态来源和失败回退，不宜直接照搬表面UI结果。

`L.G`读取aikey_option使用params对象；`L.i0`写入使用params数组。其他get/set也有差异。命令号相同不代表请求体形状完全统一。

## 6. 两类重试和结果语义

- **定时**：hsp.a失败计数从0开始，old<3再延迟5000ms，最多初次+3次；重入会登记待续查。服务为null等路径可能不回调，不能假设每个包装函数都有统一超时。
- **WiFi**：DingerDownloader.java:232只有开关f开启、错误408/503且计数<5才重试；自增后按count*1000ms等待。其它错误直接失败。HTTP完成后仍需要转换、元数据/DB更新，最后才发成功给上层。
- **通用BLE响应**：L.L:1671检查消息、body及可选命令号；无code会按默认成功处理，200/100/202/653/654可继续交给上层。**这些不全等于业务已经完成**，必须继续看具体回调。独立版不应把所有非200统一当最终成功，也不能忽略异步状态。
- **文件**：DingerEntryObject保存fid和云fileId、账号/设备、媒体路径、加密/隐身、纪要等多组状态；一个fid有文件不意味着已上传/已转写/已生成纪要。

## 7. 机型和地区边界

- P:5583读取cap_remark/cap_voiceprint/cap_incognitomode/cap_schedule/cap_aikey_option/cap_audio_source，各自门槛不同；本机历史cap_schedule=1，而官方启用需>=2。
- I.recordOperation:4626存在4G RPC路径；x78按devServId等判断，不能转用到BLE A1。
- L.o:2473的device_role/另一耳文件检查、DingerDeviceStatus左右耳/耳机盒电量、a2dp等属于共享SDK能力线索，不计入本机A1已支持功能。
- WiFi同时受灰度、连接、机型与版本约束；账户云设置及日本服务端返回不在APK控制范围内。包名/版本相同也不保证两地区可见功能一致。

## 8. 无法仅靠包内确定的内容与最小补证

| 未知项 | 最小安全证据 | 暂不做的动作 |
| --- | --- | --- |
| 左键真正事件与任意重映射能力 | 空闲基线后只短按左键一次，记录按键时间、流/状态/诊断；若开始录音再单独给停止步骤 | 不混按、不长按关机、不枚举参数 |
| 当前1000/1001独立版行为 | 按当前已知模式录一段10—20秒非敏感测试音频，拆开开始/停止并检查产物 | 不重复官方模式设置实验，不同时改多个设置 |
| 多帧布局与实际补传 | 先离线比对既有完整录音与流头；仍不足时只对专用短测试录音制造一次经确认的断连 | 不对重要录音制造故障、不盲发gap命令 |
| 设备离线定时/持久性 | 先只读cap及当前日版官方页面；仅若官方允许且单独授权，建一个短任务观察下发与执行，再按正常界面取消 | cap不足时不绕门槛；空params可能清计划，不能当无害探测 |
| 加密/隐身真实作用 | 先读回现值与文件attrs；后续另批一段测试录音对照并恢复原设置 | 不更换密钥、不改现有重要录音属性 |
| WiFi重试与完成条件 | 一条专用测试fid下载，记录HTTP→转换→DB→关闭热点；异常场景另批 | 不把HTTP成功当音频成功、不同时跑BLE下载 |
| 新绑定/云权限/投递 | 优先分析其余DEX中的服务模型和RPC适配，再用现有账号只读查询核对字段；外发/解绑需单独授权 | 不解绑重绑、不发送消息、不查询无关账号 |
| 动态UI总量/地区差异 | 用户打开当前账号各可见页面，记录入口及只读请求；建立当前日版页面清单 | 不用旧H5可见项充当当前页面全集 |

下一轮按最小风险顺序：补全动态页面清单与只读设置来源 → 独立版连接/一段短录音 → 完整文件下载可播放 → 专用录音异常恢复 → 最后设置持久性、定时和云事务。已有官方模式1001成功记录不重复计数。

## 9. 本轮边界与材料

本轮新增研究矩阵、定位索引和忽略目录中的原生反汇编；没有修改App、没有下载安装/启动新APK、没有发任何BLE/WiFi/云端指令，没有公开上传原包/抓包。

历史证据另见 [NATIVE_CLIENT_FLOW_2026-09-24.md](NATIVE_CLIENT_FLOW_2026-09-24.md)、[RESEARCH_AUDIT_2026-09-24.md](RESEARCH_AUDIT_2026-09-24.md)。独立版46项功能验收另见 `<workspace>/a1app/docs/A1_REPLACEMENT_AUDIT_2026-09-24.md`；本研究不覆盖其完成状态。
