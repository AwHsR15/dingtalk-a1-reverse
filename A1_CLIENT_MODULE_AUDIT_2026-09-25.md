# A1 官方客户端逐模块审计

日期：2026-09-25。目标是自主控制 A1、完整取得和管理录音，并将转写、翻译、总结、备忘和动作路由接到自有/本地服务。本文给出已读代码的实际行为、替代接口及证据边界，不以接口数量代表研究完成。

范围不包含固件升级以及钉钉组织、工作区、联系人、团队协作。配套功能保留，包括声纹采集、标记、播放、导出、合并、裁剪和自动处理；通用 SDK 中其他耳机/4G 设备代码不自动算作 A1 能力。

**后续范围及证据更新：** 未发现官方左键自定义接口，左键任意重映射不在目标范围。右键1000/1001继续按已知参数支持。无root接入和音频补传的本轮新增证据见 [接入与音频收尾](A1_ACCESS_AND_AUDIO_CLOSURE_2026-09-25.md)：已验证组合包序号规则，并定位缺口完成后“先发送应答、再请求下一缺口”的原生回调，更新下文相应未闭合项。

## 1. 证据与完成标准

### 本卡已解决事项更正

此前将剩余问题概括为“首次配对、按键、音频可靠性”，容易掩盖已经完成的工作。按现有记录，应区分如下：

- **本卡导入凭据后的离线鉴权已解决**：`FINDINGS.md:303–318`记录从root手机官方缓存提取deviceSecret、两组挑战值验证；365–375记录独立客户端鉴权code=200及文件下载成功。没有理由把已取得密钥再列为本卡当前使用的阻塞项。完全未绑定新卡的首次签发、重置后的生命周期是另一个尚未闭合的范围。
- **右键已知模式参数及主要动作已有实测**：`aikey_option=1000`已有按住送音频、松开停止的观察；`1001`已由官方设置获得code=200，两次长按测试分别开始持续录音、停止，随后恢复1000。证据见`DEVICE_RESEARCH_PLAN_2026-09-24.md:9–25`。不能再笼统写成“按键映射参数没拿到”；未证明的是任意新增按法或左键重映射。
- **音频正常路径已有历史成功记录，异常自动修复仍未完成**：`FINDINGS.md:375,625–634`记录完整小文件下载及实时转写；独立App当前`A1StreamCapture`保存未完整音频为`.incomplete.opus`，这是防止假成功，并不实现缺口自动补齐。当前版本的组合帧、断线补传、最终文件校验闭环仍须完成和验证。

上述实测为历史记录复核，本次未重新操作设备。研究完成情况应累积已有证据，不能因新版本未验收就将过去已证明的能力全部退回“未知”。

- **J**：官方 APK 8.5.8.3 的 Java/DEX 静态行为。`J19` 根目录为 `apks/8.5.8.3/work/src/sources`；短类名均在 `defpackage`。
- **N**：该版本 `libDingerSdk.so` 的 ARM64 指令和已解析 PLT 调用；地址为 ELF VA。
- **W**：本地保存的官方 H5 `smart-hardware-ai-assistant/0.181.1/mobile-recording/dd3fc05eaf0a1ed1801e.js`。这是独立页面资源版本，**尚未证实它与当前 APK/日版账号实时页面完全一致**；下文偏移是解码后字符串的字符偏移，不是文件字节偏移。
- **H**：历史现场记录，只作交叉证据；没有本轮新设备验收。
- **替代契约**：根据实际业务边界归纳的独立实现要求，不声称是官方 API 原文。

深度分为：**主链闭合**（已读入口、成功及主要失败出口，可制定替代契约）、**局部闭合**（关键叶子算法/版本分支仍未知）、**仅边界明确**（实际内容在未取得的远端页面/服务）。主链闭合不等于设备验收通过，更不等于恢复全部原始源码。

本轮同时检查 Java 业务层、JNI/原生音频层和 H5 消费层。模型清单另见 [云接口字段索引](CLOUD_CONTRACT_INDEX_8.5.8.3_2026-09-25.json)，先前设备命令定位见 [28 项调用链](CLIENT_CALLCHAIN_MATRIX_8.5.8.3_2026-09-25.md)。这些资料辅助定位，不能替代本报告的状态和失败分析。

## 2. 连接、协议与权限

