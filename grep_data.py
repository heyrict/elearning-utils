import os
import pickle
from http import cookies
from md5 import hex_md5

import pandas as pd
import requests

TEST_IF = "http://elearning.njmu.edu.cn/G2S/DataProvider/CourseLive/Test/MarkingProvider.aspx/Test_Get"
PAPERCARD_IF = "http://elearning.njmu.edu.cn/G2S/DataProvider/CourseLive/Test/MarkingProvider.aspx/PaperCardInfo_Get"
MARKINGPAPER_IF = "http://elearning.njmu.edu.cn/G2S/DataProvider/CourseLive/Test/MarkingProvider.aspx/MarkingPaperInfo_Get"
TESTTEMPSAVE_IF = "http://elearning.njmu.edu.cn/G2S/DataProvider/CourseLive/Test/MarkingProvider.aspx/TestTempSave_Upd"
TESTSUBMIT_IF = "http://elearning.njmu.edu.cn/G2S/DataProvider/CourseLive/Test/MarkingProvider.aspx/Test_Submit"
LOGIN_IF = "http://elearning.njmu.edu.cn/Portal/Ashx/Login.ashx"

UNPUBLISHED_MSG = "Error! The results are not published yet!"


class ResultsUnpublishedError(Exception):
    def __init__(self, *args, **kwargs):
        super(AuthenticationError, self).__init__(*args, **kwargs)


class AuthenticationError(Exception):
    def __init__(self, *args, **kwargs):
        super(AuthenticationError, self).__init__(*args, **kwargs)


def save_cookies(C, filename):
    with open(filename, "wb") as f:
        pickle.dump(C, f)


def load_cookies(filename):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            Cookie = pickle.load(f)
    else:
        Cookie = cookies.SimpleCookie()
    return Cookie


def get_cookies(C):
    return dict((k, v.value) for k, v in C.items())


def json_or_error(response):
    if response.status_code == 400:
        raise AuthenticationError("Cookies expired or invalid, please login!")

    return response.json()


def parse_cookies(cookies_str):
    Cookie = cookies.SimpleCookie()
    Cookie.load(cookies_str)
    return Cookie


def login(username, password):
    username = str(username)
    password = str(password)

    password = hex_md5(password)
    rp = requests.post(
        LOGIN_IF,
        data={
            "LoginName": username,
            "Pwd": password,
            "RawPwd": "",
            "IsRecord": "true",
            "action": "toLogin",
        })

    if rp.status_code != 200:
        raise requests.exceptions.ConnectionError(
            "Server Error: %s" % rp.status_code)

    if rp.text == "False":
        raise AuthenticationError(
            "Authentication Failed: Check your username and your password")

    Cookie = cookies.SimpleCookie()
    Cookie.load(rp.headers.get("Set-Cookie", ""))
    return Cookie


def get_test_data(testID, Cookie):
    return requests.post(
        TEST_IF,
        json={
            "TestID": testID,
            "CheckUserID": -1
        },
        cookies=get_cookies(Cookie))


def upload_answer(testID, answer, Cookie):
    return requests.post(
        TESTTEMPSAVE_IF,
        json={
            "TestID": testID,
            "Answer": answer,
        },
        cookies=get_cookies(Cookie))


def submit_answer(testID, C):
    return requests.post(
        TESTSUBMIT_IF, json={
            "TestID": testID,
        }, cookies=get_cookies(Cookie))


def get_papercard_data(paperID, Cookie):
    return requests.post(
        PAPERCARD_IF, json={"PaperID": paperID}, cookies=get_cookies(Cookie))


