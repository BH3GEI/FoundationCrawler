# Foundation NFT 数据采集工具

## 简介

一个简单的网络爬虫工具

## 功能

- 从文本文件中读取多个 NFT 页面的 URL
- 采集 Foundation 平台上 NFT 的基本信息（如描述、收藏信息、所有者等）
- 提取 NFT 的活动历史
- 将数据保存为 JSON 和 CSV 格式
- 生成 NFTScan 链接
- 采集 NFTScan 平台上的 NFT 数据

## 使用方法

确保已安装所需的依赖（Scrapy, Selenium 等）后，可以通过以下几种方式运行爬虫：

1. 使用 Scrapy 命令行（推荐）：

   - 采集单个 URL：
     ```
     scrapy crawl foundation -a url="https://foundation.app/mint/eth/0x4b36e12afed1e35396c25904c3aecdd71ecbff3e/5"
     ```

   - 从文件读取多个 URL：
     ```
     scrapy crawl foundation -a file="urls.txt"
     ```

2. 直接运行 Python 脚本：

   ```
   python3 foundation_spider.py /path/to/your/urls.txt
   ```

3. 如果没有提供参数，默认会尝试读取当前目录下的 `urls.txt` 文件：

   ```
   python3 foundation_spider.py
   ```

## 输出

程序会为每个 URL 生成三个文件：
- `foundation_data_[URL_IDENTIFIER].json`：完整的 JSON 格式数据
- `foundation_data_[URL_IDENTIFIER].csv`：基本的 CSV 格式数据
- `foundation_data_[URL_IDENTIFIER]_flat.csv`：扁平化的 CSV 格式数据

## 附加工具

### 1. NFTScan 链接生成器

使用 `get_nftscan_link.py` 脚本可以生成 NFTScan 链接：

```
python3 get_nftscan_link.py
```

这个脚本会处理 `missing_nft_information.csv` 和 `error_urls.txt` 文件，生成对应的 NFTScan 链接，并将结果保存在 `nftscan_links.csv` 文件中。

### 2. NFTSCAN 爬虫

`nftscan_spider.py` 是用于采集 NFTScan 平台数据的爬虫脚本。使用方法如下：

```
python3 nftscan_spider.py
```

这个脚本会读取 `nftscan_links.csv` 文件中的链接，并采集每个 NFT 的详细信息。采集的数据将保存在 `nftscan_data.csv` 文件中。

