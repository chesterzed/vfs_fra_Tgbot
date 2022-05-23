from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC

import os.path


browser_driver_path = 'source/chromedriver.exe'
website_link = 'https://visa.vfsglobal.com/rus/ru/fra/login'


def open_browser_and_website():  # open
    driver = webdriver.Chrome(service=Service(browser_driver_path))
    driver.get(website_link)
    WebDriverWait(driver, 20).until(EC.invisibility_of_element(driver.find_element(by=By.ID, value="loader")))
    close_cookie(driver)
    return driver


def close_cookie(driver):  # close cookie notification
    WebDriverWait(driver, 20).until(lambda d: d.find_element(by=By.CLASS_NAME, value="banner-close-button"))
    driver.find_element(by=By.CLASS_NAME, value="banner-close-button").click()


#################### login ####################


def account_enter(driver, login, password):
    email_elem = driver.find_element(by=By.XPATH, value="//input[@formcontrolname='username']")
    pass_elem = driver.find_element(by=By.XPATH, value="//input[@formcontrolname='password']")
    email_elem.send_keys(login)
    pass_elem.send_keys(password)
    pass_elem.send_keys(Keys.ENTER)

    wait_load(driver, 20, "ngx-overlay")


def start_new_booking(driver):  # start new booking
    but_sign = driver.find_element(by=By.CLASS_NAME, value="btn-block")
    but_sign.click()
    # loading wait
    wait_load(driver, 20, "ngx-overlay")


############# Application Details #############


def show_VAC(driver):  # Choose your Visa Application Centre
    app_centre = driver.find_element(by=By.XPATH, value="//*[@formcontrolname='centerCode']")
    li = dropdown_show_names(driver, app_centre)
    return li


def choose_VAC(driver, vac_len, choice):
    app_centre = driver.find_element(by=By.XPATH, value="//*[@formcontrolname='centerCode']")
    dropdown_choose(driver, app_centre, vac_len, choice)
    wait_load(driver, 30, "ngx-overlay")  # loading wait


def show_AC(driver):  # Choose your appointment category
    app_category = driver.find_element(by=By.XPATH, value="//*[@formcontrolname='selectedSubvisaCategory']")
    li = dropdown_show_names(driver, app_category)
    return li


def choose_AC(driver, vac_len, choice):
    app_category = driver.find_element(by=By.XPATH, value="//*[@formcontrolname='selectedSubvisaCategory']")
    dropdown_choose(driver, app_category, vac_len, choice)
    wait_load(driver, 30, "ngx-overlay")  # loading wait


def show_SC(driver):  # Choose your sub-category
    sub_category = driver.find_element(by=By.XPATH, value="//*[@formcontrolname='visaCategoryCode']")
    li = dropdown_show_names(driver, sub_category)
    return li


def choose_SC(driver, vac_len, choice):
    sub_category = driver.find_element(by=By.XPATH, value="//*[@formcontrolname='visaCategoryCode']")
    dropdown_choose(driver, sub_category, vac_len, choice)
    wait_load(driver, 30, "ngx-overlay")  # loading wait


def check_alert(driver, isClickable, xpath):
    # "//div[text()=' В настоящее время нет свободных мест для записи ']"
    # "//button[contains(@class,'mat-focus-indicator btn')]"
    try:
        print("wait")
        b = WebDriverWait(driver, 3).until(EC.visibility_of_element_located(
            (By.XPATH, xpath)))
        if isClickable:
            b.click()
        to_dashboard(driver)
        print("wait")
        return True
    except Exception:
        print("Элемента нет")
        return False


def to_dashboard(driver):
    driver.find_element(by=By.XPATH, value="//a[@data-toggle='dropdown']").click()
    driver.find_element(by=By.XPATH,
                        value="//div[contains(@class,'dropdown-menu dropdown-menu-right')]//a[1]").click()


def next_step_to_ur_det(driver):
    # check button on: if Class name == "mat-button-disabled" => to sqlite
    # next step
    next_but = driver.find_element(by=By.CLASS_NAME, value="mat-raised-button")
    next_but.click()
    # loading wait
    wait_load(driver, 30, "ngx-overlay")