def get_markingpaper_data(testID, paperID, Cookie):
    """
    Shape of the returned data
    ---
    {
      d {
        PaperID
        Type
        paper {
          PaperID: Int
          CourseID: Int
          OCID: Int
          OwnerUserID: Int
          CreateUserID: Int
          UserName: String
          PaperName: String
          Type: Int
          TypeName: String?
          Scope: Int
          ShareScope: Int
          TimeLimit: Int
          Brief: String
          UpdateTime: String
          Num: Int
          Score: Int
          Conten: String
          Answer: String
          IsDeleted: Bool
          IsTactic: Int
          ChapterOrKen: Int
          ExerciseCount: Int
        }
        papergrouplist {
          ExerciseCount: Int
          ExerciseStore: Int
          ExerciseList: Any?
          GroupID: Int
          PaperID: Int
          GroupName: String
          Orde: Int
          Brief: String
          Timelimit: Int
        }
        exerciselist {
          IsChildren: Bool
          IsZG: Bool
          IsTactic: Bool
          IsInclude: Bool
          ChapterName: String?
          KenName: String?
          Conten: String
          Diffcult: Int
          IsRand: Bool
          ExerciseTypeName: String
          ExerciseType: Int
          PaperExerciseID: Int
          PaperID: Int
          PaperGroupID: Int
          ExerciseID: Int
          ParentExerciseID: Int
          PaperTacticID: Int
          Score: Int
          Orde: Int
          Answer: String
          ChoicesAnswerCN: Any?
          Analysis: Any?
          TestTacticExerciseID: Int
          OrdeIsShow: Bool
          UserIDS: Any?
        }
        ExerciseChoices {
          ChoiceID: Int
          ExerciseID: Int
          Conten: String
          ISCorrect: Bool
          Grou: Int
          OrderNum: Int
          ISDeleted: Bool
          Answer: Any?
        }
        attachmentlist
      }
    }
    """
    return requests.post(
        MARKINGPAPER_IF,
        json={
            "TestID": testID,
            "PaperID": paperID,
            "UserID": -1
        },
        cookies=get_cookies(Cookie))


def get_all_data(testID, Cookie, ignore_unpublished=False):
    """
    Shortcut for getting all required data (exercise list & choices)
    from paperID and cookies. Returns (exerciselist, ExerciseChoices).

    See Also
    --------
    get_markingpaper_data
    """
    test_data = json_or_error(get_test_data(testID, Cookie))
    if not test_data['d']['IsSend'] and not ignore_unpublished:
        raise Exception(UNPUBLISHED_MSG)

    paperID = test_data['d']['PaperID']
    all_data = json_or_error(get_markingpaper_data(testID, paperID,
                                                   Cookie))['d']
    return all_data["paper"], all_data['exerciselist'], all_data[
        'ExerciseChoices']


def lookup_choices(exid, choices_table):
    choices = pd.DataFrame(choices_table[choices_table["ExerciseID"] == exid])
    num_choices = len(choices)
    choices["ChoiceName"] = [chr(x + ord("A")) for x in range(num_choices)]
    true_choices = "".join(choices[choices["IsCorrect"]]["ChoiceName"])
    choices_dict = choices.set_index("ChoiceName")["Conten"].to_dict()

    return true_choices, choices_dict


def parse_result(el, ec):
    dfl = pd.DataFrame(el)[[
        "ExerciseID", "Conten", "ExerciseType", "ExerciseTypeName"
    ]]
    dfc = pd.DataFrame(ec)

    choices_data = dfl["ExerciseID"].map(
        lambda exid: lookup_choices(exid, dfc))
    dfl["TrueChoices"] = choices_data.map(lambda x: x[0])
    dfl["Choices"] = choices_data.map(lambda x: x[1])

    return dfl


def render_to_text(result):
    output = ""
    question_layout = "[%(trueansw)s]%(id)s. %(ques)s\n%(choices)s\n"
    choices_layout = "%(name)s. %(content)s\n"

    result["Choices"] = result["Choices"].map(lambda choices_dict: [
        (choices_layout % {"name": k, "content": v.strip()})
        for k, v in choices_dict.items()
    ])
    output = "".join(result.apply(lambda l:
        question_layout % {
            "trueansw": l["TrueChoices"],
            "id": l["ExerciseID"],
            "ques": l["Conten"].strip(),
            "choices": "".join(l["Choices"])
        }, axis=1))
    return output