| 模块 / 用户功能 | 入口与状态流 | 输入输出、设备/本地/服务边界 | 失败与恢复 | 自主替代契约、证据与深度 |
| --- | --- | --- | --- | --- |
| M01 发现与 BLE 连接 | `I.c:4518` 解析连接信息；`Bluetooth/a.s0:1473` 直接按 MAC 连接；GATT callback 进入 MTU/服务发现/通知订阅。不同开关下顺序不同 | FE3C 服务、FE1C 写、FE1B 通知；Android 权限/系统蓝牙归手机；通知字节交 `PushBleRecvData`。`connectOperation` 是另一条云连接协调入口，不能代替 GATT | 蓝牙关闭、无权限、地址非法、特征缺失分别失败。`a.j:1711` 对 133/22/18 条件性延迟 1 秒重试，计数<3；不是所有断连无限重连 | 分开 `disconnected/connecting/gattReady/authenticated/ready`；旧连接回调不得污染新会话。J19 `Bluetooth/a:134,694,747,1473,1630–1720`。**主链闭合**；全部系统兼容分支和日版扫描名称未实测 |
| M02 设备鉴权与初始凭据 | `lj2.s:2565` 读 `x78.p→DeviceModel.deviceSecret`；`lj2.E:1524` 发 0x0008 请求随机值；`lj2.r:1189` 构造 token 后发 0x0133 | 请求含 corp_id/did/token/model/timestamp/sdk_ver；这里的 corp_id 是协议输入标识，不要求实现钉钉组织产品。原生 `AesEncrypt` 还把密钥装入流录制对象，认证调用具有本地副作用 | 密钥为空直接失败；原生生成 token 的存在不能证明新设备凭据可离线取得。首次签发、绑定变更/重置后凭据变化未闭合 | 区分已配对设备离线重连与全新设备首次授权；密钥来源、持久化、缺失状态必须明确。J19 `x78:313`、上述 `lj2`；N 0x2fbaa0/0x239718/0x2508f4/0x250d9c。**局部闭合**，凭据签发是完全独立首次使用的真实阻点 |
| M03 帧发送、重组和应答 | Java 分片队列→GATT 写；通知→native 长度重组→请求/响应分派→按消息 ID 观察者 | A1 消息 `type:u8, cmd:BE16, seq:u8, len:BE32, body`。请求应答与主动录音事件必须按类型/命令/序号/内容共同判断，seq=0 不是唯一推送条件 | `BleFrameSender` 队列>500清空；开关启用时等待写回调许可 5 秒超时后继续循环，旧分支无该超时；这是手机 GATT 流控，不是设备业务 ACK。音频 0x0117 有特殊应答分支 | 自有队列需显式报告溢出/失败；GATT 写成功、设备接受、文件完成分开。J19 `BleFrameSender:31–116`、`a:1657`；N `SendCmdToDevice 0x231ac8`/`ResponseDevice 0x233a28`，H。**局部闭合**，0x0117 所有 ACK 条件未全恢复 |
| M04 连接占用与状态恢复 | `I.h:5022` 的 connect/enableConnect/disableConnect→j78 云协调；BLE 状态另由管理器观察。`pt8` 连接后查能力/状态并驱动同步 | 云 appDeviceId/account 状态与本地 GATT 状态分开；独立客户端可自管会话所有权，但不能假定卡允许多个控制端同时写 | 断连清 GATT/MTU/特征引用；H5 保存断连前显示状态，显示 pause，重连再恢复显示。该 UI 恢复不是证明设备录音已经暂停/恢复 | 重连后重新查真实录音/fid/文件传输状态，再恢复任务；不按旧界面字符串盲发开始。J19 `a:1680`、`I.h`、`j78`；W 897650 附近。**主链闭合**；卡多控制端仲裁需实测 |

`I` 在全文代表 `com/alibaba/dingtalk/dingerimpl/DingerInterfaceImpl.java`；`P` 代表 `defpackage/pt8.java`。

### M02 原生认证算法新增结论

指令可确认：`AESUtil.aesEncrypt` 接收两个字符串，从第一个字符串复制前 16 字节作为 key 和 IV，第二个字符串作为输入，固定处理 32 字节；`dtiot_os_hal_aes` 使用 128 位 key、CBC 加密模式。结果逐字节格式化为 64 字符字符串；格式化大小写仍未在此报告断言。没有在该路径看到将 secret 先做十六进制解码或对随机值做常规 PKCS#7 填充的调用。输入长度校验应由独立实现明确承担，不能对异常短值照抄内存读取。

此结论限定于连接 token；不能把它直接应用到所有录音文件的解密。

## 3. 录音、按键、设置与标记

