import datetime
import time
import requests
import pyautogui
import pygetwindow
import json
from pathlib import Path

SLEEP_MINUTES = 5
MAX_RETRIES = 5
QUEUE_FILE = "./QUEUE_TRAINING.txt"
IMAGES_DIR = "./screenshots/train/"
MODEL_NAME = "GrEma_on_fondue_open"
BASE_MODEL = "FONDUE-MLT-CAT_full"
FACTOR = 1

def clickImage(IMG,CONF=0.9,GREY=False,CLICK_N=1):
    # 4 element tuple
    toFind = IMAGES_DIR+IMG
    location = None
    RETRY = 0
    while True:
        try:
            location = pyautogui.locateOnScreen(toFind,grayscale=GREY)
            break
        except pyautogui.ImageNotFoundException:
            RETRY += 1 
            print(f"Failed to locate \"{IMG}\" on screen. Try {RETRY}. Retrying in 0.5 seconds")
            if RETRY > 10:
                return
            time.sleep(0.5)
    x,y = pyautogui.center(location)
    pyautogui.click(x/FACTOR,y/FACTOR,clicks=CLICK_N,interval=1)
    return (x,y)

def get_url_bar():
    pyautogui.hotkey("alt","d")
    return
print("Before declaring class")
class Scheduler:
    def __init__(self,DOC_IDs_FILE):
        self.QUEUE_ITER : int = 0
        with open(DOC_IDs_FILE,"r") as fd:
            self.DOC_IDs : list[str] = fd.readlines()

    def start_new_training(self):
        if self.QUEUE_ITER >= len(self.DOC_IDs):
            return
        CURRENT_DOC = self.DOC_IDs[self.QUEUE_ITER][:-1]
        
        WINDOW_TITLE = "Chrome"
        windows : list[pygetwindow.BaseWindow] = pygetwindow.getWindowsWithTitle(WINDOW_TITLE)
        if len(windows) == 0 :
            print(f"No window named {WINDOW_TITLE}. Exit")
            exit(-1)
        windows[0].activate()
        get_url_bar()
        pyautogui.press("backspace")
        print(f"GOTO http://localhost:8080/document/{CURRENT_DOC}/images")
        pyautogui.write(f"http://localhost:8080/document/{CURRENT_DOC}/images")
        pyautogui.press("enter")
        time.sleep(5)
        clickImage("select_all.png")
        clickImage("train.png")
        clickImage("recognizer.png")

        highest = None
        lowest = None
        for t in pyautogui.locateAllOnScreen((Path(IMAGES_DIR) / "arrows.png").resolve().__str__()):
            print(t)
            # locateAllOnScreen(image, grayscale=False) - 
            # Returns a generator that yields (left, top, width, height) 
            # tuples for where the image is found on the screen.
            if (highest is None) or (t.top < highest.top):
                highest = t

            if (lowest is None) or ((t.top + t.height) > (lowest.top + lowest.height)):
                lowest = t 
        #endFor
        o_box = pyautogui.locateOnScreen((Path(IMAGES_DIR) / "overwrite.png").resolve().__str__())
        o_box_check = (o_box.left, o_box.top, o_box.width/11, o_box.height)

        if int(CURRENT_DOC) > 0 :
            pyautogui.click(pyautogui.center(highest))
            pyautogui.write("imported")
            pyautogui.write("zip")
            pyautogui.press("enter")
            time.sleep(5)
            pyautogui.click(pyautogui.center(lowest))
            pyautogui.write(MODEL_NAME)
            pyautogui.press("enter")
            time.sleep(5)
            
            pyautogui.click(pyautogui.center(o_box_check))
            time.sleep(5)
            clickImage("start_training.png")
        else:
            pyautogui.click(pyautogui.center(highest))
            pyautogui.write("imported")
            pyautogui.write("zip")
            pyautogui.press("enter")
            time.sleep(5)
            clickImage("new_model_name.png")
            pyautogui.write(MODEL_NAME)
            time.sleep(5)
            pyautogui.click(pyautogui.center(lowest))
            pyautogui.write(BASE_MODEL)
            pyautogui.press("enter")            
            time.sleep(5)
            clickImage("start_training.png")
        #endElse
        
        
        self.QUEUE_ITER += 1

print("After declaring class")
sched = Scheduler(QUEUE_FILE)
sched.start_new_training()

while True:
    print("Iteration in while true")
    for retry in range(0,MAX_RETRIES):
        TASK = None

        json_bytes = requests.get(f"http://localhost:5555/api/tasks").content
        json_dict : dict[str,dict] = json.loads(json_bytes.decode('utf-8'))
        LATEST_TASK = None
        for k in json_dict.keys() :

            # Searching for a training task
            task_type = json_dict[k].get("name",None)
            if (task_type is None) or (task_type != "core.tasks.train"):
                print("Skip : not training task")
                continue
            # Searching for a running task
            task_status = json_dict[k].get("state",None)
            if (task_status is None) or (task_status == "SUCCESS"):
                print("Skip : completed task")
                continue

            # Searching for the last started task
            start : float = json_dict[k].get("started",None)
            if start is None :
                print("Skip : cannot find start time")
                continue

            # If the first good one i find or the current last
            if (LATEST_TASK is None) or (k > LATEST_TASK):
                LATEST_TASK = k
                continue

        if not (LATEST_TASK is None):
            print(f"Did find a good one at this retry : {LATEST_TASK}")
            break
        print("Did not find any started training task. Sleeping for 60 seconds")
        time.sleep(10)
    #endFor
    
    if LATEST_TASK is None:
        print("Aborting because i cannot find a new task")
        exit(-1)

    while True:
        json1_bytes = requests.get(f"http://localhost:5555/api/task/info/{LATEST_TASK}").content
        json1_dict : dict[str] = json.loads(json1_bytes.decode("utf-8"))

        task_state = json1_dict.get("state",None)

        if (task_state is None) or (task_state != "SUCCESS" ):
            print(f"Train task {LATEST_TASK} not finished yet. Going to sleep for {SLEEP_MINUTES} minutes")
            print(f"Now is {datetime.datetime.now()}")
            time.sleep(60 * SLEEP_MINUTES)
            continue
        break

    sched.start_new_training()
#endWhile
