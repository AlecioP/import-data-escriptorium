import time
import requests
import pyautogui
import pygetwindow
import json

SLEEP_MINUTES = 15
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
            if RETRY > 5:
                return
            time.sleep(0.5)
    x,y = pyautogui.center(location)
    pyautogui.click(x/FACTOR,y/FACTOR,clicks=CLICK_N,interval=1)
    return (x,y)

def get_url_bar():
    pyautogui.hotkey("alt","d")
    return

class Scheduler:
    def __init__(self,DOC_IDs_FILE):
        self.QUEUE_ITER : int = 0
        with open(DOC_IDs_FILE,"r") as fd:
            self.DOC_IDs : list[str] = fd.readlines()

    def start_new_training(self):
        if self.QUEUE_ITER >= len(self.DOC_IDs):
            return
        CURRENT_DOC = self.DOC_IDs[self.QUEUE_ITER]
        
        WINDOW_TITLE = "Chrome"
        windows : list[pygetwindow.BaseWindow] = pygetwindow.getWindowsWithTitle(WINDOW_TITLE)
        if len(windows) == 0 :
            print(f"No window named {WINDOW_TITLE}. Exit")
            exit(-1)
        windows[0].activate()
        get_url_bar()
        pyautogui.press("backspace")
        pyautogui.write(f"http://localhost:8080/document/{CURRENT_DOC}/images")
        pyautogui.press("enter")
        clickImage("select_all.png")
        clickImage("train.png")
        clickImage("recognizer.png")

        highest = None
        lowest = None
        for t in pyautogui.locateAllOnScreen(IMAGES_DIR+"arrows.png"):
            # locateAllOnScreen(image, grayscale=False) - 
            # Returns a generator that yields (left, top, width, height) 
            # tuples for where the image is found on the screen.
            if (highest is None) or (t.top < highest):
                highest = t

            if (lowest is None) or ((t.top + t.height) > lowest):
                highest = t 
        #endFor
        o_box = pyautogui.locateOnScreen(IMAGES_DIR+"overwrite.png")
        o_box.width = o_box.width / 11

        if CURRENT_DOC > 0 :
            pyautogui.click(pyautogui.center(highest))
            pyautogui.write("imported")
            pyautogui.write("zip")
            pyautogui.press("enter")

            pyautogui.click(pyautogui.center(lowest))
            pyautogui.write(MODEL_NAME)
            pyautogui.press("enter")

            
            pyautogui.click(pyautogui.center(o_box))

            clickImage("start_training.png")
        else:
            pyautogui.click(pyautogui.center(highest))
            pyautogui.write("imported")
            pyautogui.write("zip")
            pyautogui.press("enter")

            clickImage("new_model_name.png")
            pyautogui.write(MODEL_NAME)

            pyautogui.click(pyautogui.center(lowest))
            pyautogui.write(BASE_MODEL)
            pyautogui.press("enter")            

            clickImage("start_training.png")
        #endElse
        
        
        self.QUEUE_ITER += 1


sched = Scheduler(QUEUE_FILE)

while True:

    for retry in range(0,MAX_RETRIES):
        TASK = None

        json_bytes = requests.get(f"http://localhost:5555/api/tasks").content
        json_dict : dict[str,dict] = json.loads(json_bytes.decode('utf-8'))
        LATEST_TASK = None
        for k in json_dict.keys() :

            # Searching for a training task
            task_type = json_dict[k].get("name",None)
            if (task_type is None) or (task_type != "core.tasks.train"):
                continue
            # Searching for a running task
            task_status = json_dict[k].get("state",None)
            if (task_type is None) or (task_type == "SUCCESS"):
                continue

            # Searching for the last started task
            start : float = json_dict[k].get("started",None)
            if start is None :
                continue

            # If the first good one i find or the current last
            if (LATEST_TASK is None) or (k > LATEST_TASK):
                LATEST_TASK = k
                continue

        if not (LATEST_TASK is None):
            break
    #endFor
    
    if LATEST_TASK is None:
        print("Aborting because i cannot find a new task")
        exit(-1)

    json1_bytes = requests.get(f"http://localhost:5555/api/task/info/{LATEST_TASK}").content
    json1_dict : dict[str] = json.loads(json1_bytes.decode("utf-8"))

    task_state = json1_dict.get("state",None)

    if (task_state is None) or (task_state != "SUCCESS" ):
        time.sleep(60 * SLEEP_MINUTES)
        continue

    sched.start_new_training()
#endWhile