| 模块 / 用户功能 | 入口与状态流 | 输入输出与边界 | 失败与恢复 | 替代契约、证据与深度 |
| --- | --- | --- | --- | --- |
| M05 App 控制录音 | `I.c0:4577→P.q3:5104→lj2.P:1759` 发0x0100；设备主动事件也更新状态。pause/resume 与 hold/unhold 有独立处理 | did/action；运行中 fid、duration、audio_status；`DeviceSyncStatus.r` 把 recording/pause/resume 视为录音生命周期，syncing 独立 | BLE 未连/升级占用前置拒绝；录音请求接受不等于已收到流头；hold/unhold 还影响同步恢复 | 操作结果、设备状态、音频接收状态分开；未知 action 不穷举。J19 上述函数、P:1533、DeviceSyncStatus:273；N/H。**主链闭合**；各状态竞争需实机验收 |
| M06 物理按键与自定义动作入口 | 设置写云→q98缓存→卡 aikey_option；按键启动录音后，P.g3 按 source/process 与业务选项选择备忘/助手等 | `aikey_option=1000/1001` 是已知设备模式；云页面多个选项并非多个独立设备模式。`device/device_chat/device_voiceprint` 分流 | 云设置成功而 BLE 写失败可不一致；睡眠/传文件会影响可观测动作。左键没有找到独立重映射入口 | 可自定义收到音频后的处理；不能保证可捕获每次短按/双击，更不能据耳机 button_click 通用代码推定 A1。J19 I:3544、fallback.k2、P.g3:4423；H。**局部闭合**，任意按法重映射缺设备接口证据 |
| M07 参数与隐私设置 | `I` get/set→lj2 对应方法；q98 管云默认值；连接后能力门选择可用项 | mode/audio_source/audio_source_switch、aes/incognitomode/one_shot_incognito/force_sync_incognito/upload_stream、默认 remark/stream_record/ble_conn_param_auto。不同命令 params 可为对象或数组 | 云缓存与卡读回可不同；隐身录音、文件加密、是否转写是三件事；初始化可能覆盖设置，不能只验写应答 | 按字段保存期望值/实际值/来源，重连读回并核对；独立云处理开关本地保存。J19 I:3378–3544、lj2:x/Z/C/b0/c0/d0/e0/S/T、q98.f:220。**主链闭合**；枚举完整域与持久性仍受本机能力约束 |
| M08 录音标记与笔记 | `I.O:3967` add→`lj2.W:1909` 0x0102；remove→t88 云删除；记录上传时将标记时间关联文件 | 必须带 operationName/deviceId/fid/timestamp/type；type允许1或2；设备载荷 fid/ts/type。云笔记不是卡文件删除 | 缺字段、fid/timestamp非正、未知type拒绝。发送返回负数在某分支直接return，调用者可能无结束回调 | 自有笔记库记录绝对时间与相对音频位置、来源、删除状态；设备标记确认与本地保存分别完成。J19 I.O、lj2.W、t88、r78.createFile。**主链闭合**；标记类型完整语义和时间单位需结合文件头核对 |
| M09 声纹采集 | `I.B0:3092` start/stop→lj2.j0/k0；P.g3 对 device_voiceprint 的 oggPath/duration→sjw.e | 采集音频转换 WAV→上传得mediaId→voiceprint请求 audioDuration/audioMediaType=1/platform=A1；这是手机/服务侧后处理 | 前置 BLE/录音占用门；路径空、转换失败、上传失败均有分支，部分异常只记录日志 | 可将音频交自己的声纹/说话人模块；官方身份库不属目标，不能声称本地模型等同官方质量。J19 I.B0、P.g3、sjw:132–171。**主链闭合**，声纹事件在本机实际可达性未验 |

## 4. 音频数据、下载和完整性

