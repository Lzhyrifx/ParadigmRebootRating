# ParadigmRebootRating
## 计算范式：起源Rating组成
**目前仍在持续更新**<br><br>
查询范式：起源Rating组成成分即best50<br>
通过OCR截图来排序best35+best15<br>(简称b35+b15合称b50)<br>
Rating的计算详见[范式：起源wiki](https://paradigmrebootzh.miraheze.org/wiki/Rating)


## 导入
- 通过adb连接手机/平板使用无障碍模式进行批量截图<br>
- 手动截图(支持选曲界面和结算界面)
## OCR
判断截图类型<br>
选取指定歌曲,曲师,分数区域<br>
使用RapidOCR进行OCR

## 匹配
通过[Paradigm Prober](https://prp.icel.site/)的[Fastapi](https://api.prp.icel.site/songs)拉取全部歌曲数据到本地<br>
匹配难度→曲师→歌曲<br>
通过模糊匹配保存结果到本地

## 上传
登录到[Paradigm Prober](https://prp.icel.site/)<br>
选择Rating最高的35首旧版本歌曲和15首新版本歌曲上传[Paradigm Prober](https://prp.icel.site/)

## 获取b50
通过[Paradigm Prober](https://prp.icel.site/)获取b50图片

## 声明
本软件与击弦网络及相关游戏发行、开发及分发公司无任何关系，均使用互联网公开资源，仅供学习研究用途，相关版权归相关方所有
