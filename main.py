import requests
from bs4 import BeautifulSoup
import os
import shutil
import time
this_file_path = os.path.realpath(__file__)
this_file_path = this_file_path.replace('\\','/')
p_dir = '/'.join(this_file_path.split('/')[:-1])
class asahi():
    def __init__(self):
        self.url = "https://asahichinese-f.com"
    def get_url(self):
        return self.url
    def get_navigator(self) -> [dict, dict]:
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, "html.parser")
        nav_ele = soup.find(id='GlobalNav').findAll("a")
        nav_dict = {}
        translate_dict = {}
        dir_name_dict = {}
        for nav in nav_ele:
            if nav.text != "首頁":
                nav_dict[nav.text] = f"{nav.get('href')}"
                translate_dict[nav_dict[nav.text].split('/')[-2]] = nav.text
                dir_path = nav.get('href')
                for dir_name in translate_dict.keys():
                    dir_path = dir_path.replace(dir_name, translate_dict[dir_name])
                dir_name_dict[nav.text] = dir_path
        return nav_dict, dir_name_dict
    def get_article_list(self, navigator) -> list:
        page = 1
        all_href_set = set()
        # get all article href in this navigator 
        while True:
            print(f"\rnumber of page:{page}",end="")
            response = requests.get(f"{self.url}{navigator}?p={page}")
            soup = BeautifulSoup(response.text, "html.parser")
            # article
            content = soup.find(class_='Section Headlines').findAll("a")
            href_list = []
            for href in content:
                href_list.append(href.get("href"))
            
            if not (set(href_list) - all_href_set):
                break
            all_href_set |= set(href_list)
            page += 1
            time.sleep(1)
        print("")
        return list(all_href_set)
if __name__ == "__main__":
    asahi_crawler = asahi()
    navigator_dict, dir_dict = asahi().get_navigator()
    for navigator in navigator_dict:
        print(navigator_dict[navigator], dir_dict[navigator])
        #.get_article_list("/business/")
        navigator_response = requests.get(f"{asahi_crawler.get_url()}{navigator_dict[navigator]}")
        article_list = asahi_crawler.get_article_list(navigator_dict[navigator])
        for pg, article in enumerate(article_list):
            print(f"\rpg:{pg}/{len(article_list)}", end="")
            article_response = requests.get(f"{asahi_crawler.get_url()}{article}")
            soup = BeautifulSoup(article_response.text, "html.parser")
            # article title
            article_title = soup.find(class_="ArticleTitle").find("h1").text
            article_dir_path = f"{p_dir}{dir_dict[navigator]}{article.split('/')[-1]}"
            if not os.path.isdir(article_dir_path):
                os.makedirs(article_dir_path)
            #  main image
            image_list = soup.findAll(class_="Image")
            if len(image_list) > 0:
                for count, image in enumerate(image_list):  
                    if image.find("img"):
                        image_src = image.find("img").get("src")
                        if image_src.find("http:") < 0:
                            image_src = "http:" + image_src
                        req = requests.get(image_src, stream = True)
                        if req.status_code == 200:
                            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
                            req.raw.decode_content = True
                            image_text = image.find(class_="Caption").text
                        # Open a local file with wb ( write binary ) permission.
                            filename_extension = image_src.split(".")[-1]
                            filename = f"{article_dir_path}/main_image_{count}.{filename_extension}"
                            with open(filename,'wb') as f:
                                shutil.copyfileobj(req.raw, f)
                            with open(f"{article_dir_path}/article_data.txt",'w',encoding="utf-8") as f:
                                f.write(f"main_image_{count}:{image_text}\n")
            else:
                print("no main image")
            
            # extra image
            
            thum_class = soup.find(class_="Thum")
            if thum_class:
                extra_image_list = thum_class.findAll("img")
                if len(extra_image_list) > 0:
                    for count, image in enumerate(extra_image_list):  
                        image_src = image.get("src")
                        if image_src.find("http:") < 0:
                            image_src = "http:" + image_src
                        req = requests.get(image_src, stream = True)
                        if req.status_code == 200:
                            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
                            req.raw.decode_content = True
                        # Open a local file with wb ( write binary ) permission.
                            filename_extension = image_src.split(".")[-1]
                            filename = f"{article_dir_path}/extra_image_{count}.{filename_extension}"
                            with open(filename,'wb') as f:
                                shutil.copyfileobj(req.raw, f)
                else:
                    print("no main image")
            
            # author
            author = soup.find(class_="ArticleName").text
            # date
            date = soup.find(class_="LastUpdated").text
            # article tag
            tag_list = soup.find(class_="Tag").findAll("a")
            tags = []
            for tag in tag_list:
                tags.append(tag.text)
            tags = ','.join(tags)
            with open(f"{article_dir_path}/article_data.txt",'w',encoding="utf-8") as f:
                f.write(f"article_title:{article_title}\n")
                f.write(f"author:{author}\n")
                f.write(f"date:{date}\n")
                f.write(f"tags:{tags}\n")
            # content text
            with open(f"{article_dir_path}/content.txt",'w',encoding="utf-8") as f:
                f.write(soup.find(class_='ArticleText').get_text())
            time.sleep(2)
        print("")
    