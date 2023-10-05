from bs4 import BeautifulSoup
from selenium import webdriver
import pandas
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


def get_pages(html):
    soup = BeautifulSoup(html, 'lxml')
    pages = soup.find('div', class_=re.compile('js-pages pagination-pagination-_FSNE')).find_all('span', class_=re.compile('styles-module-text-InivV'))[-1].text
    print(f'Найдено страниц выдачи: {pages}')
    return int(pages)


def get_content_page(html):
    soup = BeautifulSoup(html, 'lxml')
    blocks = soup.find_all('div', class_=re.compile('iva-item-root-_lk9K photo-slider-slider-S15A_ iva-item-list-rfgcH iva-item-redesign-rop6P iva-item-responsive-_lbhG items-item-My3ih items-listItem-Gd1jN js-catalog-item-enum'))
    data = []
    for block in blocks:
        data.append({
            "Наименование": block.find('h3').get_text(),
            "Цена": block.find('meta', attrs={'itemprop': 'price'})["content"],
            "Район": block.find('div', attrs={'data-marker': 'item-address'}).find('span', attrs={'class': ''}).get_text(),
            "Ссылка": 'https://www.avito.ru' + block.find('a', attrs={'data-marker': 'item-title'})["href"]
        })
    return data


def parser(url):
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--log-level=3')
    options.add_argument("--headless")
    browser = webdriver.Chrome(options=options)
    browser.get(url)
    html = browser.page_source
    pages = get_pages(html)
    data_list_pages = []
    for page in range(1, pages + 1):
        link = url + f'&p={page}'
        try:
            browser.get(link)
            html = browser.page_source
            data_list_pages.extend(get_content_page(html))
            print(f'Парсинг страницы {page} завершен. Собрано {len(data_list_pages)} позиций')
        except Exception as ex:
            print(f'Ошибка: {ex}')
            print(link)
            browser.close()
            browser.quit()
    print('Сбор данных завершен.')
    return data_list_pages


def save_exel(data):
    dataframe = pandas.DataFrame(data)
    df = dataframe.drop_duplicates(['Ссылка'])
    writer = pandas.ExcelWriter(f'data_avito.xlsx')
    df.to_excel(writer, 'data_avito')
    writer.save()
    print(f'Собрано {len(df)} различных объявлений')
    print(f'Данные сохранены в файл "data_avito.xlsx"')


def count_dist(p1, p2):
    xpath_button = "/html/body/div[1]/div[2]/div[2]/header/div/div/div/form/div[4]/div/div/a/span/div/svg"
    xpath_from = "/html/body/div[1]/div[2]/div[11]/div/div[1]/div[1]/div[1]/div/div[1]/div/div/div/div[2]/div/form/div[2]/div[1]/div/div[1]/div/div/div[2]/div/div/span/span[1]/input"
    xpath_to = "/html/body/div[1]/div[2]/div[11]/div/div[1]/div[1]/div[1]/div/div[1]/div/div/div/div[2]/div/form/div[2]/div[1]/div/div[2]/div/div/div[2]/div/div/span/span[1]/input"
    xpath_res = "/html/body/div[1]/div[2]/div[11]/div/div[1]/div[1]/div[1]/div/div[1]/div/div/div/div[2]/div[2]/div/div[4]/div[1]/div/div[1]/div[1]"
    map_url = "https://yandex.ru/maps"
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--log-level=3')
    options.add_argument("--headless")
    browser = webdriver.Chrome()
    wait = WebDriverWait(browser, 50)
    browser.get(map_url)
    button = wait.until(EC.visibility_of_element_located((By.XPATH, xpath_button)))
    button.click()
    p_from = wait.until(EC.visibility_of_element_located((By.XPATH, xpath_from)))
    p_from.send_keys(p1)
    p_from.send_keys(Keys.ENTER)
    p_to = wait.until(EC.visibility_of_element_located((By.XPATH, xpath_to)))
    p_to.send_keys(p2)
    p_to.send_keys(Keys.ENTER)
    time = wait.until(EC.visibility_of_element_located((By.XPATH, xpath_res)))
    dist = 0
    if 'ч' in time.text and 'мин' in time.text:
        str = time.text.split(' ')
        dist += int(str[0])*60 + int(str[2])
    elif 'ч' in time.text:
        str = time.text.split(' ')
        dist += int(str[0])*60
    else:
        dist += int(time.text[:-3:])
    return int(dist)


def solve(url):
    data = parser(url)
    dist = int(input("Введите сколько минут вы готовы потратить на поездку или 0, если без разницы:"))
    if dist == 0:
        save_exel(data)
        return
    points = pandas.read_csv("points.csv")
    var = []
    for element in data:
        good = True
        for p in points['Район']:
            if count_dist(element['Район'], p) > dist:
                good = False
                break
        if good:
            print("Нашли подходящее объявление")
            new_el = element
            new_el["Расстояние"] = dist
            var.extend(new_el)
            if len(var) == 20:
                break
    save_exel(var)
    browser.close()
    browser.quit()



if __name__ == "__main__":
    url = input('Введите ссылку на раздел, с заранее выбранными характеристиками (ценовой диапазон и тд):\n')
    print('Запуск парсера...')
    solve(url)