| 模块 / 用户功能 | 入口与状态流 | 输入输出与边界 | 失败与恢复 | 替代契约、证据与深度 |
| --- | --- | --- | --- | --- |
| M10 实时流接收 | 0x0116 头→选择 StreamRecord/V2→0x0117 包→stop→补缺口/落盘/转换 | 头含 attrs/fid/fsync/stream_type/file_ver/aes/alg_mode/incognitomode/sid；stream_type=2抢占历史文件传输；同fid新头可更新参数 | 停止录音不等于音频收齐；旧包、重复头、格式版本决定不同分支 | 以流头建立会话；输出 encoded chunk、seq、format、fid及完整性标志；分别发 deviceStopped/dataComplete。N 0x22e340/0x22edc0、[原生流程报告](NATIVE_CLIENT_FLOW_2026-09-24.md)。**局部闭合**，组合帧/所有版本判定仍缺 |
| M11 缺包检测与补传 | DetectSeqGap→RecordGapStart/End→持久化 gaps→RequestGapFill→FillGap→继续下一缺口 | V2已有写入数据且当前seq>lastSeq+1时，缺口=current−(last+1)；请求0x0111携fid/s_off/b_size/gap_mode/gap | gaps列表达到60项进入合并/截断尾部为开放区间的处理；空/逆向区间丢弃。30秒活动超时回调file_sync_abort；不是整段录音限时30秒 | 必須追踪缺口与重传请求，写文件成功后再消缺；不把补静音算原音频恢复。N 0x30d784/0x30d848/0x30da68/0x239758/0x239b2c/0x30e844/0x232fa8。**局部闭合**，重试上限/所有回包关联规则仍缺 |
| M12 文件列表与 BLE 下载 | lj2.A/B/z→0x0110；按fid/范围分页→队列→SendFileSyncCmd→流写入→落盘事件→DB | s_fid/e_fid/recently；下载含fid及偏移/模式，文件索引与数据传输分开；V2位置是80+seq×frameSize | 列表请求成功不等于所有文件已下载；部分fid仍录制中；取消0x0112与尾块可能竞争；停止/断线保留未完成状态 | 每项有 queued/downloading/cancelled/incomplete/complete，队列只由一个拥有者推进；文件真实存在与可解码再交给后续模块。J19 lj2:1440/1466/2375/2703；N 0x232360/0x30c82c。**局部闭合**，独立完整落盘仍需样本回归 |
| M13 WiFi 快传 | 能力门→0x0120获取快传信息→手机连热点→HTTP下载→OpusConvertToOgg→DB→成功；0x0121关闭 | URL追加14位补零fid；HTTP文件输入转换器；WiFi连通、HTTP完成、转换完成三个阶段 | 下载器在特定开关下只对408/503最多重试5次，延迟1…5秒；转换非0失败；网络切换与取消需释放所有权 | BLE/WiFi不能并发写同一文件；自建下载器可独立于官方云工作，必须保留转换和完整性阶段。J19 WifiTransferDialog:509、DingerDownloader:131等、lj2.I/q。**主链闭合**；热点权限和断点恢复需本机验证 |
| M14 加密、容器与音频标准化 | 设备流→原生自有文件→Opus/Ogg转换；播放/导出用secret打开；部分场景缺钥查file_encrypt_secret | 至少要区分传输帧、自有80字节头文件、Ogg页、解码PCM。SDK落盘某分支只加密每帧去掉前缀后的首16字节，余部复制 | V2密钥截取/零补至16字节；AES错误时当前SeekWrite分支存在复制原数据继续写的退路；不能盲用文件后缀判定已解密 | 自有处理入口需要明确 codec/container/rate/channels/encryption/completeness；标准化完成前禁止作为完整转写输入。N 0x30ebf8/0x30d04c/0x30c82c；J19 P.O1、cq8.L。**局部闭合**，全部文件版本/解密校验规则未全恢复 |

### 音频原生细节：本轮从指令确认的部分

1. **补写位置和落盘结果**：`SeekWrite` 和 `FillGap` 都 `fseek(80+seq*frameSize)`；fseek失败、fwrite长度不符返回−1。SeekWrite成功更新最后序号并持久化；FillGap本身只负责指定位置写入，不能把其返回0等同全部缺口完成。
2. **缺口边界**：RecordGapEnd在end<start或end==start时移除最后区间；合法结束写入end。RequestGapFill使用 `(end-start)*frameSize`，与半开区间一致；end=0是开放尾区间的特殊请求。
3. **全量重传标志**：V2 Stop 在仍有缺口且统计总帧数≥100时比较 dropped/total 与float32 0.05；严格大于阈值置 NeedsFullRetransmit 标志。RecordDroppedFrames同时增加total和dropped，RecordReceivedFrames增加total和received。**置标志本身不是已经执行全量重传**，调用方决定后续动作。
4. **结束条件**：Stop在有gaps时持久化缺口，没gaps时走删除gaps文件及ConvertOpusToOggWrap；因此收到stop事件后直接重命名“完成”会丢失官方完整性语义。
5. **帧魔数**：ValidateMagic在帧前缀长度为4时要求输入至少4字节，并比较第一个小端32位字右移22等于0x2a5；其他前缀长度分支直接返回真并记录日志。这是某版帧判定，不是所有Opus都带该魔数。
6. **V2局部加密**：SetAesKey截取前16字节，短值补0；EncryptData按16字节向上补0，CBC key/IV同源；SeekWrite只在加密标志、密钥、帧整除等条件成立时，对每帧有效载荷首16字节调用它，其余数据复制。不能据此推定卡上所有文件也以相同方式存储。
7. **组合帧序号与重复数据**：ParseRequestStreamPacket在0x22ffdc起，根据数据长度/frameSize求包内帧数，商为0或frameSize<1时用1；从包内序号减去该数（下溢归0）得到firstSeq。lastSeq非0且firstSeq≤lastSeq时走重复/旧包计数分支，跳过该处正常顺序写入流程。此结论限于所读V2支路，不可直接套用所有流版本。
8. **开头缺失的特殊策略**：lastSeq=0、firstSeq非0、没有开放或待补缺口时，0x2303b0检查firstSeq：≤10调用FillSilenceFrames(0,firstSeq)，>10登记[0,firstSeq)缺口并保存。这是开头缺失策略，不能概括成“任何少于10帧的缺包都补静音”；补静音也不等于无损恢复。
9. **写入失败与统计**：0x23034c调用SeekWrite后，此调用点未检查其返回值便继续RecordReceivedFrames。因此统计收到帧数不能单独证明文件写入成功；独立实现应明确传播磁盘写入失败。
10. **0x0117条件标志进一步定位**：ParseRequest在0x22c220读取并清除对象偏移0x4e1的标志，对0x0117有条件跳过异步支路；本轮在有符号的DingerProtocolAna函数中找到ParseRequestFileBlock的0x22d904写入该标志。尚未闭合该写入的全部条件和异步回调行为，不能将此局部结果当成完整ACK规则。

