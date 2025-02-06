import time
import json
import pyautogui
from pathlib import Path
import shutil

from argparse import ArgumentParser

parser = ArgumentParser(description="Automatic import of data into escriptorium - transcriptions")

parser.add_argument("--import_folder",type=str,help="Path to root directory of data to import",nargs=1,required=True)

parser.add_argument("--url_map_json",type=str,help="File json containing links to document's page",nargs=1,required=True)

ARGS = parser.parse_args()

IMPORT_FOLDER = ARGS.import_folder[0]

JSON_PATH = ARGS.url_map_json[0]

PATH_TO_URL = {}
with open(JSON_PATH,"r") as fd:
    PATH_TO_URL = json.load(fd)

IMAGES_DIR = "./screenshots/"

FACTOR = 1


def clickImage(IMG,CONF=0.9,GREY=False,CLICK_N=1):
	# 4 element tuple
	toFind = IMAGES_DIR+IMG
	location = pyautogui.locateOnScreen(toFind,grayscale=GREY)
	x,y = pyautogui.center(location)
	pyautogui.click(x/FACTOR,y/FACTOR,clicks=CLICK_N,interval=1)
	return (x,y)

def chrome_url_bar():
    pyautogui.hotkey("alt","d")
    return


# FOR EACH FOLDER IN ROOT 

Path("QUEUE_DONE_XML.txt").touch(exist_ok=True)

print("Giving you time to setup the windows. Make sure escriptorium project's browser window is visible on the screen")
time.sleep(5)
try:
    for f in Path(IMPORT_FOLDER).glob("*/"):
        # ENTER ONE
        DOC_ID = list(f.glob("*/"))[0].parts[-1]
        # GET DOC ID
        print(DOC_ID)
        #print(f)
        #print((f / DOC_ID).resolve())

        with open("QUEUE_DONE_XML.txt","r") as fd:
            if DOC_ID in fd.read():
                print(f"Skip cause DOC_ID={DOC_ID} has already been imported")
                continue

        # Gain focus
        clickImage("documents_list.png",CLICK_N=2)
        # paste url related to current document
        chrome_url_bar()
        pyautogui.press("backspace")
        path_key = str((f / DOC_ID).resolve())
        document_url = PATH_TO_URL.get(path_key,None)
        if document_url is None:
            print(f"SKIP because cannot find url for path {path_key}")
            continue
        pyautogui.write(document_url.replace("edit","images"))
        pyautogui.press("enter")
        # Redirect so wait
        time.sleep(1)
        clickImage("import.png")
        clickImage("transcriptions.png")
        clickImage("scegli_file.png")

        # MACRO click explorer address bar
        pyautogui.press("f4")
        pyautogui.hotkey("ctrl","a")
        pyautogui.press("backspace")

        # type DOC_ID folder
        pyautogui.write(str((f / DOC_ID).resolve()))
        pyautogui.press("enter")

        time.sleep(1)
        # This sequence empirically seems to work. Chrome (Versione 133.0.6943.53) Open file dialog (Windows 11 Enterprise 10.0.26100 build 26100)
        pyautogui.press("enter")
        pyautogui.press("enter")
        pyautogui.press("enter")
        time.sleep(1)

        shutil.make_archive(base_name=str(f / DOC_ID / "page").resolve(),format="zip",base_dir=str(f / DOC_ID / "page"))

        pyautogui.write("\"page.zip\"")

        pyautogui.press("enter")
        pyautogui.press("enter")

        clickImage("name_transcription.png")
        pyautogui.write("imported")
        pyautogui.press("enter")
        

        RETRY = 0
        while True:
            try:
                clickImage("back_to_doc_list.png",CONF=0.9)
                break
            except pyautogui.ImageNotFoundException:
                RETRY += 1
                if RETRY > 3:
                    break

        with open("QUEUE_DONE_XML.TXT","a") as fd:
            fd.write(DOC_ID + "\n")

        print("To stop press ctrl+c TWO TIMES (5 seconds)")
        time.sleep(5)
except KeyboardInterrupt :
    print("ctrl + c pressed. hope you did it when you could do it because rollback is not implemented")
    # TODO rollback last iteration

