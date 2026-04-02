

# Practice_Score_System

使用数据库存储实践成绩信息，来代替传统使用Excel表格存储的方式，更方便了录入成绩和版本管理。
```
仓库remote：practice
```
# 社会实践成绩管理系统（简要说明）

## 环境要求

- Python **3.8 或更高版本**

## 依赖（固定版本）

在项目根目录创建（或使用）`requirements.txt`：

```txt
Flask==2.3.3
pandas==2.0.3
openpyxl==3.1.2
```

## 安装依赖
```txt
pip install -r requirements.txt
```

## 运行
```txt
先启动
python init_db.py
再启动
python app.py
```
## 第一次使用遇到的问题 V5.0版本（已解决）

```txt
1.录入端会2次录入，容易覆盖原有数据，达到修改的效果（不可取）
```

## 第二次更新

```
1.更新了登陆页面
2.将.idea文件夹添加到.gitnore中
```

