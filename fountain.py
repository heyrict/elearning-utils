# coding: utf-8
"""
Automatically comment or crawl comments in the forum.
"""

import time

from selenium.webdriver.common.keys import Keys

openInNewTab = Keys.CONTROL + Keys.SHIFT + Keys.ENTER

LOAD_WAITING_TIME = 5


def fountain(dr, grub_page=10):
    """
    Comment in a thread using the last comment in grub_page.
    """
    # turn to page 10
    somepageinp = dr.find_element_by_class_name("laypage_skip")
    somepageinp.send_keys(grub_page)
    somepagebtn = dr.find_element_by_class_name("laypage_btn")
    somepagebtn.click()

    # grep text
    somecontent = dr.find_element_by_xpath("//p[@class='comment_content']")
    ttc = somecontent.text

    # flow the thread
    frame = dr.find_element_by_tag_name("iframe")
    frame.click()
    frame.send_keys(ttc)
    print("Get text:", ttc)
    framebtn = dr.find_element_by_class_name("issue_btn")
    framebtn.click()


def flow_the_page(dr, title_filter=None, call_back=fountain, **kwargs):
    """
    Call call_back(**kwargs) in multiple threads matching title_filter in the current page.
    """
    returns = []

    eles = dr.find_elements_by_xpath(
        "//ul[@class='theme_list']/li//a[@class='ng-binding'][@ng-bind='m.Title']"
    )
    for ele in eles[1:]:
        if title_filter != None and not title_filter(ele):
            continue
        ele.send_keys(openInNewTab)
        time.sleep(LOAD_WAITING_TIME)
        dr.switch_to_window(dr.window_handles[1])
        try:
            returns.append(call_back(dr, **kwargs))
        except:
            print("Error in calling %s with arguments: %s" %
                  (call_back.__name__, str(kwargs)))
        dr.close()
        dr.switch_to_window(dr.window_handles[0])

    return returns


def crawl_the_contents(dr, answCount=3):
    returns = {}

    returns["cont"] = dr.find_element_by_class_name("bulletin_box").text

    # grep text
    somecontent = dr.find_elements_by_xpath("//p[@class='comment_content']")
    returns["answ"] = [i.text for i in somecontent]

    return returns
