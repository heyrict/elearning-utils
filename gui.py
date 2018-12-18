import re
import tkinter as tk
from http import cookies

from grep_data import *

TESTID_RE = re.compile(r"TestID=(\d+)")
NUMONLY_RE = re.compile(r"^(\d+)$")


class Page(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

    def show(self):
        self.lift()


class LoginPage(Page):
    def __init__(self, master=None, loginSuccess=None):
        Page.__init__(self, master)
        self.loginSuccess = loginSuccess

        self.msg = tk.StringVar()
        self.un = tk.StringVar()
        self.pw = tk.StringVar()
        self.un.set("16010101")
        self.pw.set("16010101")

        formFrame = tk.Frame(self)

        titleLbl = tk.Label(formFrame, text="ElearningFetch", font=(32))
        unLbl = tk.Label(formFrame, text="Username")
        pwLbl = tk.Label(formFrame, text="Password")
        msgLbl = tk.Label(formFrame, textvariable=self.msg)
        unEnt = tk.Entry(formFrame, fg="red", font=(16), textvariable=self.un)
        pwEnt = tk.Entry(formFrame, show="*", textvariable=self.pw)

        titleLbl.pack(side="top", pady=10, fill="x", expand=False)
        unLbl.pack(side="top", pady=10, fill="x", expand=False)
        unEnt.pack(side="top", pady=10, fill="x", expand=False)
        pwLbl.pack(side="top", pady=10, fill="x", expand=False)
        pwEnt.pack(side="top", pady=10, fill="x", expand=False)
        msgLbl.pack(side="top", pady=10, fill="x", expand=False)

        formFrame.pack(side="top", padx=10, pady=20, fill="both", expand=True)

        loginBtn = tk.Button(
            self, text="Login", command=self.handleLoginButtonClick)
        loginBtn.pack(
            side="bottom", padx=30, pady=20, fill="both", expand=False)

    def handleLoginButtonClick(self):
        username = self.un.get()
        password = self.pw.get()
        try:
            self.msg.set("Now Loading...")
            cookie = login(username, password)
            self.loginSuccess(cookie)
        except Exception as e:
            self.msg.set(str(e))


class FetchPage(Page):
    def __init__(self, master=None):
        Page.__init__(self, master)
        self.cookie = cookies.SimpleCookie()
        self.testId = tk.StringVar()

        inputFrame = tk.Frame(self, width="200")
        idLbl = tk.Label(inputFrame, text="TestId")
        idEnt = tk.Entry(inputFrame, textvariable=self.testId)
        idBtn = tk.Button(
            inputFrame, text="Fetch", command=self.handleFetchButtonClick)
        idLbl.pack(side="top", fill="x", pady=(50, 20), padx=20)
        idEnt.pack(side="top", fill="x", pady=(0, 20), padx=20)
        idBtn.pack(side="top", fill="x", pady=(0, 50), padx=20)

        outputFrame = tk.Frame(self)
        self.out = tk.Text(outputFrame, bg="#fcf4dc", fg="black")
        self.out.insert('end', 'Welcome')
        self.out.configure(state="disable")
        self.out.pack(fill="both", expand=True)

        inputFrame.pack(side="left", fill="y", expand=False)
        outputFrame.pack(side="left", fill="both", expand=True)

    def setMessage(self, txt):
        self.out.configure(state="normal")
        self.out.delete('1.0', 'end')
        self.out.insert('end', txt)
        self.out.configure(state="disable")

    def handleFetchButtonClick(self):
        testId = self.testId.get()

        if NUMONLY_RE.match(testId):
            match = testId
            paper, el, ec = get_all_data(testId, self.cookie)
        elif TESTID_RE.search(testId):
            match = TESTID_RE.search(testId).expand(r"\1")
            paper, el, ec = get_all_data(match, self.cookie)
        else:
            self.setMessage("Unrecognizable testpaper argument: %s" % testId)
            return
        res = parse_result(el, ec)
        txt = render_to_text(res)
        self.setMessage("TestID %(testid)s: [%(papername)s]\n\n%(txt)s" % {
            'testid': match,
            'papername': paper['Papername'],
            'txt': txt,
        })


class MainView(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pl = LoginPage(self, loginSuccess=self.handleLoginSuccess)
        self.pf = FetchPage(self)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        self.pl.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        self.pf.place(in_=container, x=0, y=0, relwidth=1, relheight=1)

        self.pl.show()

    def handleLoginSuccess(self, cookie):
        self.pf.cookie = cookie
        self.pf.show()


if __name__ == "__main__":
    root = tk.Tk()
    main = MainView(root)
    main.pack(side="top", fill="both", expand=True)
    root.wm_geometry("800x400")
    root.mainloop()
