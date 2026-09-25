# A1 官方后台模块：提取结果与接入边界

日期：2026-09-25。研究范围为设备后台、音频函数及绑定机制，不迁移官方前端；不以重写或完全理解底层算法为目标。

发布补充：指定核心提取件现收录于 [vendor/dinger-sdk/8.5.8.3](vendor/dinger-sdk/8.5.8.3/)，接入见 [开发指南](docs/SDK_INTEGRATION.md)，权利说明见 [NOTICE](NOTICE.md)。下文“本地路径”保留研究时的定位信息；其中“尚未发布”的表述仅描述提取时状态，不代表本次发布状态。

## 1. 已实际提取的本地模块包

目录：`<workspace>/dingtalk-a1\apks\8.5.8.3\backend_bundle`。

来源均为已有官方8.5.8.3 APK：

- `split_demand1.apk!/lib/arm64-v8a/libDingerSdk.so`
- `base.apk!/lib/arm64-v8a/libc++_shared.so`
- `base.apk!/classes27.dex`中的`com.android.dingersdk.nativeInterface`，经JADX 1.5.2提取15个顶层Java文件。

共2个原生库、15个Java文件；另生成9个核心Java文件的`dinger-jni-core.jar`、文件哈希清单和接口清单。没有打包H5、Activity、Fragment、布局或界面资源。

提取时文件来源和SHA-256见 [文件清单](A1_BACKEND_BUNDLE_MANIFEST_2026-09-25.json)，42个原生入口的声明见 [接口清单](A1_BACKEND_INTERFACE_INDEX_2026-09-25.json)。本地提取件尚未替换当前App，也未作为公开二进制发布。

## 2. 哪个文件是什么模块

以下Java文件均位于包内`java/com/android/dingersdk/nativeInterface/`。

| 文件 | 实际职责 | 接入时需要什么 / 能得到什么 |
| --- | --- | --- |
| `jniLibs/arm64-v8a/libDingerSdk.so` | 设备协议、认证计算、流/文件接收、音频容器/解码/转换等核心原生实现；同一库也含不启用的OTA和官方ASR通道 | 宿主提供BLE字节、目录、配置、密钥和回调；输出待发送字节、事件、音频数据、文件结果。算法内部优先直接复用 |
| `jniLibs/arm64-v8a/libc++_shared.so` | C++运行库依赖 | 与所选SDK配套；不是设备业务模块 |
| `DingerAudioTools.java` | JNI总入口和native→Java回调转发器 | 42个native方法；`System.loadLibrary("DingerSdk")`；注册/注销回调 |
| `RecvMsgCallback.java` | 宿主必须提供的6种回调 | `OnSendData`待发送BLE字节；`MsgCallback`请求结果；`EventCallback`事件；`StreamDataCallback`带标签字节；`GraySwitchCallback`开关查询；`LogCallback`诊断 |
| `AudioFileParam.java` | 文件处理输入结构 | `audioFilePath/secretMd5/isEncrypted/duration`。字段名称保持原样，不能凭名字自行改变密钥表达 |
| `AudioFileAttr.java` | 打开音频后的属性输出 | channels、containerSampleRate、inputSampleRate、depthBit、duration、fileSize、isEncrypted |
| `AudioFrameBuffer.java` | 文件解码读帧缓冲区 | buffer、bufferLen、dataLen；配合readAudioFrames |
| `AudioClipParam.java` | 裁剪输入 | AudioFileParam与startTime/endTime；时间单位沿调用契约确认，不根据字段名猜 |
| `ExportProgressCallback.java` | 导出进度 | 进度和附加文本；返回进度不等于最终文件成功 |
| `MergeProgressCallback.java` | 合并进度 | 同上；合并结果另由输出参数和返回码取得 |
| `CalledByNative.java` | 标记由JNI调用的Java成员 | 保持类、方法和字段可被native找到 |
| `DingerCommandHelper.java` | 常用命令JSON构造与发送封装 | 录音、随机值、连接、文件、热点、状态等；依赖Android Log/JSON。不是账号绑定或密钥签发器 |
| `DingerBleRequest.java` | BLE请求数据结构 | msgId、reqCmd、reqData、reqLen；源码另引用AndroidX NonNull |
| `DingerEvent.java`、`DtIotEvent.java` | 事件常量/枚举 | 给回调事件命名；不要把所有通用设备事件都视为本卡支持 |
| `DtiotAudioMode.java`、`dtiot_ble_request.java` | 音频模式、命令和控制键常量 | 降低宿主硬编码量；常量存在不代表本卡支持全部取值 |

## 3. 可调用的后台功能组

