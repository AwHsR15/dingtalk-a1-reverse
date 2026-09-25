# 官方 A1 绑定与密钥取得链路

日期：2026-09-25。只读分析已有8.5.8.3 APK、已保存H5快照，并获取公开智能设备跳转页；未执行新绑定、解绑、恢复出厂或账号请求。本文不把root提取缓存当作无root接入方案。

## 1. A1 的实际入口

已保存官方H5 `smart-hardware-ai-assistant/0.181.1/mobile-recording/dd3fc05eaf0a1ed1801e.js`：

- 约字符333000–337100：连接入口`as()`打开`https://qr.dingtalk.com/page/smartdevice?conn=qr&code=13&service=<serviceId>`。
- 日本地区分支附加`from=japan`；约1064032处服务枚举standard=1383、Pro=1415、earphone=1413、lite=1392、A14G=1446。这是页面快照，不冒充当前账号实际分发配置。
- 扫码分支调用`biz.util.scan`，将扫码URL交给官方链接处理器；没有在该页面直接生成密钥。

classes5的`DoorGuardImpl.parseDeviceBindUrl:602–661`解析这个URL。当开关`nvr.a()`启用且deviceTypeCode=13、serviceId=1383时，进入`LightAppUtil.h`；该函数`:247–257`把qr域名入口改为pages域名并打开WebView。其他分支进入DeviceBindActivity，因此不能把通用原生绑定界面视为所有版本A1唯一入口。

## 2. 服务器还决定下一段流程

本轮实际获取了公开页面：

[智能设备跳转页](https://pages.dingtalk.com/wow/dingtalk/act/smartdevice?conn=qr&code=13&service=1383&from=japan)

其源码160–178行在钉钉环境中执行：

```text
dd.internal.request.lwp
  uri: /r/Adaptor/OpenDeviceI/getRedirectUrl
  body: [当前URL查询串]
结果: success / url / miniVersion / errorCode / errorMsg
```

成功后检查最低客户端版本，再打开服务端返回的url。日本地区标记随查询串传给该请求。本次仅获取静态公开页面，没有调用已登录账号的LWP，所以**当前日版账号被分发的最终绑定页地址仍未取得**。

这明确了下一处证据边界：完整确认当前日版首次绑定，需要观察用户自己账号中getRedirectUrl的实际返回及其加载的后台调用；无需重新测试已知右键。前端只作入口证据，不纳入要嵌入的模块包。

## 3. APK 中已有的原生绑定后端

以下调用已读源码，但属于通用设备绑定实现；不能在缺少上一节实际分发结果时，把它所有步骤都断言为日版A1当前路径。

| 阶段 | 函数及文件 | 输入和输出 |
| --- | --- | --- |
| BLE连接 | `BleBindPresenter.d0:1894–1902` | FE3C服务，FE1C写、FE1B读/持续通知；由Doraemon BluetoothMagician建立BleInterface |
| 读取激活资料 | `BleBindPresenter.w.run:1396起`及`e.onActiveInfo:223–245` | `getActiveInfo()`取得sn/devServId/info/compTag等；保存到绑定数据源 |
| 账号绑定请求 | `BleBindPresenter.bind:1776–1790`→`c98.b` | corpId、devServid、activeInfo、nick、deviceMac→guard版DeviceIService.bindAndActive |
| 绑定结果 | `BleBindPresenter.m.onDataReceived`→b0 | BindDeviceModel；不能仅凭“绑定成功”推断响应直接含deviceSecret |
| 已有设备取密钥 | `BleBindPresenter.n0:2080–2082`→`c98.j` | 明确参数是serviceId和deviceId→DeviceIService.getDeviceSecret→String |
| 密钥成功回调 | `BleBindPresenter.c.onDataReceived:163起` | 空值或断连拒绝继续；非空值交f0构造握手材料，再B0执行；另有getDeviceEndorsementV2分支 |

`c98.java`位于classes5，是账号RPC服务包装器；依赖`lcq`服务代理、`ApiEventListener`和官方账号网络环境。它不是.so内的纯本地函数。通用绑定的握手格式与已绑定A1的0x0008/0x0133连接鉴权应分别记录，不能混用。

### 一个重要更正

已经读取的BindDeviceModel定义有uid/devId/url/activeCode/extInfo，并没有具名deviceSecret字段。密钥来源应按**设备信息查询/专门密钥查询**建立证据，不能笼统说“调用绑定必然直接返回密钥”。extInfo是否在某机型另含数据，本轮没有响应证据。

## 4. A1 已绑定后的密钥链已闭合

这是classes19的A1业务代码，证据比上节通用绑定分支更直接：

```text
o98.a
  → DeviceMonitorIService.queryUserBindDevices(requestId)
  → QueryUserBindDevicesResultModel.deviceModel
  → DingerInterfaceImpl的设备列表成功回调
  → x78.N：保存完整DeviceModel列表到官方私有缓存
  → x78.p(deviceId)：取DeviceModel.deviceSecret
  → lj2：取得卡随机值，使用密钥计算token，再发送连接鉴权
```

源码锚点：o98:136–146；DingerInterfaceImpl:2265–2317；x78:161–168、316–320；lj2的0x0008/0x0133链见既有调用链报告。DeviceModel的密钥字段为FieldId(19)。

返回给H5的设备列表经过DeviceInfoH5转换，明确不含deviceSecret，因此`internal.dinger.getDeviceList`不能直接用作密钥导出接口。

历史从root手机取得的就是缓存里的deviceSecret。导入独立App后可离线计算挑战响应；这证明凭据取得后SDK/协议可独立运行，不证明无root取得流程已完成。

## 5. 为什么官方无root能取得，而普通独立App还没接上

官方App在自己的登录会话里请求自己账号有权访问的设备资料，然后写入自己的私有缓存，不需要root。独立App要复现，应取得用户授权的账号会话或官方提供的设备凭据授权/导出能力；仅复制getDeviceSecret包装函数或.so不会自动获得这些条件。

已定位到具体调用和参数，尚未验证第三方App可用的登录授权、该接口权限、日版最终绑定页及密钥交付途径。因此当前可复现边界是：

- **已有本卡凭据→无root独立运行**：历史已成立。
- **任意普通用户→首次取得自己的凭据**：未闭合，继续研究实际授权入口与返回结果。
- **本地核心SDK提取/内嵌**：已提取配套文件，不以复制官方前端或整个账号客户端为前提。

## 6. 材料位置

本轮另通过ADB只读确认平板在线并检查静态资源目录：app_h5apps在指定深度未列出文件；nebulaInstallApps中列出了两份包及其资源文件名，DtNest在指定深度未列出文件。这次有限目录检查没有取得当前账号getRedirectUrl返回值，不能据此推断绑定资源不存在。未导出账号缓存、密钥、录音或Cookie，也未触发重新绑定。

- 当前官方JNI和原生库：`apks/8.5.8.3/backend_bundle/`。
- 单类反编译：`apks/8.5.8.3/work/binding/`，包括c98、BleBindPresenter、DoorGuardImpl、LightAppUtil等。
- 本轮公开跳转页快照：`apks/8.5.8.3/work/binding/public/smartdevice.html`。仅是公开资源，不包含登录账号返回的绑定地址或密钥。
- [后台文件映射](A1_BACKEND_MODULE_MAP_2026-09-25.md)、[原生接口清单](A1_BACKEND_INTERFACE_INDEX_2026-09-25.json)。