上述指令在忽略目录 `apks/8.5.8.3/work/module_native_audit.txt`，生成器同目录 `module_native_audit.py`。通用调用使用ELF重定位表解析名称；没有依赖自动猜测字符串注释。

## 5. 文件操作与本地状态

| 模块 / 用户功能 | 入口与状态流 | 输入输出与边界 | 失败与恢复 | 替代契约、证据与深度 |
| --- | --- | --- | --- | --- |
| M15 本地库、列表、备忘 | hr8/DBManager以设备录音、云记录和处理结果关联；列表可合并卡/本地/云；DB更新推动界面 | deviceId/fid与fileId/spaceId/dentryUuid/minutesId不是同一ID；路径、时长、回收状态、加密/裁剪/合并、纪要状态分别保存 | 路径空、DB无记录、文件已上传但本地缺失均有不同补救；只清缓存不能删云记录/卡原件 | 独立recordingId关联(deviceId,fid)，音频、文本、任务、笔记各自状态；重启可回查和续接。J19 hr8:1170/1288/1419、DingerEntryObject、r78。**主链闭合** |
| M16 删除、回收、恢复、分组 | `I.s:5755→P.E1`按state分支；fileId分云/本地；部分开关允许卡0x0113；r78负责文件分组 | state1删除、3回收、0恢复为所读业务分支；卡fid、本地路径、云fileId操作对象不同 | 部分成功需保留各层结果；卡删除没有证明可恢复；云回收成功不代表卡被擦除 | 删除作用域必须明确；自有回收站可恢复索引/自有副本，不能承诺恢复已删卡数据。J19 I.s、P.C1/E1、fs8、r78。**主链闭合**；破坏性行为本轮未验 |
| M17 播放、拖动、倍速 | `I.b→cq8.L→openAudioFile→AudioTrack`；pause/resume/seek/stop分别处理；进度回调 | AudioFileAttr提供sampleRate/channels/depth/duration；seek输入秒×1000，再除总时长并将>=1截到0.999；倍速枚举0.5/1/1.25/1.5/2/3 | 密钥缓存缺失时云补取最多等待5秒；打开失败或AudioTrack未初始化返回失败；倍速灰度关闭/不支持拒绝 | 用自己的解码/播放器消费标准音频；保存位置、播放与录音状态分离。J19 cq8:370/404/517/540/686。**主链闭合**，底层各编码覆盖取决于M14 |
| M18 导出与合并 | `P.O1/S1`构造AudioFileParam→gs8.d；合并P.P1/P2→gs8.f→新增本地记录 | path/secretMd5/isEncrypted/duration及目标格式；输出新路径、进度、错误码；合并输入数组而非拼接压缩字节 | 两条路径会先callback.onSuccess(null)再执行native，只有成功码且路径非空才完成；错误时发convert/merge_info_update；异常部分仅日志 | 独立契约区分accepted/progress/completed/failed；保留原文件，完整新文件才登记。J19 P:3437/3480/3509、gs8:170/229/255。**主链闭合**，全部导出格式枚举/编码细节仍局部未知 |
| M19 手动裁剪/智能去空白 | ClipActivity→DingerAudioHandler→native处理；Normal/Disabled/AiClipping/AiClipEnd；保存可另存新记录 | AudioClipParam包含文件与时间范围；结果路径/时长/大小，智能裁剪还返空白区间列表；最后文件存在且SUCCESS才接受 | 取消调用CancelSmartClip；失败回Normal。时间校正有100单位量化；反编译出现未定义r7，不能直接照搬该表达式 | 自有实现可用解码PCM/标准工具裁剪，智能去空白用本地算法；不要求复刻官方模型，但需解释裁剪区间并可取消。J19 ClipActivity:199/245/712/1008/1037。**局部闭合**；精确官方自动裁剪算法未恢复，不阻止等价可配置功能 |

