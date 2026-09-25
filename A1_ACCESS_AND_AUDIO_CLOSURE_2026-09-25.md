# A1：无 root 接入与音频收尾证据

日期：2026-09-25。继续静态分析官方 Android 8.5.8.3 与回放已有抓包；本轮没有连接设备、安装 App、登录账号、下载私人数据或修改卡片。左键自定义不在开发范围内；右键1000/1001沿用已取得的参数与历史实测。

## 1. 普通用户能否自动取得密钥

### 已确定的调用链

1. `defpackage/o98.java:136–146` 调用 `DeviceMonitorIService.queryUserBindDevices`，请求包含随机requestId。
2. `DingerInterfaceImpl.java:2265–2317` 接收 `QueryUserBindDevicesResultModel.deviceModel`，交给 `x78.N`。
3. `x78.java:161–168` 将完整DeviceModel列表序列化进 `zv8.a` 缓存；`x78.p:316–320` 从模型读取deviceSecret用于连接鉴权。历史root提取正是取得此缓存里的凭据。
4. `DeviceIService.java:54` 另声明 `getDeviceSecret(Integer, Long, RequestHandler<String>)`。这是官方会话中的内部RPC声明；仅凭签名不能确认两个入参完整业务语义，也不能确认公开OAuth可调用。
5. `DingerInterfaceImpl.f1:4871–4912` 返回给H5的是经过转换的DeviceInfoH5，**不是原始DeviceModel**。`DeviceInfoH5.java`的字段和fromDeviceModel赋值均没有deviceSecret。因此已研究的`internal.dinger.getDeviceList`桥接不能直接作为密钥导出接口。

上述源码均位于 `apks/8.5.8.3/work/src/sources`，接口声明位于 `work/cloud28/sources/com/dingtalk/device/client`。没有在报告保存任何真实凭据。

### 接入方式当前结论

| 方式 | 证据与结论 |
| --- | --- |
| 已有deviceSecret，导入独立App | 已有历史成功鉴权；运行时不要求root。取得密钥与使用密钥是两件事 |
| root手机自动提取官方缓存 | 历史已验证可提取；可自动化，但不能作为无root用户的复现答案 |
| 普通App读取官方App私有缓存 | 不能依靠普通蓝牙或存储权限完成；Android应用沙箱隔离私有数据 |
| 系统蓝牙配对/HCI抓包 | 已确认挑战值与计算后的token；未发现该鉴权交换直接发送deviceSecret，不能从“看到了token”推出“拿到了secret” |
| 官方H5设备列表桥接 | 此版本已确认不返回deviceSecret |
| 用户授权的官方账号接口/导出 | 内部密钥和设备列表RPC存在；但尚未找到并验证可供普通第三方App使用的授权、导出和调用闭环。它是无root接入的具体未完成项 |
| 用户主动导出的诊断日志 | 源码有记录完整模型/缓存的日志调用，可作进一步调查线索；尚未证明发行版实际输出、普通用户可导出且包含密钥，不能当作现成方案 |