| 功能组 | 入口 | 从哪里取得结果 |
| --- | --- | --- |
| 初始化 | GetSdkVer、InitConfig、setGraySwitches、RegistMsgCallback | 返回值和后续回调；目录需预先存在 |
| 蓝牙协议通道 | PushBleRecvData、SendCmdToDevice | OnSendData、MsgCallback、EventCallback |
| 文件同步 | SendFileSyncCmd | 由SDK建立内部接收上下文；落盘结果/事件，不能只发同名JSON来替代 |
| 鉴权计算 | AESEncrypt、AESDecrypt；DingerCommandHelper连接命令 | 计算结果与设备应答；仍需要外部提供deviceSecret |
| 容器转换 | OpusConvertToOgg、GetOpusFileSize | 返回码、生成文件及文件属性 |
| 解码/播放数据 | openAudioFile、readAudioFrames、seekToPosition、seekToSecond、AudioFileClose | AudioFileAttr和AudioFrameBuffer；播放设备/AudioTrack由宿主管理 |
| 导出、合并、裁剪 | ExportAudioWithProgress、MergeFilesWithProgress、AudioClipWithProgress、SmartClipWithProgress及Cancel接口 | 输出路径、返回码、进度/完成回调；内部算法直接复用 |
| 单帧解码与音频通道 | decodeOpusFrame、resetOpusDecoder、openDownlinkStream等 | 字节/流句柄；新增接口仅说明SDK具备入口，不宣称本卡所有通道已验收 |

StartAsr/StopAsr/PauseAsr属于SDK内置的转写传输通道，不是离线转写模型。用户需要的自有ASR、翻译和总结应接收输出后独立运行。OTA入口保留在原始声明中，但不接入产品功能、不调用。

**音频回调不能仅凭名字当作PCM**：StreamDataCallback只有byte[]、长度、tag，必须按已验证的模式/标签解释。宿主对SDK只承担调用契约，不需要重写内部音频算法。

## 4. 哪些官方后台类不应整包拖进来

| 已定位的源文件 | 职责 | 处理方式 |
| --- | --- | --- |
| classes19的`Bluetooth/a.java`、`BleFrameSender.java` | Android GATT、MTU、写队列、重连 | 使用现有A1Client提供同等传输接口，不引入官方账号/UI依赖 |
| `lj2.java` | JSON命令、异步请求等待、鉴权衔接 | 保留必要命令和接口契约；核心收发交SDK |
| `pt8.java` | 初始化、录音与文件流程编排、事件分派 | 混合大量官方服务/UI/数据库依赖，不是可独立直接编译的音频模块；取必要后台调用次序，宿主提供服务接口 |
| `hsp.java` | 计划获取、能力门、下发与重试 | 可用自有计划源，保留与SDK/卡交互契约 |
| `cq8.java`、`gs8.java` | 播放、转换、合并的上层调用 | SDK入口已提取，外围播放与结果保存用自己的实现 |
| `x78.java`、`o98.java` | 设备信息/密钥缓存、账号设备查询 | 凭据来源单独接入，不能靠复制.so得到账号会话 |
| `hr8.java`、`r78.java`、`n4j.java`、`ga8.java` | 官方数据库、文件云记录、上传/纪要/转写任务 | 用自有存储和处理服务替代；不捆绑钉盘、组织或官方付费服务 |
| `DingerInterfaceImpl.java` | H5桥接门面，混合参数检查、页面与业务调用 | 不搬官方前端，不把这个大类整体当成可独立模块 |

源文件位于`apks/8.5.8.3/work/src/sources`。这些上层类在研究目录保留，不放进本次独立核心包。

## 5. 接入与验证边界

```text
自定义界面 / 自定义动作 / 自有ASR和AI
                 ↓ 命令、设置       ↑ 事件、音频、文件
                 后台适配层
                 ↓ JNI            ↑ 回调
       同版本 DingerAudioTools + libDingerSdk
                 ↓ OnSendData      ↑ PushBleRecvData
              宿主 Android BLE 传输
                         ↕
                        A1
```

密钥来自独立的凭据接入流程，注入后台适配层。SDK、Kotlin不能同时管理同一下载的ACK/写文件；上层收到SDK真正的完成事件并验证产物后再保存“完成”。

当前已完成的验证：

- 两个.so与来源APK成员逐字节一致并记录SHA-256。
- 9个核心Java源用JDK21的`javac --release 8`编译成功，生成Java8字节码核心JAR；另6个辅助文件保留为源码，未在本轮独立编译。
- 42个native方法名均在对应.so找到直接JNI导出；未据此声称所有参数描述符/运行时回调已验收。
- 动态链接依赖只有libc++_shared.so及Android系统的liblog/libm/libdl/libc；不需要把libddopustools.so仅因名字含opus就加进来。运行期配置/模型资源仍要按启用功能核对。
- 当前App的JNI声明有34个native方法，新提取接口有42个；新增8个音频通道/单帧解码入口，没有删除现有方法名。当前App内.so与新提取库哈希不同，替换需按整套版本验证。

尚未做的是把此版本接入现有App并在Android上验证初始化、真实事件/音频、完整文件和断连恢复。编译通过不等于设备上已可用。官方二进制来源与自己的开源适配层分别记录；本次没有发布二进制或私人材料。

公开Java文件已去除JADX注释中的本机绝对路径；实际下载件校验以vendor目录的manifest.json和package-manifest.json为准，提取时原始哈希另行保留。