## 6. 转写、翻译、总结：可替代的处理契约

| 模块 / 用户功能 | 入口与状态流 | 输入输出与边界 | 失败与恢复 | 替代契约、证据与深度 |
| --- | --- | --- | --- | --- |
| M20 实时转写音频管道 | `I.b0:4468` start/stop切upload_stream；set解析needAsr→P.R3/Y3；ugu取动态WSS→native StartAsr；event0送H5或xgw | ga8 attributes明确Format=opus/SampleRate=16000/SpeakerCount=1/Protocol=5；原生OpusAssemble组Ogg header/page，以WS binary发送。设备采集与云转写可分开启停 | URL空报错，但部分service/param空分支只return；参数字符串作为URL缓存键。TaskFailed参与native重连；PauseAsr随录音pause/resume | 自有ASR入口接有格式声明的音频，支持start/chunk/pause/end/cancel/error；显式会话ID和完整性。J19 I.b0、P:3676/3947、ga8/ugu；N 0x3144c4/0x315848/0x29f97c。**主链闭合**；全部WS终止/续接时序未还原，不需复用官方协议 |
| M21 转写结果消费 | P event0→xgw或H5；native弹窗按SentenceBegin清临时文本，Changed替换，End把缓存入列表；H5按SentenceEnd决定partial=false | 外层type/payload，payload.name、payload.sentence.text；H5还消费sentenceId/sentenceUuid/partial。不是每条文字都追加新段落 | JSON解析失败丢弃；native缓存最终句依赖之前Changed，说明不能盲抄为通用ASR规范；H5批量更新保留句标识 | 自有统一事件：session/segmentId/text/isFinal，可选start/end/speaker；最终句覆盖同段临时句，幂等去重。J19 xgw:108、VoiceMsgPopDialogV2；W 896380附近。**主链闭合**（W版本有界） |
| M22 实时翻译/面对面翻译 | H5按模式ASR/FACE2FACE_TRANSLATION/LIVE_TRANSLATION分派；按源/目标语言送左右列表，逐句替换/聚合 | `type=TRANSLATE_RESULT`：payload.targetLang、sentence；`ASR_RESULT`：sourceLang、sentence；sentence含sentenceUuid/text/partial/currentTime，sentenceId也被读取 | 空句/空uuid不更新；重复同version/text/partial跳过。面对面模式所读代码仅接受sourceLang=cn的ASR支路，这是此版本的限制，不能泛化成设备限制 | 自有翻译保留稳定句ID和源/目标语言，临时结果可修订；语言支持由自有模型决定。W 893500–897650（Sa/Ra/订阅）；J19 ga8.d。**主链闭合**，不需阿里服务权限 |
| M23 历史转写与总结/纪要 | I.t解析fid/fids、模板/模型/语言/说话人设置→n4j查库：已有URL返回；已有存储关联直接建任务；缺fileId先登记；本地缺文件可下载；随后上传/任务 | 返回deviceId/fid/mobileMinutesUrl/async，DB保存minutesId/状态；批量results/totalCount/successCount/failCount。**原生此路径交付的是纪要入口和任务信息，不是完整纪要正文** | 文件缺失1202；上传失败向上转发；任务async不代表正文完成；部分无记录分支传null给错误处理后只return，存在未结束回调 | 自有流水线：完整音频→ASR分段→翻译（可选）→总结（模板/模型可选）→本地文档；各阶段独立可重试。J19 I.t:5878、n4j:349/593/601/623/700/738、ga8.a。**业务主链闭合，官方远端正文仅边界明确**；不阻止自有总结 |
| M24 自动处理与偏好 | q98把default_source_language/default_llm/default_minutes_template/default_speaker_diarization映射为任务attributes；录音/文件完成触发后续 | 设置与音频传输不同步；自动纪要必须等音频/记录达到所需阶段。模板可含JSON并从中取ID | 模板解析失败记录日志；云缓存可滞后；隐身是否允许转写是独立设置 | 自有偏好库+每次任务参数快照；模型/语言/模板可覆盖，隐私关闭应阻止自动上传。J19 q98.f:220、s98、n4j.m。**主链闭合**；完整自动触发去重需与M10/M15联合验证 |