################################################


def set_your_details(driver, data):
    wait_load(driver, 30, "ngx-overlay")
    # Your Details
    # fields
    visa_field = driver.find_element(
        by=By.XPATH, value="//input[contains(@class,'mat-input-element mat-form-field-autofill-control')]")
    f_name = driver.find_element(
        by=By.XPATH, value="(//input[contains(@class,'mat-input-element mat-form-field-autofill-control')])[2]")
    l_name = driver.find_element(
        by=By.XPATH, value="(//input[contains(@class,'mat-input-element mat-form-field-autofill-control')])[3]")
    gender = driver.find_element(by=By.XPATH, value="//mat-select")
    birth = driver.find_element(by=By.XPATH, value="//input[contains(@class,'form-control fs-inherit')]")
    nationality = driver.find_element(by=By.XPATH, value="(//mat-select)[2]")
    # зависит от языка
    passport_num = driver.find_element(by=By.XPATH, value="//input[@placeholder='Введите номер паспорта']")
    passport_expiry = driver.find_element(by=By.XPATH, value="(//input[contains(@class,'form-control fs-inherit')])[2]")
    phone_code = driver.find_element(by=By.XPATH, value="//input[@placeholder='44']")
    phone_number = driver.find_element(by=By.XPATH, value="//input[@placeholder='012345648382']")
    email = driver.find_element(by=By.XPATH, value="//input[@type='email']")

    # data
    gen = dropdown_show_names(driver, gender)
    dropdown_choose(driver, gender, len(gen), data[7])

    visa_field.send_keys(data[4])                         # visa_field.send_keys("FRA987VSGX9872176")
    f_name.send_keys(data[5])                             # f_name.send_keys("roman")
    l_name.send_keys(data[6])                             # l_name.send_keys("fedorov")
    birth.send_keys(data[8])                              # birth.send_keys("20052000")
    passport_num.send_keys(data[10])                      # passport_num.send_keys("6548")
    passport_expiry.send_keys(data[11])                   # passport_expiry.send_keys("20052025")
    phone_code.send_keys(data[12])                        # phone_code.send_keys("44")
    phone_number.send_keys(data[13])                      # phone_number.send_keys("123456789")
    email.send_keys(data[14])                             # email.send_keys("saiuyfb@mail.com")

    nat = dropdown_show_names(driver, nationality)
    dropdown_choose(driver, nationality, len(nat), data[9])

    write_list_to_file("chfiles/genders.txt", gen)
    write_list_to_file("chfiles/nationalities.txt", nat)

    # next button
    next_but = driver.find_element(
        by=By.XPATH, value="(//button[contains(@class,'mat-focus-indicator mat-stroked-button')])[2]")
    next_but.click()

    # loading wait
    wait_load(driver, 30, "ngx-overlay")


def next_to_date(driver):
    # next button
    next_but = driver.find_element(
        by=By.XPATH, value="(//button[contains(@class,'mat-focus-indicator btn')])[3]")
    next_but.click()

    # loading wait
    wait_load(driver, 30, "ngx-overlay")


def set_date(driver):
    # checking dates   class name => date-availiable
    # select date
    free_date = driver.find_element(by=By.CLASS_NAME, value="date-availiable")
    print(free_date.text)
    free_date.click()
    # checking time   class name => hidden-item
    # select time
    free_time = driver.find_element(by=By.CLASS_NAME, value="hidden-item")
    print(free_time.text)
    free_time.click()

    # next step (3 end)
    next_but = driver.find_element(by=By.XPATH, value="(//button[contains(@class,'mat-focus-indicator btn')])[3]")
    next_but.click()

    # loading wait
    wait_load(driver, 30, "ngx-overlay")

    # next step - страховка (4)
    next_but = driver.find_element(by=By.XPATH, value="(//button[contains(@class,'mat-focus-indicator btn')])[2]")
    next_but.click()

    # next step (confirm)
    next_but = driver.find_element(by=By.XPATH, value="//button[@matdialogclose='true']")
    next_but.click()

    # loading wait
    wait_load(driver, 30, "ngx-overlay")


