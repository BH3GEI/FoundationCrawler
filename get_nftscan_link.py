import csv

# 创建一个新的CSV文件来存储结果
with open('nftscan_links.csv', 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(['NFTScan Link'])  # 写入标题行

    # 处理 missing_nft_information.csv 文件
    with open('missing_nft_information.csv', 'r') as infile:
        reader = csv.reader(infile)
        next(reader)  # 跳过标题行
        for row in reader:
            if len(row) >= 3:
                contract_address = row[1]
                token_id = row[2]
                link = f"https://eth.nftscan.com/{contract_address}/{token_id}"
                writer.writerow([link])

    # 处理 error_urls.txt 文件
    with open('error_urls.txt', 'r') as error_file:
        for line in error_file:
            line = line.strip()
            if line.startswith('https://foundation.app/mint/eth/'):
                new_link = line.replace('https://foundation.app/mint/eth/', 'https://eth.nftscan.com/')
                writer.writerow([new_link])

print("处理完成,结果已保存到 nftscan_links.csv 文件中。")