### 翻译页面状态细节

H5 `Sa` 用sentenceUuid定位旧项，更新临时/最终文本；`Ra` 用origin/translate两个map和currentVersion聚合段落。已确认的断段条件包含：非partial，当前侧全部完成或map数量>7，且累计文字长度≥50或所用currentTime差>10000；两侧ready集合都含当前句时提交双侧最终段并清map。列表超过100条会裁掉前25条。这里的currentTime单位仅由比较常量不能独立证明。

这些是官方显示策略；自有客户端应保存完整文本，不能把页面裁掉的条目当作可删除的录音资料。只要统一适配后的句ID、修订、最终状态和时间关联正确，就无需复制其所有显示阈值。

### 最小自有处理接口（设计结论，不冒充官方协议）

```text
RecordingRef: recordingId, deviceId, fid, source, container, codec,
              sampleRate, channels, durationMs, completeness, localPath
StreamEvent: sessionId, seq, audioChunk | paused | ended | failed
TextSegment: sessionId, segmentId, revision, text, isFinal,
             startMs?, endMs?, speakerId?, sourceLanguage
Translation: segmentId, revision, targetLanguage, text, isFinal
SummaryJob: recordingId, transcriptVersion, template, model,
            queued | running | completed | failed | cancelled,
            document?, error?, retryable
```

这些字段足以让设备层、音频层、ASR、翻译和总结分别替换。需要的能力是输入标准音频、接收结构化文本、追踪完成/失败和保存结果；不需要阿里网关、订阅校验或官方纪要网页。

## 7. 定时、存储与自定义动作

| 模块 / 用户功能 | 入口与状态流 | 输入输出与边界 | 失败与恢复 | 替代契约、证据与深度 |
| --- | --- | --- | --- | --- |
| M25 计划录音 | P.s1能力门→hsp查询→过滤/排序→lj2.g0下发0x011A | did/action=set/current/params[{sid,start,end}]，设备侧秒；官方来源是毫秒云任务；空结果仍发空计划 | 首次失败后最多3次追加重试，间隔5秒；检查网络/BLE/非OTA/非解绑；并发检查合并为一次续查 | 自建计划库可替代云来源。手机到时发命令和卡内离线执行必须分开；本机历史cap=1低于官方门槛2，卡内离线能力尚未证实。J19 hsp:44/74/144/164、lj2.g0。**客户端主链闭合，设备支持未定** |
| M26 自有存储与任务上传 | 官方ecv队列→ga8.f创建上传任务→云盘上传→r78关联→本地更新→纪要 | taskId/spaceId只属官方服务；文件md5、时长、创建时间、备注/隐身等随元数据关联；二进制与业务记录分阶段 | 空mediaID失败；对象上传成功后关联失败仍需修复；DOA附件失败部分分支不阻断主音频。服务器可选分片大小，256KiB只是请求建议 | 自有对象存储/本地库均可；幂等上传、校验、关联和重试分别有状态。J19 ecv/zz4/p73:218/602、r78:231/288。**主链闭合**；不需要复刻钉盘协议 |
| M27 备忘与自定义动作 | P.g3 source/process判断→流start/stop→保存音频/文本→助手或备忘入口；voice模式不改变后续服务必须是谁 | action可消费音频路径、fid、文字、时间、选择模式；相关A1助手/scene API是官方实现之一，不是硬件要求 | 不完整音频、最终文本未到、服务失败会产生不同终止条件；按键事件不应重复创建同一任务 | 定义 trigger/condition/action，以recordingId+trigger做幂等；动作可本地保存、送自有API、生成文档。J19 P.g3:4423、xgw:177及后续、DingerAiAssistantI/DeviceAiSceneI。**主路由闭合**，官方复杂助手内部行为不属替代前提 |
| M28 诊断、能力与版本隔离 | 0x000C诊断解析；能力0x0133、状态0x0132、默认参数0x0137；ps8控制App灰度 | 诊断记录有时间/模块/完整事件ID/值；SYSTEM_UPTIME不是按键事件。设备cap、App开关、云权益应分别标记 | 格式长度/记录数非法应拒绝；同名称不同版本不能混用；当前独立App内库仍是较旧8.3.48.3样本 | 保留版本化解析器及未知字段，不把通用耳机/4G分支当A1功能；错误可诊断而不输出密钥/录音。J/N/H，[原生流程报告](NATIVE_CLIENT_FLOW_2026-09-24.md)。**主链闭合**；日本版枚举和可达性需实机 |