def last_confirm(driver):
    wait_load(driver, 30, "ngx-overlay")
    toggle = driver.find_element(by=By.XPATH, value="//label[@class='mat-checkbox-layout']//span")
    toggle.click()
    next_but = driver.find_element(by=By.XPATH, value="(//button[contains(@class,'mat-focus-indicator btn')])[2]")
    next_but.click()
    wait_load(driver, 30, "ngx-overlay")

    last_but = driver.find_element(by=By.XPATH, value="//button[contains(@class,'mat-focus-indicator btn')]")
    last_but.click()
    wait_load(driver, 30, "ngx-overlay")


################# if no places #################


# find 'dashboard' button
# //div[contains(@class,'alert alert-info')]
# //a[@data-toggle='dropdown']
# //div[contains(@class,'dropdown-menu dropdown-menu-right')]//a[1]


################################################
##################### help #####################


def wait_load(driver, sec, load_scr_class):  # wait
    WebDriverWait(driver, sec).until(
        EC.invisibility_of_element(driver.find_element(by=By.CLASS_NAME, value=load_scr_class)))


def dropdown_choose(driver, element, max_list_len, choose):
    if str(type(choose)) == "<class 'int'>":
        for i in range(choose):
            element.send_keys(Keys.ARROW_DOWN)
        element.send_keys(Keys.ENTER)
        return

    for i in range(1, max_list_len + 1):
        ch = driver.find_element(by=By.XPATH, value="(//mat-option[@role='option']//span)[" + str(i) + "]").text
        if ch == choose:
            element.send_keys(Keys.ENTER)
            break
        else:
            element.send_keys(Keys.ARROW_DOWN)


def dropdown_show_names(driver, element):
    li = []
    element.click()
    driver.implicitly_wait(6)
    elems = driver.find_elements(by=By.XPATH, value="//mat-option[@role='option']//span")
    for i in elems:
        li.append(i.text)
    return li


def write_list_to_file(f_name, value_list):
    if not os.path.exists(f_name):
        with open(f_name, "w+") as file:
            for i in value_list:
                file.write(str(i) + '\n')


def reset_all_choice_files():
    test_data = ["", "", "", "", "FRA987VSGX9872176", "roman", "fedorov", "Male", "20052000",
                 "ALBANIA", "6548", "20052025", "44", "123456789", "saiuyfb@mail.com"]
    driver = open_browser_and_website()
    account_enter(driver, "chester.1.80@mail.ru", "1Q2w3e##")
    start_new_booking(driver)

    if not os.path.exists("chfiles/"):
        os.mkdir("chfiles/")

    # remove all files
    if os.path.exists("chfiles/VAC.txt"):
        os.remove("chfiles/VAC.txt")
    if os.path.exists("chfiles/AC.txt"):
        os.remove("chfiles/AC.txt")
    if os.path.exists("chfiles/longSC.txt"):
        os.remove("chfiles/longSC.txt")
    if os.path.exists("chfiles/shortSC.txt"):
        os.remove("chfiles/shortSC.txt")

    # add new files

    li = show_VAC(driver)
    choose_VAC(driver, len(li), 2)
    write_list_to_file("chfiles/VAC.txt", li)

    li = show_AC(driver)
    choose_AC(driver, len(li), 0)
    write_list_to_file("chfiles/AC.txt", li)

    li = show_SC(driver)
    choose_SC(driver, len(li), 1)
    write_list_to_file("chfiles/longSC.txt", li)

    li = show_AC(driver)
    choose_AC(driver, len(li), 2)

    li = show_SC(driver)
    choose_SC(driver, len(li), 12)
    write_list_to_file("chfiles/shortSC.txt", li)

    next_step_to_ur_det(driver)

    if check_alert(driver, False, "//div[text()=' В настоящее время нет свободных мест для записи ']"):
        return

    if os.path.exists("chfiles/genders.txt"):
        os.remove("chfiles/genders.txt")
    if os.path.exists("chfiles/nationalities.txt"):
        os.remove("chfiles/nationalities.txt")

    set_your_details(driver, test_data)
    to_dashboard(driver)