平台依据：[Android应用沙箱](https://source.android.com/docs/security/app-sandbox)；[Android 12的ADB备份限制](https://developer.android.com/about/versions/12/behavior-changes-12)。ADB备份不应被写成适用于所有现售手机的密钥导出教程。

**开源复现边界：目前能开源协议、导入流程与验证工具；不能宣称普通无root用户已经可以一键提取密钥。** 新用户接入仍需要一个已验证的凭据取得途径。公开仓库不应携带某个用户的密钥，也不能用共享密钥代替每台卡自己的凭据。官方原包与提取的.so也不是独立源码实现的证明；研究材料、自己写的代码和依赖应分别说明。

## 2. 组合音频帧：本次已用旧抓包验证

离线重放 `capture/official_mode1001_stop.log`，使用已有ATT/A1重组器，再用新脚本 [audio_stream_metadata.py](tools/audio_stream_metadata.py) 只统计结构，不输出deviceId、fid、密钥或音频内容。

```powershell
python tools/audio_stream_metadata.py capture/official_mode1001_stop.log
```

匹配到的流为file_ver=v1.7、stream_type=3，attrs声明frameBytes=84：

| 单条消息中声明的数据字节数 | 消息数 | 对应84字节帧数 |
| --- | ---: | ---: |
| 84 | 4257 | 1 |
| 168 | 5 | 2 |
| 252 | 1 | 3 |
| 336 | 1 | 4 |
| 504 | 1 | 6 |

共4265条音频消息、4280个按该长度划分的帧；8条为组合消息。4264次相邻序号比较全部满足：

脱敏统计及原抓包SHA-256见 [回放结果](A1_AUDIO_METADATA_REPLAY_2026-09-25.json)。额外使用合成的单帧→双帧连续序号和真实跳号两种输入，确认脚本能够区分正常组合包与缺口；这些检查不替代实际音频解码验收。

```text
当前消息的序号 - 上一消息的序号 = 当前消息字节数 / 84
```

这一已匹配流内未发现序号缺口，声明长度越界和非整帧长度均为0。抓包整体有37个孤立续片（当前工具统计），因此不能据此证明整个抓包从头完整，也不能把序号连续等同每帧可解码或整段录音完整。

### 对当前独立代码的直接影响

`a1app/.../device/A1Protocol.kt:369–376` 将整段消息体提取为一个AudioChunk；`A1StreamCapture.kt:41–49`按消息序号+1计算缺口，并将长度不等于单帧长度标记为不确定。这条代码路径对上面8条组合消息会产生不完整判断，且序号跳增会被计入missingPackets。

因此，“组合包被误判为丢包”已有**官方指令、真实历史样本、当前代码**三层对应证据。是否走到该Kotlin路径仍取决于运行时native/Kotlin分工，不能据此断言所有用户录音都受影响。

### 可复现规则与限制

- 原生 `ParseRequestStreamPacket 0x22ffdc–0x230004` 按数据长度/frameSize计算帧数，从消息序号减去帧数得到firstSeq，下溢归0。这与样本中的序号步进一致。
- 该样本应按84字节划分多帧后分别处理；不能把252/336/504字节的多帧拼块直接当成单个Opus包。
- 不可对所有版本硬编码84；应来自该会话有效头部。长度不整除、无头部和版本不识别应明确报不支持/不完整。
- 本样本4280个边界均**不匹配**原生某分支的4字节魔数判定。因此不能把“每帧必有4字节前缀”或“所有帧必须匹配0x2a5魔数”写成通用规则；前缀长度必须跟随实际格式分支。尚未在本轮验证解码结果。

## 3. 缺口补传：本次新闭合的调用顺序

对象偏移只用于同一哈希的8.5.8.3原生库，不是跨版本ABI。指令输出在忽略目录 `work/audio_closure_disassembly.txt`。

1. `RequestGapFill 0x239758` 取得frameSize，优先V2对象值；为0时回退协议对象的正值，再回退80。`s_off=80+start*frameSize`；有限区间请求的字节数按半开缺口 `[start,end)` 计算，end=0表示开放尾部。
2. `ParseRequestFileBlock 0x22d658–0x22d6b0` 在gap模式下按“当前偏移减请求起始偏移”与请求长度判断这一段收完；开放尾部则与已知文件末端比较。普通下载另按文件大小比较。
3. `0x22d7bc–0x22d840` flush/close当前文件，更新已补字节统计并清本段状态。
4. `0x22d844–0x22d8c0` 移除缺口列表首项。还有缺口时SaveGaps，并在`0x22d904`设置对象偏移0x4e1的“稍后继续补传”标志。
5. 普通请求的异步回调位于`0x23bc84`：`0x23bcf4`先调用ResponseDevice，`0x23bd2c`再按该标志调用ProcessPendingGaps。由ParseRequest构造闭包时的vtable地址0x6d7f78，经ELF重定位表+0x28定位到该函数。
6. 0x0117在ParseRequest里跳过通用响应支路；若有待处理标志，则走另一个异步回调`0x23c028→0x23c06c→ProcessPendingGaps`，日志明确为fallback。不能给每条0x0117无条件套用普通消息ACK。
7. `ProcessPendingGaps 0x239b2c` 选择剩余首个缺口发下一次RequestGapFill。缺口列表空时清理记录；FileBlock完成路径`0x22dda0–0x22ddf0`执行ClearGaps并调用ConvertOpusToOggWrap。

这里确认的是**先调用响应发送函数，再启动下一段补传**；没有证明必须等待底层GATT写完成回调后才发下一次请求。应答发送、下一次请求、最终转换不能颠倒成收到stop即文件成功。

此前报告“0x4e1写入条件及异步回调未闭合”已由以上证据补齐。仍需保留的限制是跨版本布局、磁盘失败传播、全部超时/重试出口、完整文件解密及可播放性。当前没有修改App业务代码，不能将研究闭合写成自动修复已上线。

## 4. 本次结论

- 左键任意映射从验收范围删除；右键1000/1001保留已验证结论。
- 无root接入的实际缺口是**普通用户可授权使用的密钥取得途径**，不是AES算法未知。
- 组合包的正常序号规则已由真实数据验证；原先泛称“音频可靠性未知”过于笼统。
- 缺口移除、持久化、应答后继续下一段及最终转换的主要链路已经从官方底层补齐。
- 剩余协议问题需继续以具体输入/输出和回放证据解决；现有研究不要求重新测已知按键动作。