## 8. 仍不能确定的点：具体原因及影响

| 未确定项 | 当前限制，而非下一轮路线图 | 是否阻碍自主功能 |
| --- | --- | --- |
| 全新设备凭据如何签发、重置后密钥如何变 | 已追到DeviceModel来源和设备挑战链，尚未闭合发起绑定的全部跨DEX/远端页面及实际服务响应；目前没有独立首次激活证据 | **阻碍“任何新卡都完全脱离官方初始化”**；不等于已绑定卡每次使用都要付费 |
| 所有音频版本、0x0117特殊ACK、跨包/缺口关联 | 原生状态机的关键函数已读，但全部调用路径及版本组合未穷尽；Java反编译无法展示这些叶子逻辑 | **阻碍无官方SDK的完整协议实现保证**。调用官方SDK可利用其处理，但不能因此宣称已理解或独立替换算法 |
| 缺包策略的全部阈值/重传终止 | 本轮已恢复60区间门槛、100帧/5%全重传标志、开头≤10帧补静音、补写偏移和缺口结束；跨版本的全部选择条件及重传上限仍未完整闭合 | **阻碍所有异常流都无损恢复的保证**；不是阻止实现正常录音 |
| 所有加密容器校验/密钥更新 | 已确认认证与V2局部加密算法；DecryptOggFile等全部格式分支还未逐条验证 | **阻碍全部加密历史文件都能独立解码的保证** |
| 任意新增按键模式（左键已排除） | 用户已确认左键不支持自定义并移出目标；右键1000/1001参数和主要行为已有证据。没有任意新增手势接口的证据 | **不再将左键映射作为目标缺口**；按已知右键模式取得音频后自定义处理可继续 |
| 卡内计划持久化、并发连接、日版能力 | 固件侧执行规则和本机能力不能只从App门槛推导，缺相应实测 | **阻碍离线自主定时及全部模式保证**；手机定时可另实现但条件不同 |
| 官方完整纪要网页正文/所有AI算法 | 本地客户端主要接URL/异步任务；远端内容未包含在已保存材料。智能裁剪原生算法也未完全恢复 | **不阻碍自有ASR/翻译/总结/智能裁剪**；阻碍像素和算法结果逐项完全一致，这不是自定义目标 |
| H5页面与日版当前分发版本是否一致 | 已保存资源标识0.181.1，缺当前页面版本对应证据 | **不阻碍采用已恢复的数据语义**；阻碍声称该页面就是当前日版实际运行的所有分支 |
| Java反编译有损 | classes28有1、classes29有36个反编译错误；n4j批量成功、裁剪校正等局部存在fallback/未定义变量 | 自有模块可按输入输出重写；对这几个官方分支的精确行为须保留“未知”，不得复制错误伪源码 |

## 9. 审计结论

设备及配套功能现在已按 **28 个模块**展开到入口、状态、数据和失败处理，并识别出真实的设备依赖与可替换服务边界。28是报告结构，**不是28项已实机通过**。

可以据此独立设计录音控制、状态库、文件管理、播放/导出、转写/翻译/总结及动作系统；其中云付费服务不是必要依赖。剩余重点是无root新用户的凭据取得途径、全部音频格式/完整性和卡内离线执行能力。已绑定本卡的离线鉴权和已测右键模式不再作为未知项；左键映射已排除。其余官方生态不应继续占据研究资源。

本次没有安装软件、写卡设置、录音、解绑、改业务代码或触发云任务。新增的是静态证据和研究文档。当前不能宣称全部底层细节掌握，也不能用“静态审计覆盖”代替“独立客户端在本卡跑通”。

## 10. 入口覆盖与复查材料

[证据文件索引](A1_MODULE_EVIDENCE_INDEX_2026-09-25.json)保存本轮29个本地材料的路径、大小与SHA-256，以及18个导出原生函数的地址和长度。索引将H5快照中找到的25种`internal.dinger.*`桥接名称逐一映射到上述模块；这是检查入口归属的方法，不代表25个入口下的所有分支都已恢复。

容易混淆的入口另作说明：`sendBleCommand`是原始命令桥接，不证明设备接受任意命令；`grayConfig`和`hasDolbyDecoder`涉及客户端开关/解码能力，不是新的卡指令；`pageOperation`涉及页面生命周期。`unbind`已归入凭据/连接模块，但解绑后的服务与设备凭据生命周期未闭合，也没有执行解绑。它不能因为名称已入索引就算作已验证功能。

检查结果：28个模块编号唯一；25种快照桥接名称全部有归属；索引29个材料均实际存在并计算了哈希。上述检查验证报告可追溯性，不验证设备功能。
