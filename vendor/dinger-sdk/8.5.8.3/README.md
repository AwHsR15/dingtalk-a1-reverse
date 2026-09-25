# 官方 A1 后台核心提取件 8.5.8.3

这是从本地官方 APK 提取并发布的第三方后台组件，不含官方前端。仅支持已提取的 Android arm64-v8a。

- `jniLibs/arm64-v8a/libDingerSdk.so`：来自 split_demand1.apk。
- `jniLibs/arm64-v8a/libc++_shared.so`：来自 base.apk。
- `java/com/android/dingersdk/nativeInterface/`：来自 base.apk/classes27.dex，经 JADX 1.5.2 反编译的15个顶层Java文件。
- `dinger-jni-core.jar`：由其中9个核心源以 javac --release 8 编译生成，不是官方原包内现成JAR。
- `manifest.json`：17个发布来源文件的大小、哈希和出处；Java仅去掉反编译注释中的本机路径，另保留脱敏前哈希。
- `package-manifest.json`：本目录其余全部发布文件的大小和哈希。
- `interface-inventory.json`：42个JNI声明及与先前客户端的接口差异。

## 接入

见[SDK接入文档](../../../docs/SDK_INTEGRATION.md)和[完整模块映射](../../../A1_BACKEND_MODULE_MAP_2026-09-25.md)。保持原JNI包名，JAR和其中同名Java源二选一。其他6个辅助源有Android相关依赖。

已验证来源文件哈希、核心Java编译、42个方法名对应JNI导出；没有完成这个版本在独立App中的全套实机验收。存在接口不等于设备支持全部功能。

OTA等接口保留原样，不作为本项目启用功能。账号会话、设备密钥、官方云服务环境及可选运行期模型没有包含在此包中。

## 权利说明

这些是官方/第三方原件及其接口提取件，**不适用根目录MIT授权**。本项目不能替原权利人授予许可；参见[NOTICE](../../../NOTICE.md)。
